from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, Prefetch
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging

from .models import Bid, BidNotification, BidStatistics
from cargo.models import CargoListing
from .serializers import (
    CargoListingSerializer, CargoListingSummarySerializer,
    BidSerializer, BidCreateSerializer, BidUpdateSerializer, BidSummarySerializer,
    BidResponseSerializer, BidNotificationSerializer, BidStatisticsSerializer
)

logger = logging.getLogger(__name__)


# ============================================================================
# PAGINATION
# ============================================================================

class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination configuration"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ============================================================================
# FILTERS
# ============================================================================

class CargoListingFilter(django_filters.FilterSet):
    """Filter for cargo listings"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    posted_by = django_filters.CharFilter(field_name='posted_by__username', lookup_expr='icontains')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    has_bids = django_filters.BooleanFilter(method='filter_has_bids')
    min_bids = django_filters.NumberFilter(method='filter_min_bids')
    max_bids = django_filters.NumberFilter(method='filter_max_bids')

    class Meta:
        model = CargoListing
        fields = ['status', 'cargo_type']

    def filter_has_bids(self, queryset, name, value):
        if value:
            return queryset.filter(bids__isnull=False).distinct()
        return queryset.filter(bids__isnull=True)

    def filter_min_bids(self, queryset, name, value):
        return queryset.annotate(bid_count=Count('bids')).filter(bid_count__gte=value)

    def filter_max_bids(self, queryset, name, value):
        return queryset.annotate(bid_count=Count('bids')).filter(bid_count__lte=value)


class BidFilter(django_filters.FilterSet):
    """Filter for bids"""
    bidder = django_filters.CharFilter(field_name='bidder__username', lookup_expr='icontains')
    cargo_listing = django_filters.UUIDFilter(field_name='cargo_listing__id')
    listing_title = django_filters.CharFilter(field_name='cargo_listing__title', lookup_expr='icontains')
    min_amount = django_filters.NumberFilter(field_name='bid_amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='bid_amount', lookup_expr='lte')
    submitted_after = django_filters.DateTimeFilter(field_name='submitted_at', lookup_expr='gte')
    submitted_before = django_filters.DateTimeFilter(field_name='submitted_at', lookup_expr='lte')
    expires_after = django_filters.DateTimeFilter(field_name='expires_at', lookup_expr='gte')
    expires_before = django_filters.DateTimeFilter(field_name='expires_at', lookup_expr='lte')
    is_expired = django_filters.BooleanFilter(method='filter_is_expired')

    class Meta:
        model = Bid
        fields = ['status', 'estimated_delivery_time', 'is_active']

    def filter_is_expired(self, queryset, name, value):
        now = timezone.now()
        if value:
            return queryset.filter(expires_at__lt=now)
        return queryset.filter(Q(expires_at__gte=now) | Q(expires_at__isnull=True))


# ============================================================================
# CARGO LISTING VIEWS
# ============================================================================

@method_decorator(csrf_exempt, name='post')
class CargoListingListCreateView(generics.ListCreateAPIView):
    """
    Combined view for listing and creating cargo listings.
    GET: Returns filtered list of cargo listings (public access)
    POST: Create new cargo listing (authenticated users only)
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CargoListingFilter
    search_fields = ['title', 'description', 'posted_by__username']
    ordering_fields = ['created_at', 'updated_at', 'title', 'budget']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Optimized queryset with annotations and select_related"""
        return CargoListing.objects.select_related('posted_by').prefetch_related(
            Prefetch('bids', queryset=Bid.objects.filter(is_active=True, status='pending'))
        ).annotate(
            bid_count=Count('bids', filter=Q(bids__is_active=True, bids__status='pending'))
        ).filter(status='OPEN')  # Only show open listings

    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return CargoListingSerializer  # Use full serializer for creation
        return CargoListingSummarySerializer

    def get_permissions(self):
        """Different permissions for different methods"""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        """Create listing with proper user assignment"""
        try:
            with transaction.atomic():
                listing = serializer.save(posted_by=self.request.user)
                logger.info(f"Cargo listing created: {listing.id} by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error creating cargo listing: {str(e)}")
            raise ValidationError("Unable to create cargo listing. Please try again.")


class CargoListingDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single cargo listing with full details
    """
    serializer_class = CargoListingSerializer
    permission_classes = [permissions.AllowAny]  # Public view
    lookup_field = 'id'

    def get_queryset(self):
        """Optimized queryset with related data"""
        return CargoListing.objects.select_related('posted_by').prefetch_related(
            Prefetch('bids', queryset=Bid.objects.filter(is_active=True).select_related('bidder'))
        )

    def get_object(self):
        """Get object with proper error handling"""
        try:
            obj = super().get_object()
            return obj
        except CargoListing.DoesNotExist:
            raise NotFound("Cargo listing not found.")


class MyCargoListingsView(generics.ListAPIView):
    """List current user's cargo listings"""
    serializer_class = CargoListingSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'cargo_type']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        return CargoListing.objects.filter(
            posted_by=self.request.user
        ).annotate(
            bid_count=Count('bids', filter=Q(bids__is_active=True, bids__status='pending'))
        )


# ============================================================================
# BID VIEWS
# ============================================================================

@method_decorator(csrf_exempt, name='post')

class BidListCreateView(generics.ListCreateAPIView):
    """
    Combined view for listing and creating bids.
    GET: Returns filtered list of user's bids and bids on user's listings
    POST: Create new bid
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BidFilter
    search_fields = ['cargo_listing__title', 'message_to_shipper', 'bidder__username']
    ordering_fields = ['submitted_at', 'bid_amount', 'expires_at']
    ordering = ['-submitted_at']
    pagination_class = StandardResultsSetPagination
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    

    def get_queryset(self):
        """Optimized queryset - users can only see their own bids and bids on their listings"""
        user = self.request.user
        
        # Handle AnonymousUser for GET requests
        if not user.is_authenticated:
            return Bid.objects.none()
            
        return Bid.objects.select_related(
            'bidder', 'cargo_listing__posted_by'
        ).filter(
            Q(bidder=user) | Q(cargo_listing__posted_by=user)
        ).distinct()

    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return BidCreateSerializer
        return BidSummarySerializer

    def get_permissions(self):
        """Different permissions for different methods"""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def create(self, request, *args, **kwargs):
        """Override create to handle bid creation properly"""
        # Debug logging
        logger.debug(f"Request data: {request.data}")
        cargo_id = request.data.get('cargo_id')
        logger.debug(f"Cargo ID from frontend: {cargo_id}")
        
        # Use the serializer directly without queryset filtering
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """Create bid with proper validation and notifications"""
        try:
            with transaction.atomic():
                bid = serializer.save()
                logger.info(f"Bid created: {bid.id} by user {self.request.user.id}")
                
                # Create notification for cargo owner
                if bid.cargo_listing.posted_by != bid.bidder:
                    BidNotification.objects.create(
                        recipient=bid.cargo_listing.posted_by,
                        bid=bid,
                        notification_type='new_bid',
                        message=f"New bid of {bid.bid_amount} KSh received for '{bid.cargo_listing.title}'"
                    )
                    
        except Exception as e:
            logger.error(f"Error creating bid: {str(e)}")
            raise ValidationError("Unable to create bid. Please try again.")


class BidDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a bid.
    Only the bidder can update/delete their bids.
    Cargo owners can view bids on their listings.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Users can only access their own bids and bids on their listings"""
        user = self.request.user
        return Bid.objects.select_related(
            'bidder', 'cargo_listing__posted_by'
        ).filter(
            Q(bidder=user) | Q(cargo_listing__posted_by=user)
        )

    def get_serializer_class(self):
        """Use update serializer for PUT/PATCH"""
        if self.request.method in ['PUT', 'PATCH']:
            return BidUpdateSerializer
        return BidSerializer

    def check_object_permissions(self, request, obj):
        """Check bid access permissions"""
        super().check_object_permissions(request, obj)
        user = request.user
        
        # Bidder can view, update, delete their bid
        # Cargo owner can view bids on their listings
        if not (obj.bidder == user or obj.cargo_listing.posted_by == user):
            raise PermissionDenied("You don't have permission to access this bid.")
        
        # Only bidder can modify their bid
        if request.method in ['PUT', 'PATCH', 'DELETE'] and obj.bidder != user:
            raise PermissionDenied("You can only modify your own bids.")

    def perform_update(self, serializer):
        """Update bid with logging"""
        try:
            with transaction.atomic():
                bid = serializer.save()
                logger.info(f"Bid updated: {bid.id} by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error updating bid: {str(e)}")
            raise ValidationError("Unable to update bid. Please try again.")

    def perform_destroy(self, instance):
        """Soft delete by setting is_active=False"""
        try:
            with transaction.atomic():
                instance.is_active = False
                instance.save()
                logger.info(f"Bid deactivated: {instance.id} by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error deactivating bid: {str(e)}")
            raise ValidationError("Unable to deactivate bid. Please try again.")


class MyBidsView(generics.ListAPIView):
    """List current user's bids"""
    serializer_class = BidSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'is_active']
    ordering_fields = ['submitted_at', 'bid_amount']
    ordering = ['-submitted_at']

    def get_queryset(self):
        return Bid.objects.select_related(
            'cargo_listing'
        ).filter(bidder=self.request.user)


class ListingBidsView(generics.ListAPIView):
    """List all bids for a specific cargo listing (only for listing owner)"""
    serializer_class = BidSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'is_active']
    ordering_fields = ['submitted_at', 'bid_amount']
    ordering = ['bid_amount']  # Lowest bids first

    def get_queryset(self):
        listing_id = self.kwargs['listing_id']
        try:
            listing = CargoListing.objects.get(id=listing_id, posted_by=self.request.user)
        except CargoListing.DoesNotExist:
            raise NotFound("Cargo listing not found or you don't have permission to view its bids.")
        
        return Bid.objects.select_related('bidder').filter(
            cargo_listing=listing
        )


# ============================================================================
# BID RESPONSE AND NOTIFICATIONS
# ============================================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def respond_to_bid(request, bid_id):
    """
    Accept or reject a bid (only for cargo listing owner)
    """
    try:
        bid = get_object_or_404(
            Bid.objects.select_related('cargo_listing', 'bidder'),
            id=bid_id
        )
        
        # Check permissions
        if bid.cargo_listing.posted_by != request.user:
            raise PermissionDenied("You can only respond to bids on your own cargo listings.")
        
        serializer = BidResponseSerializer(
            data=request.data,
            context={'bid': bid, 'request': request}
        )
        
        if serializer.is_valid():
            with transaction.atomic():
                updated_bid = serializer.save()
                logger.info(f"Bid {bid_id} {serializer.validated_data['action']}ed by user {request.user.id}")
                
                return Response({
                    'message': f'Bid {serializer.validated_data["action"]}ed successfully',
                    'bid': BidSerializer(updated_bid).data
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error responding to bid {bid_id}: {str(e)}")
        return Response(
            {'error': 'Unable to process bid response. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class BidNotificationListView(generics.ListAPIView):
    """List user's bid notifications"""
    serializer_class = BidNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_read', 'notification_type']
    ordering_fields = ['sent_at']
    ordering = ['-sent_at']

    def get_queryset(self):
        return BidNotification.objects.select_related(
            'recipient', 'bid__cargo_listing', 'bid__bidder'
        ).filter(recipient=self.request.user)


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = get_object_or_404(
            BidNotification,
            id=notification_id,
            recipient=request.user
        )
        
        notification.is_read = True
        notification.save()
        
        return Response({
            'message': 'Notification marked as read',
            'notification': BidNotificationSerializer(notification).data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {str(e)}")
        return Response(
            {'error': 'Unable to update notification. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all user's notifications as read"""
    try:
        updated_count = BidNotification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'message': f'{updated_count} notifications marked as read'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Unable to update notifications. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# STATISTICS AND DASHBOARD
# ============================================================================

class BidStatisticsView(generics.RetrieveAPIView):
    """Get user's bid statistics"""
    serializer_class = BidStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get or create statistics for current user"""
        try:
            stats, created = BidStatistics.objects.get_or_create(
                user=self.request.user
            )
            if created:
                logger.info(f"Created bid statistics for user {self.request.user.id}")
            return stats
        except Exception as e:
            logger.error(f"Error getting bid statistics for user {self.request.user.id}: {str(e)}")
            raise ValidationError("Unable to retrieve statistics. Please try again.")


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_summary(request):
    """
    Get dashboard summary for current user
    """
    try:
        user = request.user
        
        # Get user's listings summary
        my_listings = CargoListing.objects.filter(posted_by=user).aggregate(
            total_listings=Count('id'),
            open_listings=Count('id', filter=Q(status='OPEN')),
            in_progress_listings=Count('id', filter=Q(status='IN_PROGRESS')),
            completed_listings=Count('id', filter=Q(status='COMPLETED')),
            total_bids_received=Count('bids', filter=Q(bids__is_active=True))
        )
        
        # Get user's bids summary
        my_bids = Bid.objects.filter(bidder=user, is_active=True).aggregate(
            total_bids=Count('id'),
            pending_bids=Count('id', filter=Q(status='pending')),
            accepted_bids=Count('id', filter=Q(status='accepted')),
            rejected_bids=Count('id', filter=Q(status='rejected')),
            average_bid=Avg('bid_amount')
        )
        
        # Get unread notifications count
        unread_notifications = BidNotification.objects.filter(
            recipient=user,
            is_read=False
        ).count()
        
        return Response({
            'listings': my_listings,
            'bids': my_bids,
            'unread_notifications': unread_notifications
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Unable to load dashboard. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )