from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class CargoType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, blank=True, default='Unnamed Type')
    # Description field for additional details
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CargoListing(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_CHOICES = [
        ('CASH', 'Cash'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CARD', 'Card Payment'),
    ]

    CARGO_TYPE_CHOICES = [
        ('general', 'General Goods'),
        ('perishable', 'Perishable Goods'),
        ('fragile', 'Fragile Items'),
        ('machinery', 'Machinery/Equipment'),
        ('construction', 'Construction Materials'),
        ('furniture', 'Furniture'),
        ('electronics', 'Electronics'),
        ('other', 'Other'),
    ]

    # Primary key as UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic info - auto-generated title
    cargo_type = models.CharField(max_length=50, choices=CARGO_TYPE_CHOICES)
    description = models.TextField(max_length=500, blank=True, help_text="Detailed description of the cargo")
    
    # Physical properties
    weight = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Weight", 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    volume = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Volume", 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    estimated_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Estimated value of cargo",
        default=Decimal('0.00')
    )
    
    # Locations (simplified - just string addresses)
    pickup_location = models.CharField(max_length=255)
    delivery_location = models.CharField(max_length=255)
    
    # Dates
    pickup_date = models.DateField(
        help_text="Date when cargo should be picked up", 
        default=None, 
        null=True
    )
    delivery_date = models.DateField(
        help_text="Date when cargo should be delivered", 
        default=None, 
        null=True
    )
    
    # Budget and payment
    budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))], 
        null=True, 
        blank=True,
        help_text="Budget for the cargo transport", 
        default=Decimal('0.00')
    )
    preferred_payment = models.CharField(
        max_length=20, 
        choices=PAYMENT_CHOICES, 
        default='CASH'
    )
    
    # Requirements
    additional_requirements = models.TextField(blank=True)
    
    # Auto-generated fields
    title = models.CharField(max_length=200, blank=True)  # Auto-generated
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        # Add indexes for better performance
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['cargo_type', 'status']),
            models.Index(fields=['pickup_location']),
            models.Index(fields=['delivery_location']),
            models.Index(fields=['pickup_date']),
        ]

    def save(self, *args, **kwargs):
        # Auto-generate title if not provided
        if not self.title:
            cargo_type_display = dict(self.CARGO_TYPE_CHOICES).get(self.cargo_type, self.cargo_type)
            self.title = f"{cargo_type_display} - {self.pickup_location} to {self.delivery_location}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    @property
    def cargo_type_display(self):
        """Get human-readable cargo type"""
        return dict(self.CARGO_TYPE_CHOICES).get(self.cargo_type, self.cargo_type)
    
    @property
    def status_display(self):
        """Get human-readable status"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    @property
    def preferred_payment_display(self):
        """Get human-readable payment method"""
        return dict(self.PAYMENT_CHOICES).get(self.preferred_payment, self.preferred_payment)
    
    @property
    def photo_count(self):
        """Get count of photos for this cargo"""
        return self.cargo_photos.count()
    
    @property
    def days_until_pickup(self):
        """Calculate days until pickup date"""
        if self.pickup_date:
            from django.utils import timezone
            today = timezone.now().date()
            return (self.pickup_date - today).days
        return None


class CargoPhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cargo = models.ForeignKey(CargoListing, on_delete=models.CASCADE, related_name='cargo_photos')
    image = models.ImageField(upload_to='cargo_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.cargo.title}"