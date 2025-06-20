# views.py
from rest_framework import generics, permissions, status, filters, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Truck, TruckImage
from .serializers import TruckSerializer, TruckListSerializer, TruckImageSerializer
from django.utils import timezone

# Views for Truck Management
class AvailableTrucksView(generics.ListAPIView):
    serializer_class = TruckListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['truck_type', 'capacity_tons', 'year', 'current_location', 'is_active']
    search_fields = ['make_model', 'current_location', 'preferred_routes']
    ordering_fields = ['created_at', 'capacity_tons', 'rate_amount', 'year']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Show all trucks regardless of active status or availability dates
        return Truck.objects.all()
        


class TruckListCreateView(generics.ListCreateAPIView):
    queryset = Truck.objects.all()  # Show all trucks instead of filtering by is_active
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['truck_type', 'capacity_tons', 'year', 'current_location', 'is_active']
    search_fields = ['make_model', 'current_location', 'preferred_routes']
    ordering_fields = ['created_at', 'capacity_tons', 'rate_amount', 'year']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TruckListSerializer
        return TruckSerializer
    
    def perform_create(self, serializer):
        # Automatically set the owner to the currently authenticated user
        serializer.save(owner=self.request.user)


class TruckDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only access their own trucks for update/delete
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return Truck.objects.filter(owner=self.request.user)
        return Truck.objects.all()  # Show all trucks for viewing
    
    def perform_destroy(self, instance):
        # Soft delete - mark as inactive instead of deleting
        instance.is_active = False
        instance.save()


class MyTrucksView(generics.ListAPIView):
    serializer_class = TruckListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'truck_type', 'is_active']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Truck.objects.filter(owner=self.request.user)


class TruckImageUploadView(generics.CreateAPIView):
    serializer_class = TruckImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        truck_id = self.kwargs['truck_id']
        try:
            truck = Truck.objects.get(id=truck_id, owner=self.request.user)
            serializer.save(truck=truck)
        except Truck.DoesNotExist:
            raise serializers.ValidationError("Truck not found or you don't have permission.")


class TruckImageDeleteView(generics.DestroyAPIView):
    queryset = TruckImage.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return TruckImage.objects.filter(truck__owner=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def truck_search(request):
    """Advanced search for trucks with multiple filters"""
    queryset = Truck.objects.all()  # Already showing all trucks
    
    # Filter parameters
    truck_type = request.GET.get('truck_type')
    min_capacity = request.GET.get('min_capacity')
    max_capacity = request.GET.get('max_capacity')
    location = request.GET.get('location')
    available_date = request.GET.get('available_date')
    max_rate = request.GET.get('max_rate')
    is_active = request.GET.get('is_active')  # Added option to filter by active status
    
    if truck_type:
        queryset = queryset.filter(truck_type=truck_type)
    
    if min_capacity:
        queryset = queryset.filter(capacity_tons__gte=min_capacity)
    
    if max_capacity:
        queryset = queryset.filter(capacity_tons__lte=max_capacity)
    
    if location:
        queryset = queryset.filter(
            Q(current_location__icontains=location) |
            Q(preferred_routes__icontains=location)
        )
    
    if available_date:
        queryset = queryset.filter(
            available_from__lte=available_date
        ).filter(
            Q(available_to__isnull=True) | Q(available_to__gte=available_date)
        )
    
    if max_rate:
        queryset = queryset.filter(rate_amount__lte=max_rate)
    
    # Optional filter by active status
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active.lower() == 'true')
    
    serializer = TruckListSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def truck_types(request):
    """Get available truck types"""
    types = [{'value': choice[0], 'label': choice[1]} for choice in Truck.TRUCK_TYPE_CHOICES]
    return Response(types)