from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CargoType, CargoListing, CargoPhoto
from decimal import Decimal

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested representation"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class CargoTypeSerializer(serializers.ModelSerializer):
    """Serializer for CargoType model"""
    class Meta:
        model = CargoType
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        if 'name' not in data or not data['name']:
            data['name']= 'Unnamed Type'
        return data

        


class CargoPhotoSerializer(serializers.ModelSerializer):
    """Serializer for CargoPhoto model"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CargoPhoto
        fields = ['id', 'image', 'image_url', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
    
    def get_image_url(self, obj):
        """Return full URL for the image"""
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class CargoListingListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing view"""
    posted_by = UserSerializer(read_only=True)
    cargo_type_display = serializers.CharField(source='get_cargo_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    preferred_payment_display = serializers.CharField(source='get_preferred_payment_display', read_only=True)
    photo_count = serializers.SerializerMethodField()
    days_until_pickup = serializers.SerializerMethodField()
    
    class Meta:
        model = CargoListing
        fields = [
            'id', 'title', 'cargo_type', 'cargo_type_display', 'weight', 'volume',
            'pickup_location', 'delivery_location', 'pickup_date', 'delivery_date',
            'budget', 'status', 'status_display', 'preferred_payment_display',
            'posted_by', 'created_at', 'updated_at', 'photo_count', 'days_until_pickup'
        ]
        read_only_fields = ['id', 'title', 'created_at', 'updated_at']
    
    def get_photo_count(self, obj):
        """Return count of photos for this cargo"""
        return obj.cargo_photos.count()
    
    def get_days_until_pickup(self, obj):
        """Calculate days until pickup date"""
        from django.utils import timezone
        today = timezone.now().date()
        if obj.pickup_date:
            delta = obj.pickup_date - today
            return delta.days
        return None


class CargoListingDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for retrieve/create/update operations"""
    posted_by = UserSerializer(read_only=True)
    cargo_photos = CargoPhotoSerializer(many=True, read_only=True)
    cargo_type_display = serializers.CharField(source='get_cargo_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    preferred_payment_display = serializers.CharField(source='get_preferred_payment_display', read_only=True)

    # Explicitly allow these fields to be optional
    description = serializers.CharField(required=False, allow_blank=True)
    budget = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)
    
    
    # Additional computed fields
    days_until_pickup = serializers.SerializerMethodField()
    days_until_delivery = serializers.SerializerMethodField()
    estimated_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = CargoListing
        fields = [
            'id', 'title', 'cargo_type', 'cargo_type_display', 'description',
            'weight', 'volume', 'estimated_value', 'pickup_location', 
            'delivery_location', 'pickup_date', 'delivery_date', 'budget',
            'preferred_payment', 'preferred_payment_display', 'additional_requirements',
            'status', 'status_display', 'posted_by', 'created_at', 'updated_at',
            'cargo_photos', 'days_until_pickup', 'days_until_delivery', 'estimated_duration'
        ]
        read_only_fields = ['id', 'title', 'posted_by', 'created_at', 'updated_at']
    
    def get_days_until_pickup(self, obj):
        """Calculate days until pickup date"""
        from django.utils import timezone
        today = timezone.now().date()
        if obj.pickup_date:
            delta = obj.pickup_date - today
            return delta.days
        return None
    
    def get_days_until_delivery(self, obj):
        """Calculate days until delivery date"""
        from django.utils import timezone
        today = timezone.now().date()
        if obj.delivery_date:
            delta = obj.delivery_date - today
            return delta.days
        return None
    
    def get_estimated_duration(self, obj):
        """Calculate estimated duration between pickup and delivery"""
        if obj.pickup_date and obj.delivery_date:
            delta = obj.delivery_date - obj.pickup_date
            return delta.days
        return None
    
    def validate(self, data):
        """Custom validation"""
        pickup_date = data.get('pickup_date')
        delivery_date = data.get('delivery_date')
        
        # Validate dates
        if pickup_date and delivery_date:
            if pickup_date >= delivery_date:
                raise serializers.ValidationError(
                    "Delivery date must be after pickup date."
                )
        
        # Validate pickup date is not in the past
        from django.utils import timezone
        today = timezone.now().date()
        if pickup_date and pickup_date < today:
            raise serializers.ValidationError(
                "Pickup date cannot be in the past."
            )
        
        # Validate budget and estimated value
        budget = data.get('budget')
        estimated_value = data.get('estimated_value')
        
        if budget and estimated_value:
            if budget > estimated_value:
                raise serializers.ValidationError(
                    "Budget cannot exceed estimated value of cargo."
                )
        
        return data
    
    def create(self, validated_data):
        """Create cargo listing with current user as posted_by"""
        validated_data['posted_by'] = self.context['request'].user
        return super().create(validated_data)


class CargoListingCreateSerializer(serializers.ModelSerializer):
    """Serializer specifically for creating cargo listings"""
    
    class Meta:
        model = CargoListing
        fields = [
            'cargo_type', 'description', 'weight', 'volume', 'estimated_value',
            'pickup_location', 'delivery_location', 'pickup_date', 'delivery_date',
            'budget', 'preferred_payment', 'additional_requirements'
        ]
    
    def validate(self, data):
        """Custom validation for creation"""
        pickup_date = data.get('pickup_date')
        delivery_date = data.get('delivery_date')
        
        # Validate dates
        if pickup_date and delivery_date:
            if pickup_date >= delivery_date:
                raise serializers.ValidationError(
                    "Delivery date must be after pickup date."
                )
        
        # Validate pickup date is not in the past
        from django.utils import timezone
        today = timezone.now().date()
        if pickup_date and pickup_date < today:
            raise serializers.ValidationError(
                "Pickup date cannot be in the past."
            )
        
        # Validate budget and estimated value
        budget = data.get('budget')
        estimated_value = data.get('estimated_value')
        
        if budget and estimated_value:
            if budget > estimated_value:
                raise serializers.ValidationError(
                    "Budget cannot exceed estimated value of cargo."
                )
        
        # Validate weight and volume are positive
        if data.get('weight') and data.get('weight') <= 0:
            raise serializers.ValidationError("Weight must be greater than 0.")
        
        if data.get('volume') and data.get('volume') <= 0:
            raise serializers.ValidationError("Volume must be greater than 0.")
        
        return data
    
    def create(self, validated_data):
        """Create cargo listing with current user as posted_by"""
        validated_data['posted_by'] = self.context['request'].user
        return super().create(validated_data)