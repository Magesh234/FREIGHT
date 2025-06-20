from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Sum  # Added Sum import here
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import CargoType, CargoListing, CargoPhoto
from .serializers import (
    CargoTypeSerializer, CargoListingListSerializer, CargoListingDetailSerializer,
    CargoListingCreateSerializer, CargoPhotoSerializer
)
from .filters import CargoListingFilter


class CargoTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cargo types
    """
    queryset = CargoType.objects.all()
    serializer_class = CargoTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        """Only allow staff users to create cargo types"""
        if not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only staff can create cargo types.")
        serializer.save()

    def perform_update(self, serializer):
        """Only allow staff users to update cargo types"""
        if not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only staff can update cargo types.")
        serializer.save()

    def perform_destroy(self, instance):
        """Only allow staff users to delete cargo types"""
        if not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only staff can delete cargo types.")
        # Check if cargo type is being used
        if CargoListing.objects.filter(cargo_type=instance.name.lower()).exists():
            raise permissions.PermissionDenied("Cannot delete cargo type that is in use.")
        instance.delete()


class CargoListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cargo listings
    Provides CRUD operations with filtering, searching, and custom actions
    """
    queryset = CargoListing.objects.select_related('posted_by').prefetch_related('cargo_photos')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CargoListingFilter
    search_fields = ['title', 'description', 'pickup_location', 'delivery_location']
    ordering_fields = ['created_at', 'pickup_date', 'delivery_date', 'budget', 'weight', 'volume']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CargoListingListSerializer
        elif self.action == 'create':
            return CargoListingCreateSerializer
        else:
            return CargoListingDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions and parameters"""
        queryset = self.queryset
        
        # Filter by user's own listings if requested
        if self.request.query_params.get('my_listings', '').lower() == 'true':
            if self.request.user.is_authenticated:
                queryset = queryset.filter(posted_by=self.request.user)
            else:
                queryset = queryset.none()
        
        return queryset

    def perform_create(self, serializer):
        """Create cargo listing with current user as owner"""
        serializer.save(posted_by=self.request.user)

    def perform_update(self, serializer):
        """Only allow owner or staff to update"""
        listing = self.get_object()
        if listing.posted_by != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only update your own listings.")
        
        # Prevent status changes to completed by non-staff
        if 'status' in serializer.validated_data:
            new_status = serializer.validated_data['status']
            if new_status == 'COMPLETED' and not self.request.user.is_staff:
                if listing.posted_by != self.request.user:
                    raise permissions.PermissionDenied("Only staff can mark listings as completed.")
        
        serializer.save()

    def perform_destroy(self, instance):
        """Only allow owner or staff to delete"""
        if instance.posted_by != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only delete your own listings.")
        
        # Prevent deletion of in-progress or completed listings
        if instance.status in ['IN_PROGRESS', 'COMPLETED']:
            raise permissions.PermissionDenied("Cannot delete listings that are in progress or completed.")
        
        instance.delete()

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update the status of a cargo listing"""
        listing = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'Status is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in dict(CargoListing.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check permissions
        if listing.posted_by != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Business logic for status transitions
        current_status = listing.status
        valid_transitions = {
            'OPEN': ['IN_PROGRESS', 'CANCELLED'],
            'IN_PROGRESS': ['COMPLETED', 'CANCELLED'],
            'COMPLETED': [],  # Cannot change from completed
            'CANCELLED': ['OPEN'],  # Can reopen cancelled listings
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            return Response(
                {'error': f'Cannot change status from {current_status} to {new_status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        listing.status = new_status
        listing.save()
        
        serializer = self.get_serializer(listing)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_listings(self, request):
        """Get current user's cargo listings"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        queryset = self.filter_queryset(
            self.queryset.filter(posted_by=request.user)
        )
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = CargoListingListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = CargoListingListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get cargo listings statistics"""
        queryset = self.filter_queryset(self.get_queryset())
        
        stats = {
            'total_listings': queryset.count(),
            'by_status': {},
            'by_cargo_type': {},
            'average_budget': 0,
            'total_weight': 0,
            'total_volume': 0,
        }
        
        # Count by status
        for status_code, status_name in CargoListing.STATUS_CHOICES:
            stats['by_status'][status_code] = queryset.filter(status=status_code).count()
        
        # Count by cargo type
        for cargo_type, type_name in CargoListing.CARGO_TYPE_CHOICES:
            stats['by_cargo_type'][cargo_type] = queryset.filter(cargo_type=cargo_type).count()
        
        # Calculate aggregates - Fixed: Now using Sum instead of models.Sum
        aggregates = queryset.aggregate(
            avg_budget=Avg('budget'),
            total_weight=Sum('weight'),  # Fixed: Now properly imported
            total_volume=Sum('volume')   # Fixed: Now properly imported
        )
        
        stats['average_budget'] = float(aggregates['avg_budget'] or 0)
        stats['total_weight'] = float(aggregates['total_weight'] or 0)
        stats['total_volume'] = float(aggregates['total_volume'] or 0)
        
        return Response(stats)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_photo(self, request, pk=None):
        """Upload a photo for a cargo listing"""
        listing = self.get_object()
        
        # Check permissions
        if listing.posted_by != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if image is provided
        if 'image' not in request.FILES:
            return Response(
                {'error': 'Image file is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create photo
        photo_data = {
            'cargo': listing.id,
            'image': request.FILES['image']
        }
        
        serializer = CargoPhotoSerializer(data=photo_data, context={'request': request})
        if serializer.is_valid():
            serializer.save(cargo=listing)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='photos/(?P<photo_id>[^/.]+)')
    def delete_photo(self, request, pk=None, photo_id=None):
        """Delete a photo from a cargo listing"""
        listing = self.get_object()
        
        # Check permissions
        if listing.posted_by != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get and delete photo
        photo = get_object_or_404(CargoPhoto, id=photo_id, cargo=listing)
        photo.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class CargoPhotoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cargo photos
    """
    queryset = CargoPhoto.objects.select_related('cargo', 'cargo__posted_by')
    serializer_class = CargoPhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """Filter photos by cargo listing if specified"""
        queryset = self.queryset
        cargo_id = self.request.query_params.get('cargo_id')
        
        if cargo_id:
            queryset = queryset.filter(cargo_id=cargo_id)
        
        return queryset

    def perform_create(self, serializer):
        """Only allow cargo owner to upload photos"""
        cargo = serializer.validated_data['cargo']
        if cargo.posted_by != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only upload photos to your own listings.")
        serializer.save()

    def perform_update(self, serializer):
        """Only allow cargo owner to update photos"""
        photo = self.get_object()
        if photo.cargo.posted_by != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only update photos of your own listings.")
        serializer.save()

    def perform_destroy(self, instance):
        """Only allow cargo owner to delete photos"""
        if instance.cargo.posted_by != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only delete photos of your own listings.")
        instance.delete()