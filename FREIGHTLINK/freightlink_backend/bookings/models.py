# bookings/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from trucks.models import Truck  # Import your Truck model

User = get_user_model()

class Booking(models.Model):
    BOOKING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    CARGO_TYPE_CHOICES = [
        ('general', 'General Cargo'),
        ('fragile', 'Fragile Items'),
        ('perishable', 'Perishable Goods'),
        ('hazardous', 'Hazardous Materials'),
        ('electronics', 'Electronics'),
        ('furniture', 'Furniture'),
        ('construction', 'Construction Materials'),
        ('automotive', 'Automotive Parts'),
        ('textiles', 'Textiles'),
        ('other', 'Other'),
    ]
    
    # Basic booking information
    booking_reference = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='bookings'
    )
    truck = models.ForeignKey(
        Truck, 
        on_delete=models.CASCADE, 
        related_name='bookings'
    )
    
    # Date information
    pickup_date = models.DateTimeField()
    expected_delivery_date = models.DateTimeField()
    
    # Address information
    pickup_address = models.TextField()
    delivery_address = models.TextField()
    
    # Cargo details
    cargo_description = models.TextField(help_text="Describe what you're shipping")
    cargo_type = models.CharField(max_length=20, choices=CARGO_TYPE_CHOICES, default='general')
    cargo_weight = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.1'))],
        null=True,
        blank=True,
        help_text="Weight in tons (optional)"
    )
    cargo_volume = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.1'))],
        help_text="Volume in cubic meters (optional)"
    )
    
    # Pricing
    quoted_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True,
        default=Decimal('15000.00'), 
        blank=True
    )
    final_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True,
        default=Decimal('15000.00'), 
        blank=True
    )
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='pending')
    special_instructions = models.TextField(blank=True, help_text="Any special handling instructions")
    
    # Contact information
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_reference']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['truck', 'status']),
            models.Index(fields=['pickup_date']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.truck}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        """Generate a unique booking reference"""
        import uuid
        return f"BK{str(uuid.uuid4())[:8].upper()}"
    
    @property
    def duration_hours(self):
        """Calculate expected duration in hours"""
        if self.pickup_date and self.expected_delivery_date:
            delta = self.expected_delivery_date - self.pickup_date
            return delta.total_seconds() / 3600
        return None
    
    @property
    def is_overdue(self):
        """Check if booking is overdue"""
        if self.status in ['completed', 'cancelled']:
            return False
        return timezone.now() > self.expected_delivery_date


class BookingStatusUpdate(models.Model):
    """Track status changes for bookings"""
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='status_updates'
    )
    old_status = models.CharField(max_length=20, choices=Booking.BOOKING_STATUS_CHOICES)
    new_status = models.CharField(max_length=20, choices=Booking.BOOKING_STATUS_CHOICES)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.booking.booking_reference}: {self.old_status} → {self.new_status}"


class BookingDocument(models.Model):
    """Store documents related to bookings"""
    DOCUMENT_TYPE_CHOICES = [
        ('invoice', 'Invoice'),
        ('receipt', 'Receipt'),
        ('delivery_note', 'Delivery Note'),
        ('cargo_manifest', 'Cargo Manifest'),
        ('insurance', 'Insurance Document'),
        ('permit', 'Permit'),
        ('photo', 'Photo'),
        ('other', 'Other'),
    ]
    
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='booking_documents/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.booking.booking_reference} - {self.title}"