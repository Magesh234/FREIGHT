from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Truck(models.Model):
    TRUCK_TYPE_CHOICES = [
        ('pickup', 'Pickup Truck'),
        ('cargo_van', 'Cargo Van'),
        ('closed_body', 'Closed Body Truck'),
        ('flatbed', 'Flatbed Truck'),
        ('refrigerated', 'Refrigerated Truck'),
        ('tipper', 'Tipper Truck'),
        ('tanker', 'Tanker Truck'),
        ('low_loader', 'Low Loader'),
        ('semi_trailer', 'Semi-Trailer'),
        ('other', 'Other'),
    ]
    
    RATE_TYPE_CHOICES = [
        ('per_km', 'Per Kilometer'),
        ('per_trip', 'Per Trip'),
        ('per_hour', 'Per Hour'),
        ('per_day', 'Per Day'),
    ]
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trucks', null=True, blank=True, default=None)
    truck_type = models.CharField(max_length=20, choices=TRUCK_TYPE_CHOICES)
    capacity_tons = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(0.1)], 
        null=True,
        blank=True,
        help_text="Maximum load capacity in tons (e.g., 1.5 for 1.5 tons)"
    )
    make_model = models.CharField(max_length=100, null=True, blank=True, help_text="Make and model of the truck (e.g., 'Ford F-150')")
    year = models.IntegerField(
        validators=[
            MinValueValidator(1950),
            MaxValueValidator(timezone.now().year + 1)
        ],
        null=True,
        blank=True,
        help_text="Year of manufacture (e.g., 2020)"
    )
    current_location = models.CharField(max_length=200)
    available_from = models.DateField()
    available_to = models.DateField(null=True, blank=True)
    preferred_routes = models.TextField(blank=True)
    rate_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,)
    rate_type = models.CharField(max_length=10, choices=RATE_TYPE_CHOICES, default='per_km')
    additional_notes = models.TextField(blank=True)
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.make_model} - {self.get_truck_type_display()} ({self.capacity_tons}t)"
    
    @property
    def is_available(self):
        today = timezone.now().date()
        if self.available_to:
            return self.available_from <= today <= self.available_to
        return self.available_from <= today


class TruckImage(models.Model):
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='truck_images/')
    caption = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f"Image for {self.truck.make_model}"