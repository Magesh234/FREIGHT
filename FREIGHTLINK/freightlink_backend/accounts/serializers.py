from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['user']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)  # Nested serializer for profile
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'full_name']
        read_only_fields = ['id', 'username']  # Username might be read-only if email is used for login
    
    def get_full_name(self, obj):
        """Return the full name by combining first_name and last_name"""
        return f"{obj.first_name} {obj.last_name}".strip()

class UserCreateSerializer(serializers.ModelSerializer):
    """
    This serializer is used for user registration.
    It handles the fields that your frontend is sending.
    """
    # Fields that match your frontend
    full_name = serializers.CharField(max_length=255, write_only=True)
    phone_number = serializers.CharField(max_length=20, write_only=True, required=False)
    user_type = serializers.CharField(max_length=50, write_only=True, required=False)
    
    # Profile data (optional, for more complex profile setup)
    profile = UserProfileSerializer(required=False, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 
            'first_name', 'last_name', 'full_name', 
            'phone_number', 'user_type', 'profile'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            'username': {'required': False},  # Make username optional if using email for login
        }
    
    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_full_name(self, value):
        """Validate full name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Full name is required.")
        return value.strip()
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if value and not value.startswith('+'):
            raise serializers.ValidationError("Phone number must be in international format (+XXX...).")
        return value
    
    def create(self, validated_data):
        # Extract the custom fields
        full_name = validated_data.pop('full_name', '')
        phone_number = validated_data.pop('phone_number', '')
        user_type = validated_data.pop('user_type', '')
        profile_data = validated_data.pop('profile', {})
        
        # Split full name into first_name and last_name
        name_parts = full_name.split(' ', 1)
        validated_data['first_name'] = name_parts[0] if name_parts else ''
        validated_data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
        
        # Generate username from email if not provided
        if not validated_data.get('username'):
            validated_data['username'] = validated_data['email'].split('@')[0]
            
            # Ensure username is unique
            base_username = validated_data['username']
            counter = 1
            while User.objects.filter(username=validated_data['username']).exists():
                validated_data['username'] = f"{base_username}{counter}"
                counter += 1
        
        # Create the user
        user = User.objects.create_user(**validated_data)
        
        # Create or update profile with additional data
        profile_defaults = {}
        if phone_number:
            profile_defaults['phone_number'] = phone_number
        if user_type:
            profile_defaults['user_type'] = user_type
        
        # Merge with any additional profile data
        profile_defaults.update(profile_data)
        
        # Create profile if we have any profile data
        if profile_defaults:
            UserProfile.objects.update_or_create(
                user=user,
                defaults=profile_defaults
            )
        else:
            # Create empty profile if none exists
            UserProfile.objects.get_or_create(user=user)
        
        return user
    
    def update(self, instance, validated_data):
        # Extract custom fields
        full_name = validated_data.pop('full_name', None)
        phone_number = validated_data.pop('phone_number', None)
        user_type = validated_data.pop('user_type', None)
        profile_data = validated_data.pop('profile', {})
        
        # Handle full name update
        if full_name:
            name_parts = full_name.split(' ', 1)
            validated_data['first_name'] = name_parts[0] if name_parts else ''
            validated_data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
        
        # Update user instance
        instance = super().update(instance, validated_data)
        
        # Update profile
        profile, created = UserProfile.objects.get_or_create(user=instance)
        
        if phone_number is not None:
            profile.phone_number = phone_number
        if user_type is not None:
            profile.user_type = user_type
        
        # Update any additional profile fields
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        
        profile.save()
        
        return instance

# Alternative simpler serializer if you want to keep it minimal
class SimpleUserCreateSerializer(serializers.ModelSerializer):
    """
    Simplified version that just handles the basic fields from your frontend
    """
    full_name = serializers.CharField(max_length=255, write_only=True)
    phone_number = serializers.CharField(max_length=20, write_only=True, required=False)
    user_type = serializers.CharField(max_length=50, write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'full_name', 'phone_number', 'user_type']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        full_name = validated_data.pop('full_name', '')
        phone_number = validated_data.pop('phone_number', '')
        user_type = validated_data.pop('user_type', '')
        
        # Split full name
        name_parts = full_name.split(' ', 1)
        validated_data['first_name'] = name_parts[0] if name_parts else ''
        validated_data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
        
        # Generate username from email
        validated_data['username'] = validated_data['email'].split('@')[0]
        
        # Ensure unique username
        base_username = validated_data['username']
        counter = 1
        while User.objects.filter(username=validated_data['username']).exists():
            validated_data['username'] = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Create profile with additional data
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'phone_number': phone_number,
                'user_type': user_type,
            }
        )
        
        return user