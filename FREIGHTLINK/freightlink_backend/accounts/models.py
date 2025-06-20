from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Make email unique and primary login field
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'  # Use email to log in instead of username
    REQUIRED_FIELDS = ['username']       # Remove username from required fields

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('trucking', 'Trucking Company/Owner'),
        ('cargo_owner', 'Cargo Owner'),
        ('individual', 'Individual'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='Kenya')

    company_name = models.CharField(max_length=255, blank=True, null=True)
    business_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES, default='individual')
    business_registration_number = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.email  # Use email here as username might be empty


# Signal to create or update UserProfile when User is created or updated
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
