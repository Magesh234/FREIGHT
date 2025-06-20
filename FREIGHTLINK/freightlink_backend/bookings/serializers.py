# bookings/serializers.py
from trucks.models import Truck
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Booking, BookingStatusUpdate, BookingDocument

from trucks.serializers import TruckSerializer  # Assuming you have truck serializers

User = get_user_model()


class BookingDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = BookingDocument
        fields = [
            'id', 'document_type', 'title', 'file', 
            'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at']


class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = BookingStatusUpdate
        fields = [
            'id', 'old_status', 'new_status', 'updated_by', 
            'updated_by_name', 'notes', 'timestamp'
        ]
        read_only_fields = ['updated_by', 'timestamp']


class BookingListSerializer(serializers.ModelSerializer):
    """Serializer for listing bookings (minimal data)"""
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    truck_info = serializers.CharField(source='truck.__str__', read_only=True)
    duration_hours = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'customer', 'customer_name',
            'truck', 'truck_info', 'pickup_date', 'expected_delivery_date',
            'pickup_address', 'delivery_address', 'status', 'quoted_price',
            'final_price', 'duration_hours', 'is_overdue', 'created_at'
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed booking view"""
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    truck_owner_name = serializers.CharField(source='truck.owner.get_full_name', read_only=True)
    truck_details = TruckSerializer(source='truck', read_only=True)
    duration_hours = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    status_updates = BookingStatusUpdateSerializer(many=True, read_only=True)
    documents = BookingDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'customer', 'customer_name', 'customer_email',
            'truck', 'truck_details', 'truck_owner_name', 'pickup_date', 
            'expected_delivery_date', 'pickup_address', 'delivery_address',
            'cargo_description', 'cargo_type', 'cargo_weight', 'cargo_volume',
            'quoted_price', 'final_price', 'status', 'special_instructions',
            'contact_phone', 'contact_email', 'duration_hours', 'is_overdue',
            'created_at', 'updated_at', 'confirmed_at', 'completed_at',
            'status_updates', 'documents'
        ]
class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings with flexible field names"""
    
    # Use PrimaryKeyRelatedField to handle truck ID conversion
    truck = serializers.PrimaryKeyRelatedField(
        queryset=Truck.objects.filter(is_active=True),
        required=False
    )
    
    # Alternative field names for backward compatibility
    truck_id = serializers.CharField(write_only=True, required=False, help_text="Alternative to 'truck'")
    delivery_date = serializers.DateTimeField(write_only=True, required=False, help_text="Alternative to 'expected_delivery_date'")
    cargo_details = serializers.CharField(write_only=True, required=False, help_text="Alternative to 'cargo_description'")
    
    class Meta:
        model = Booking
        fields = [
            'truck', 'pickup_date', 'expected_delivery_date',
            'pickup_address', 'delivery_address', 'cargo_description',
            # Alternative fields for backward compatibility
            'truck_id', 'delivery_date', 'cargo_details'
        ]
        extra_kwargs = {
            'truck': {'required': False},
            'expected_delivery_date': {'required': False},
            'cargo_description': {'required': False},
        }
    
    def validate(self, attrs):
        """Handle field name mapping and validation"""
        # Map alternative field names to standard ones
        if 'truck_id' in attrs:
            if 'truck' in attrs:
                raise serializers.ValidationError("Provide either 'truck' or 'truck_id', not both.")
            
            # Convert truck_id string to Truck instance
            try:
                truck_id = int(attrs.pop('truck_id'))  # Convert to int first
                truck = Truck.objects.get(id=truck_id, is_active=True)
                attrs['truck'] = truck
            except (ValueError, TypeError):
                raise serializers.ValidationError({"truck_id": "Invalid truck ID format."})
            except Truck.DoesNotExist:
                raise serializers.ValidationError({"truck_id": "Truck with this ID does not exist or is not active."})
        
        if 'delivery_date' in attrs:
            if 'expected_delivery_date' in attrs:
                raise serializers.ValidationError("Provide either 'expected_delivery_date' or 'delivery_date', not both.")
            attrs['expected_delivery_date'] = attrs.pop('delivery_date')
        
        if 'cargo_details' in attrs:
            if 'cargo_description' in attrs:
                raise serializers.ValidationError("Provide either 'cargo_description' or 'cargo_details', not both.")
            attrs['cargo_description'] = attrs.pop('cargo_details')
        
        # Ensure required fields are present after mapping
        required_fields = ['truck', 'expected_delivery_date', 'cargo_description']
        missing_fields = [field for field in required_fields if field not in attrs]
        
        if missing_fields:
            raise serializers.ValidationError({
                field: ["This field is required."] for field in missing_fields
            })
        
        return attrs
    
    def validate_pickup_date(self, value):
        """Ensure pickup date is not in the past"""
        if value < timezone.now():
            raise serializers.ValidationError("Pickup date cannot be in the past.")
        return value
    
    def validate_expected_delivery_date(self, value):
        """Ensure delivery date is after pickup date"""
        pickup_date = self.initial_data.get('pickup_date')
        if pickup_date and value <= pickup_date:
            raise serializers.ValidationError(
                "Expected delivery date must be after pickup date."
            )
        return value
    
    def validate_truck(self, value):
        """Validate truck availability"""
        # Value should already be a Truck instance from PrimaryKeyRelatedField or from validate()
        pickup_date = self.initial_data.get('pickup_date')
        expected_delivery_date = self.initial_data.get('expected_delivery_date') or self.initial_data.get('delivery_date')
        
        if pickup_date and expected_delivery_date:
            # Convert string dates to datetime if needed
            try:
                if isinstance(pickup_date, str):
                    pickup_date = timezone.datetime.fromisoformat(pickup_date.replace('Z', '+00:00'))
                if isinstance(expected_delivery_date, str):
                    expected_delivery_date = timezone.datetime.fromisoformat(expected_delivery_date.replace('Z', '+00:00'))
            except ValueError:
                # If date parsing fails, skip availability check for now
                pass
            else:
                # Check if truck has conflicting bookings
                conflicting_bookings = Booking.objects.filter(
                    truck=value,
                    status__in=['pending', 'confirmed', 'in_progress'],
                    pickup_date__lt=expected_delivery_date,
                    expected_delivery_date__gt=pickup_date
                )
                
                if conflicting_bookings.exists():
                    raise serializers.ValidationError(
                        "Truck is not available for the selected dates."
                    )
        
        # Check if truck has is_available method/property
        if hasattr(value, 'is_available') and not value.is_available:
            raise serializers.ValidationError("Selected truck is not available.")
        
        return value
    
    def validate_cargo_weight(self, value):
        """Validate cargo weight against truck capacity - only if provided"""
        if value is None:
            return value
            
        truck = self.initial_data.get('truck') or self.initial_data.get('truck_id')
        if truck and hasattr(truck, 'capacity_tons') and truck.capacity_tons:
            if value > truck.capacity_tons:
                raise serializers.ValidationError(
                    f"Cargo weight ({value}t) exceeds truck capacity ({truck.capacity_tons}t)."
                )
        return value
    
    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        # Set default values for optional fields
        validated_data.setdefault('cargo_type', 'general')
        validated_data.setdefault('contact_phone', self.context['request'].user.phone if hasattr(self.context['request'].user, 'phone') else '')
        validated_data.setdefault('contact_email', self.context['request'].user.email)
        return super().create(validated_data)

class BookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating bookings"""
    
    class Meta:
        model = Booking
        fields = [
            'pickup_date', 'expected_delivery_date', 'pickup_address',
            'delivery_address', 'cargo_description', 'cargo_type',
            'cargo_weight', 'cargo_volume', 'special_instructions',
            'contact_phone', 'contact_email', 'quoted_price', 'final_price'
        ]
    
    def validate(self, attrs):
        """Prevent updates to confirmed or completed bookings"""
        if self.instance.status in ['completed', 'cancelled']:
            raise serializers.ValidationError(
                "Cannot update completed or cancelled bookings."
            )
        return attrs


class BookingStatusUpdateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating status updates"""
    
    class Meta:
        model = BookingStatusUpdate
        fields = ['booking', 'new_status', 'notes']
    
    def validate_new_status(self, value):
        """Validate status transition"""
        booking = self.initial_data.get('booking')
        if booking and booking.status == value:
            raise serializers.ValidationError(
                "New status must be different from current status."
            )
        return value
    
    def create(self, validated_data):
        booking = validated_data['booking']
        validated_data['old_status'] = booking.status
        validated_data['updated_by'] = self.context['request'].user
        
        # Update the booking status
        booking.status = validated_data['new_status']
        if validated_data['new_status'] == 'confirmed':
            booking.confirmed_at = timezone.now()
        elif validated_data['new_status'] == 'completed':
            booking.completed_at = timezone.now()
        booking.save()
        
        return super().create(validated_data)