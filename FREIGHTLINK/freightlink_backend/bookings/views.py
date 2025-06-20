# bookings/views.py
from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Booking, BookingStatusUpdate, BookingDocument
from .serializers import (
    BookingListSerializer, BookingDetailSerializer, BookingCreateSerializer,
    BookingUpdateSerializer, BookingStatusUpdateSerializer,
    BookingStatusUpdateCreateSerializer, BookingDocumentSerializer
)
from trucks.models import Truck


class BookingListCreateView(generics.ListCreateAPIView):
    """
    List all bookings for the authenticated user or create a new booking
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'truck__truck_type', 'cargo_type']
    search_fields = ['booking_reference', 'pickup_address', 'delivery_address', 'cargo_description']
    ordering_fields = ['created_at', 'pickup_date', 'expected_delivery_date']
    ordering = ['-created_at']
    def create(self, request, *args, **kwargs):
        print("Booking creation request data:", request.data)  # Debug log
        return super().create(request, *args, **kwargs)
        
    def get_queryset(self):
        user = self.request.user
        queryset = Booking.objects.select_related('customer', 'truck', 'truck__owner')
        
        # Filter based on user role
        if hasattr(user, 'trucks') and user.trucks.exists():
            # User is a truck owner - show bookings for their trucks
            return queryset.filter(
                Q(customer=user) | Q(truck__owner=user)
            )
        else:
            # Regular customer - show only their bookings
            return queryset.filter(customer=user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BookingCreateSerializer
        return BookingListSerializer


class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or cancel a specific booking
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Booking.objects.select_related(
            'customer', 'truck', 'truck__owner'
        ).prefetch_related('status_updates', 'documents')
        
        # Filter based on user role
        if hasattr(user, 'trucks') and user.trucks.exists():
            return queryset.filter(
                Q(customer=user) | Q(truck__owner=user)
            )
        else:
            return queryset.filter(customer=user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return BookingUpdateSerializer
        return BookingDetailSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Cancel booking instead of deleting"""
        booking = self.get_object()
        if booking.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel completed or cancelled bookings'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        # Create status update record
        BookingStatusUpdate.objects.create(
            booking=booking,
            old_status=booking.status,
            new_status='cancelled',
            updated_by=request.user,
            notes='Cancelled by customer'
        )
        
        return Response({'message': 'Booking cancelled successfully'})


class MyBookingsView(generics.ListAPIView):
    """
    List bookings for the authenticated customer only
    """
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'truck__truck_type', 'cargo_type']
    search_fields = ['booking_reference', 'pickup_address', 'delivery_address']
    ordering_fields = ['created_at', 'pickup_date', 'expected_delivery_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Booking.objects.filter(
            customer=self.request.user
        ).select_related('customer', 'truck', 'truck__owner')


class TruckBookingsView(generics.ListAPIView):
    """
    List bookings for trucks owned by the authenticated user
    """
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'truck', 'cargo_type']
    ordering_fields = ['created_at', 'pickup_date', 'expected_delivery_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Booking.objects.filter(
            truck__owner=self.request.user
        ).select_related('customer', 'truck')


class BookingStatusUpdateView(generics.CreateAPIView):
    """
    Create a status update for a booking
    """
    serializer_class = BookingStatusUpdateCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        booking_id = self.kwargs.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Check permissions
        user = request.user
        if not (booking.customer == user or booking.truck.owner == user):
            return Response(
                {'error': 'You do not have permission to update this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Add booking to validated data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['booking'] = booking
        
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BookingDocumentUploadView(generics.CreateAPIView):
    """
    Upload a document for a booking
    """
    serializer_class = BookingDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        booking_id = self.kwargs.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Check permissions
        user = request.user
        if not (booking.customer == user or booking.truck.owner == user):
            return Response(
                {'error': 'You do not have permission to upload documents for this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(booking=booking, uploaded_by=request.user)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_trucks(request):
    """
    Get available trucks for booking based on date range
    """
    pickup_date = request.GET.get('pickup_date')
    delivery_date = request.GET.get('delivery_date')
    
    if not pickup_date or not delivery_date:
        return Response(
            {'error': 'pickup_date and delivery_date parameters are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        pickup_date = timezone.datetime.fromisoformat(pickup_date.replace('Z', '+00:00'))
        delivery_date = timezone.datetime.fromisoformat(delivery_date.replace('Z', '+00:00'))
    except ValueError:
        return Response(
            {'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get trucks that don't have conflicting bookings
    conflicting_bookings = Booking.objects.filter(
        status__in=['pending', 'confirmed', 'in_progress'],
        pickup_date__lt=delivery_date,
        expected_delivery_date__gt=pickup_date
    ).values_list('truck_id', flat=True)
    
    available_trucks = Truck.objects.filter(
        is_active=True
    ).exclude(
        id__in=conflicting_bookings
    ).select_related('owner')
    
    # Apply additional filters
    truck_type = request.GET.get('truck_type')
    if truck_type:
        available_trucks = available_trucks.filter(truck_type=truck_type)
    
    min_capacity = request.GET.get('min_capacity')
    if min_capacity:
        try:
            min_capacity = float(min_capacity)
            available_trucks = available_trucks.filter(capacity_tons__gte=min_capacity)
        except ValueError:
            pass
    
    location = request.GET.get('location')
    if location:
        available_trucks = available_trucks.filter(
            current_location__icontains=location
        )
    
    from trucks.serializers import TruckSerializer  # Import here to avoid circular imports
    serializer = TruckSerializer(available_trucks, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def booking_statistics(request):
    """
    Get booking statistics for the authenticated user
    """
    user = request.user
    
    # Customer statistics
    customer_bookings = Booking.objects.filter(customer=user)
    customer_stats = {
        'total_bookings': customer_bookings.count(),
        'pending_bookings': customer_bookings.filter(status='pending').count(),
        'confirmed_bookings': customer_bookings.filter(status='confirmed').count(),
        'completed_bookings': customer_bookings.filter(status='completed').count(),
        'cancelled_bookings': customer_bookings.filter(status='cancelled').count(),
    }
    
    # Truck owner statistics (if applicable)
    truck_owner_stats = None
    if hasattr(user, 'trucks') and user.trucks.exists():
        truck_bookings = Booking.objects.filter(truck__owner=user)
        truck_owner_stats = {
            'total_bookings': truck_bookings.count(),
            'pending_bookings': truck_bookings.filter(status='pending').count(),
            'confirmed_bookings': truck_bookings.filter(status='confirmed').count(),
            'completed_bookings': truck_bookings.filter(status='completed').count(),
            'revenue': truck_bookings.filter(
                status='completed', 
                final_price__isnull=False
            ).aggregate(
                total=Sum('final_price')
            )['total'] or 0
        }
    
    return Response({
        'customer_stats': customer_stats,
        'truck_owner_stats': truck_owner_stats
    })