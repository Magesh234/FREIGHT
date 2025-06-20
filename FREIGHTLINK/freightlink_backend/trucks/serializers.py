# serializers.py
from rest_framework import serializers
from .models import Truck, TruckImage

class TruckImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TruckImage
        fields = ['id', 'image', 'caption', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class TruckSerializer(serializers.ModelSerializer):
    images = TruckImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    truck_type_display = serializers.CharField(source='get_truck_type_display', read_only=True)
    rate_type_display = serializers.CharField(source='get_rate_type_display', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Truck
        fields = [
            'id', 'truck_type', 'truck_type_display', 'capacity_tons', 
            'make_model', 'year', 'current_location', 'available_from', 
            'available_to', 'preferred_routes', 'rate_amount', 'rate_type',
            'rate_type_display', 'additional_notes', 'is_active', 
            'created_at', 'updated_at', 'images', 'uploaded_images',
            'owner_name', 'owner_username', 'is_available'
        ]
        # Exclude owner from fields that can be set - it's automatically assigned
        read_only_fields = ['created_at', 'updated_at', 'owner', 'owner_name', 'owner_username']
    
    def validate(self, data):
        if data.get('available_to') and data.get('available_from'):
            if data['available_to'] < data['available_from']:
                raise serializers.ValidationError(
                    "Available to date must be after available from date."
                )
        return data
    
    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        truck = Truck.objects.create(**validated_data)
        
        # Handle image uploads
        for image in uploaded_images:
            TruckImage.objects.create(truck=truck, image=image)
        
        return truck
    
    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        
        # Update truck instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle new image uploads
        for image in uploaded_images:
            TruckImage.objects.create(truck=instance, image=image)
        
        return instance


class TruckListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing trucks"""
    truck_type_display = serializers.CharField(source='get_truck_type_display', read_only=True)
    rate_type_display = serializers.CharField(source='get_rate_type_display', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    image_count = serializers.IntegerField(source='images.count', read_only=True)
    
    class Meta:
        model = Truck
        fields = [
            'id', 'truck_type', 'truck_type_display', 'capacity_tons',
            'make_model', 'year', 'current_location', 'rate_amount',
            'rate_type_display', 'is_available', 'image_count', 'created_at'
        ]