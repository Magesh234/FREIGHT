from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from .models import Bid, BidNotification, BidStatistics
from cargo.models import CargoListing  # Import CargoListing from cargo app

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested relationships"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']
        read_only_fields = ['id', 'username']


class CargoListingSerializer(serializers.ModelSerializer):
    """Serializer for CargoListing model from cargo app"""
    posted_by = UserBasicSerializer(read_only=True)
    bid_count = serializers.SerializerMethodField()
    lowest_bid = serializers.SerializerMethodField()
    highest_bid = serializers.SerializerMethodField()
    cargo_type_display = serializers.ReadOnlyField()
    status_display = serializers.ReadOnlyField()
    preferred_payment_display = serializers.ReadOnlyField()
    photo_count = serializers.ReadOnlyField()
    days_until_pickup = serializers.ReadOnlyField()
    
    class Meta:
        model = CargoListing
        fields = [
            'id', 'title', 'cargo_type', 'cargo_type_display', 'description',
            'weight', 'volume', 'estimated_value', 'pickup_location', 
            'delivery_location', 'pickup_date', 'delivery_date', 'budget',
            'preferred_payment', 'preferred_payment_display', 'additional_requirements',
            'status', 'status_display', 'posted_by', 'created_at', 'updated_at',
            'bid_count', 'lowest_bid', 'highest_bid', 'photo_count', 'days_until_pickup'
        ]
        read_only_fields = ['id', 'title', 'posted_by', 'created_at', 'updated_at']
    
    def get_bid_count(self, obj):
        """Get total number of active bids"""
        return obj.bids.filter(is_active=True, status='pending').count()
    
    def get_lowest_bid(self, obj):
        """Get the lowest bid amount"""
        bid = obj.bids.filter(is_active=True, status='pending').order_by('bid_amount').first()
        return float(bid.bid_amount) if bid else None
    
    def get_highest_bid(self, obj):
        """Get the highest bid amount"""
        bid = obj.bids.filter(is_active=True, status='pending').order_by('-bid_amount').first()
        return float(bid.bid_amount) if bid else None


class CargoListingSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for cargo listing lists"""
    posted_by_name = serializers.CharField(source='posted_by.username', read_only=True)
    bid_count = serializers.SerializerMethodField()
    cargo_type_display = serializers.ReadOnlyField()
    
    class Meta:
        model = CargoListing
        fields = [
            'id', 'title', 'cargo_type', 'cargo_type_display', 'posted_by_name', 
            'pickup_location', 'delivery_location', 'budget', 'status', 
            'created_at', 'bid_count'
        ]
    
    def get_bid_count(self, obj):
        return getattr(obj, 'bid_count', 0)  # Expects annotation from view


class BidSerializer(serializers.ModelSerializer):
    """Main serializer for Bid model"""
    bidder = UserBasicSerializer(read_only=True)
    cargo_listing = CargoListingSummarySerializer(read_only=True)
    cargo_listing_id = serializers.PrimaryKeyRelatedField(
        source='cargo_listing',
        queryset=CargoListing.objects.all(),
        write_only=True
    )
    delivery_time_display = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Bid
        fields = [
            'id', 'cargo_listing', 'cargo_listing_id','bidder', 'bid_amount',
            'estimated_delivery_time', 'custom_delivery_time',
            'message_to_shipper', 'status', 'submitted_at',
            'expires_at', 'responded_at', 'is_active',
            'shipper_notes', 'delivery_time_display', 'is_expired'
        ]
        read_only_fields = [
            'id', 'bidder', 'cargo_listing', 'status',
            'submitted_at', 'responded_at', 'shipper_notes'
        ]
    
    def validate_bid_amount(self, value):
        """Validate bid amount"""
        if value < Decimal('1.00'):
            raise serializers.ValidationError("Bid amount must be at least 1.00 KSh")
        if value > Decimal('10000000.00'):  # 10 million KSh max
            raise serializers.ValidationError("Bid amount cannot exceed 10,000,000 KSh")
        return value
    
    def validate_expires_at(self, value):
        """Validate expiration date"""
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future")
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        # Check if custom delivery time is provided when needed
        if attrs.get('estimated_delivery_time') == 'custom':
            if not attrs.get('custom_delivery_time'):
                raise serializers.ValidationError({
                    'custom_delivery_time': 'Custom delivery time must be specified when selecting custom option'
                })
        
        # Clear custom_delivery_time if not using custom option
        elif attrs.get('custom_delivery_time'):
            attrs['custom_delivery_time'] = None
        
        return attrs

    def validate_cargo_listing_id(self, value):
        """Validate that cargo listing is open for bids"""
        if value.status != 'OPEN':
            raise serializers.ValidationError("This cargo listing is not open for bids")
        return value


class BidCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bids"""
    # Accept frontend field names and map them
    cargo_id = serializers.UUIDField(write_only=True, required=False)
    delivery_timeframe = serializers.CharField(write_only=True, required=False)
    bid_message = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    cargo_listing = serializers.PrimaryKeyRelatedField(
        queryset=CargoListing.objects.filter(status='OPEN'),  # Only open listings
        required=False
    )
    
    class Meta:
        model = Bid
        fields = [
            'cargo_id', 
            'cargo_listing', 
            'bid_amount', 
            'delivery_timeframe',     # Frontend field name
            'bid_message',           # Frontend field name
            'expires_at'
        ]
    
    def validate(self, data):
        # Map cargo_id to cargo_listing if cargo_id is provided
        cargo_id = data.pop('cargo_id', None)
        if cargo_id and not data.get('cargo_listing'):
            try:
                cargo_listing = CargoListing.objects.get(id=cargo_id)
                if cargo_listing.status != 'OPEN':
                    raise serializers.ValidationError({
                        'non_field_errors': [f'Cargo listing "{cargo_listing.title}" is not open for bids']
                    })
                data['cargo_listing'] = cargo_listing
                print(f"Found cargo listing: {cargo_listing.id} - {cargo_listing.title}")
            except CargoListing.DoesNotExist:
                print(f"CargoListing with ID {cargo_id} does not exist")
                existing_ids = list(CargoListing.objects.filter(status='OPEN').values_list('id', flat=True))
                print(f"Available open CargoListing IDs: {existing_ids}")
                raise serializers.ValidationError({
                    'non_field_errors': [f'Cargo listing with ID {cargo_id} does not exist or is not open for bids']
                })
        
        # Map frontend fields to model fields
        delivery_timeframe = data.pop('delivery_timeframe', None)
        if delivery_timeframe:
            # Map delivery timeframe options to match model choices
            timeframe_mapping = {
                'same-day': 'same-day',
                'next-day': 'next-day', 
                '2-3-days': '2-3-days',
                '4-7-days': '4-7-days',
                'custom': 'custom',
                'unknown': 'unknown'
            }
            mapped_timeframe = timeframe_mapping.get(delivery_timeframe, delivery_timeframe)
            data['estimated_delivery_time'] = mapped_timeframe
            print(f"Mapped delivery_timeframe '{delivery_timeframe}' to '{mapped_timeframe}'")
        
        bid_message = data.pop('bid_message', None)
        if bid_message:
            data['message_to_shipper'] = bid_message
        
        # Ensure we have a cargo_listing
        if not data.get('cargo_listing'):
            raise serializers.ValidationError({'non_field_errors': ['Cargo listing is required']})
        
        # Check if user already has a bid for this listing
        if self.context['request'].user.is_authenticated:
            existing_bid = Bid.objects.filter(
                cargo_listing=data['cargo_listing'],
                bidder=self.context['request'].user,
                status='pending'
            ).first()
            if existing_bid:
                raise serializers.ValidationError({
                    'non_field_errors': ['You already have a pending bid for this cargo listing']
                })
        
        print(f"Final validated data: {data}")
        return data
    
    def create(self, validated_data):
        # Set the bidder if authenticated
        if self.context['request'].user.is_authenticated:
            validated_data['bidder'] = self.context['request'].user
        
        return super().create(validated_data)


class BidUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating bids (limited fields)"""
    class Meta:
        model = Bid
        fields = ['bid_amount', 'estimated_delivery_time', 'custom_delivery_time', 'message_to_shipper']
    
    def validate(self, attrs):
        """Ensure bid can be updated"""
        if self.instance.status != 'pending':
            raise serializers.ValidationError("Only pending bids can be updated")
        
        # Custom delivery time validation
        estimated_time = attrs.get('estimated_delivery_time', self.instance.estimated_delivery_time)
        if estimated_time == 'custom':
            custom_time = attrs.get('custom_delivery_time', self.instance.custom_delivery_time)
            if not custom_time:
                raise serializers.ValidationError({
                    'custom_delivery_time': 'Custom delivery time must be specified'
                })
        
        return attrs


class BidResponseSerializer(serializers.Serializer):
    """Serializer for accepting/rejecting bids"""
    action = serializers.ChoiceField(choices=['accept', 'reject'])
    shipper_notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    
    def validate_action(self, value):
        """Validate action is allowed"""
        bid = self.context.get('bid')
        if not bid or bid.status != 'pending':
            raise serializers.ValidationError("Only pending bids can be accepted or rejected")
        return value
    
    def save(self):
        """Process the bid response"""
        bid = self.context['bid']
        action = self.validated_data['action']
        shipper_notes = self.validated_data.get('shipper_notes', '')
        
        if action == 'accept':
            bid.accept(shipper_notes)
            notification_type = 'bid_accepted'
            message = f"Your bid of {bid.bid_amount} KSh has been accepted for '{bid.cargo_listing.title}'"
            
            # Update cargo listing status to IN_PROGRESS
            bid.cargo_listing.status = 'IN_PROGRESS'
            bid.cargo_listing.save()
            
        else:
            bid.reject(shipper_notes)
            notification_type = 'bid_rejected' 
            message = f"Your bid of {bid.bid_amount} KSh has been rejected for '{bid.cargo_listing.title}'"
        
        # Create notification for bidder
        BidNotification.objects.create(
            recipient=bid.bidder,
            bid=bid,
            notification_type=notification_type,
            message=message
        )
        
        return bid


class BidNotificationSerializer(serializers.ModelSerializer):
    """Serializer for bid notifications"""
    recipient = UserBasicSerializer(read_only=True)
    bid = BidSerializer(read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = BidNotification
        fields = [
            'id', 'recipient', 'bid', 'notification_type',
            'notification_type_display', 'message', 'is_read', 'sent_at'
        ]
        read_only_fields = ['id', 'recipient', 'bid', 'notification_type', 'message', 'sent_at']


class BidStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for bid statistics"""
    user = UserBasicSerializer(read_only=True)
    acceptance_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = BidStatistics
        fields = [
            'user', 'total_bids_submitted', 'bids_accepted', 'bids_rejected',
            'average_bid_amount', 'total_listings_posted', 'total_bids_received',
            'average_bids_per_listing', 'acceptance_rate'
        ]
        read_only_fields = [
            'user', 'total_bids_submitted', 'bids_accepted', 'bids_rejected',
            'average_bid_amount', 'total_listings_posted', 'total_bids_received',
            'average_bids_per_listing'
        ]


class BidSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for bid lists"""
    bidder_name = serializers.CharField(source='bidder.username', read_only=True)
    listing_title = serializers.CharField(source='cargo_listing.title', read_only=True)
    delivery_time_display = serializers.ReadOnlyField()
    
    class Meta:
        model = Bid
        fields = [
            'id', 'bidder_name', 'listing_title', 'bid_amount',
            'delivery_time_display', 'status', 'submitted_at'
        ]