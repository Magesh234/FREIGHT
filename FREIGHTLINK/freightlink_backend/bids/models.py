from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

# Import the CargoListing from the cargo app
from cargo.models import CargoListing


class TimeStampedModel(models.Model):
    """Abstract base class with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Bid(TimeStampedModel):
    """Model for bids submitted by carriers"""
    
    DELIVERY_TIME_CHOICES = [
        ('same-day', 'Same Day'),
        ('next-day', 'Next Day'),
        ('2-3-days', '2-3 Days'),
        ('4-7-days', '4-7 Days'),
        ('custom', 'Custom'),
        ('unknown', 'Unknown'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    # Core bid information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cargo_listing = models.ForeignKey(
        CargoListing,  # Now references your cargo.models.CargoListing
        on_delete=models.CASCADE, 
        related_name='bids'
    )
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='submitted_bids'
    )
    
    # Bid amount in Kenyan Shillings    
    bid_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))],
        help_text="Bid amount in KSh"
    )
    
    # Estimated delivery time
    estimated_delivery_time = models.CharField(
        max_length=20,
        choices=DELIVERY_TIME_CHOICES,
        help_text="How long will delivery take?"
    )
    
    # Custom delivery time (if 'custom' is selected)
    custom_delivery_time = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Specify custom delivery timeframe"
    )
    
    # Optional message to shipper
    message_to_shipper = models.TextField(
        blank=True,
        help_text="Include any conditions, questions, or details about your service"
    )
    
    # Bid status and management
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Timestamps for bid lifecycle
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this bid expires (optional)"
    )
    responded_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When shipper responded to this bid"
    )
    
    # Additional fields
    is_active = models.BooleanField(default=True, db_index=True)
    shipper_notes = models.TextField(
        blank=True,
        help_text="Notes from shipper about this bid"
    )
    
    class Meta:
        db_table = 'freight_bids'
        ordering = ['-submitted_at']
        unique_together = ['cargo_listing', 'bidder']  # One bid per carrier per listing
        indexes = [
            models.Index(fields=['cargo_listing', 'status']),
            models.Index(fields=['bidder', 'status']),
            models.Index(fields=['submitted_at', 'status']),
            models.Index(fields=['bid_amount']),
            models.Index(fields=['estimated_delivery_time']),
        ]
    
    def __str__(self):
        return f"Bid {self.bid_amount} KSh by {self.bidder.username} - {self.get_estimated_delivery_time_display()}"
    
    @property
    def is_expired(self):
        """Check if bid has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def delivery_time_display(self):
        """Get human-readable delivery time"""
        if self.estimated_delivery_time == 'custom' and self.custom_delivery_time:
            return self.custom_delivery_time
        return self.get_estimated_delivery_time_display()
    
    def accept(self, shipper_notes=None):
        """Accept this bid"""
        if self.status == 'pending':
            self.status = 'accepted'
            self.responded_at = timezone.now()
            if shipper_notes:
                self.shipper_notes = shipper_notes
            self.save()
            
            # Reject all other bids for this listing
            Bid.objects.filter(
                cargo_listing=self.cargo_listing,
                status='pending'
            ).exclude(id=self.id).update(
                status='rejected',
                responded_at=timezone.now()
            )
    
    def reject(self, shipper_notes=None):
        """Reject this bid"""
        if self.status == 'pending':
            self.status = 'rejected'
            self.responded_at = timezone.now()
            if shipper_notes:
                self.shipper_notes = shipper_notes
            self.save()
    
    def withdraw(self):
        """Withdraw this bid (by bidder)"""
        if self.status == 'pending':
            self.status = 'withdrawn'
            self.save()


class BidNotification(TimeStampedModel):
    """Model for tracking bid-related notifications"""
    
    NOTIFICATION_TYPES = [
        ('new_bid', 'New Bid Received'),
        ('bid_accepted', 'Bid Accepted'),
        ('bid_rejected', 'Bid Rejected'),
        ('bid_withdrawn', 'Bid Withdrawn'),
        ('bid_expiring', 'Bid Expiring Soon'),
    ]
    
    id = models.AutoField(primary_key=True)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bid_notifications'
    )
    bid = models.ForeignKey(
        Bid,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'freight_bid_notifications'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type', 'sent_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save(update_fields=['is_read'])


class BidStatistics(TimeStampedModel):
    """Model to track bidding statistics per user"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bid_stats'
    )
    
    # Bidder stats
    total_bids_submitted = models.PositiveIntegerField(default=0)
    bids_accepted = models.PositiveIntegerField(default=0)
    bids_rejected = models.PositiveIntegerField(default=0)
    average_bid_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    
    # Shipper stats
    total_listings_posted = models.PositiveIntegerField(default=0)
    total_bids_received = models.PositiveIntegerField(default=0)
    average_bids_per_listing = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    
    class Meta:
        db_table = 'freight_bid_statistics'
    
    def __str__(self):
        return f"Bid Stats for {self.user.username}"
    
    @property
    def acceptance_rate(self):
        """Calculate bid acceptance rate as percentage"""
        if self.total_bids_submitted > 0:
            return (self.bids_accepted / self.total_bids_submitted) * 100
        return 0