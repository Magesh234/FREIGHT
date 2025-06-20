import django_filters
from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from .models import CargoListing, CargoType


class CargoListingFilter(django_filters.FilterSet):
    """
    Comprehensive filter set for CargoListing model
    Provides filtering by various fields with range and lookup options
    """
    
    # Status filters
    status = django_filters.ChoiceFilter(choices=CargoListing.STATUS_CHOICES)
    status_in = django_filters.MultipleChoiceFilter(
        field_name='status', 
        choices=CargoListing.STATUS_CHOICES,
        help_text="Filter by multiple status values"
    )
    
    # Cargo type filters
    cargo_type = django_filters.ChoiceFilter(choices=CargoListing.CARGO_TYPE_CHOICES)
    cargo_type_in = django_filters.MultipleChoiceFilter(
        field_name='cargo_type',
        choices=CargoListing.CARGO_TYPE_CHOICES,
        help_text="Filter by multiple cargo types"
    )
    
    # Location filters
    pickup_location = django_filters.CharFilter(lookup_expr='icontains')
    delivery_location = django_filters.CharFilter(lookup_expr='icontains')
    pickup_location_exact = django_filters.CharFilter(field_name='pickup_location', lookup_expr='iexact')
    delivery_location_exact = django_filters.CharFilter(field_name='delivery_location', lookup_expr='iexact')
    
    # Date filters
    pickup_date = django_filters.DateFilter()
    pickup_date_after = django_filters.DateFilter(field_name='pickup_date', lookup_expr='gte')
    pickup_date_before = django_filters.DateFilter(field_name='pickup_date', lookup_expr='lte')
    pickup_date_range = django_filters.DateFromToRangeFilter(field_name='pickup_date')
    
    delivery_date = django_filters.DateFilter()
    delivery_date_after = django_filters.DateFilter(field_name='delivery_date', lookup_expr='gte')
    delivery_date_before = django_filters.DateFilter(field_name='delivery_date', lookup_expr='lte')
    delivery_date_range = django_filters.DateFromToRangeFilter(field_name='delivery_date')
    
    # Created date filters
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')
    created_range = django_filters.DateFromToRangeFilter(field_name='created_at__date')
    
    # Budget filters
    budget = django_filters.NumberFilter()
    budget_min = django_filters.NumberFilter(field_name='budget', lookup_expr='gte')
    budget_max = django_filters.NumberFilter(field_name='budget', lookup_expr='lte')
    budget_range = django_filters.RangeFilter(field_name='budget')
    
    # Weight filters
    weight = django_filters.NumberFilter()
    weight_min = django_filters.NumberFilter(field_name='weight', lookup_expr='gte')
    weight_max = django_filters.NumberFilter(field_name='weight', lookup_expr='lte')
    weight_range = django_filters.RangeFilter(field_name='weight')
    
    # Volume filters
    volume = django_filters.NumberFilter()
    volume_min = django_filters.NumberFilter(field_name='volume', lookup_expr='gte')
    volume_max = django_filters.NumberFilter(field_name='volume', lookup_expr='lte')
    volume_range = django_filters.RangeFilter(field_name='volume')
    
    # Estimated value filters
    estimated_value_min = django_filters.NumberFilter(field_name='estimated_value', lookup_expr='gte')
    estimated_value_max = django_filters.NumberFilter(field_name='estimated_value', lookup_expr='lte')
    estimated_value_range = django_filters.RangeFilter(field_name='estimated_value')
    
    # Payment method filter
    preferred_payment = django_filters.ChoiceFilter(choices=CargoListing.PAYMENT_CHOICES)
    preferred_payment_in = django_filters.MultipleChoiceFilter(
        field_name='preferred_payment',
        choices=CargoListing.PAYMENT_CHOICES,
        help_text="Filter by multiple payment methods"
    )
    
    # User filters
    posted_by = django_filters.NumberFilter(field_name='posted_by__id')
    posted_by_username = django_filters.CharFilter(field_name='posted_by__username', lookup_expr='icontains')
    
    # Custom filters for common use cases
    urgent = django_filters.BooleanFilter(method='filter_urgent', help_text="Filter urgent deliveries (pickup within 3 days)")
    available_today = django_filters.BooleanFilter(method='filter_available_today', help_text="Filter listings available for pickup today")
    high_value = django_filters.BooleanFilter(method='filter_high_value', help_text="Filter high-value cargo (>100,000)")
    has_photos = django_filters.BooleanFilter(method='filter_has_photos', help_text="Filter listings with photos")
    
    # Route-based filters
    route_contains = django_filters.CharFilter(method='filter_route_contains', help_text="Filter by pickup or delivery location")
    
    class Meta:
        model = CargoListing
        fields = {
            'title': ['exact', 'icontains'],
            'description': ['icontains'],
            'weight': ['exact', 'gte', 'lte'],
            'volume': ['exact', 'gte', 'lte'],
            'budget': ['exact', 'gte', 'lte'],
            'estimated_value': ['exact', 'gte', 'lte'],
            'pickup_date': ['exact', 'gte', 'lte'],
            'delivery_date': ['exact', 'gte', 'lte'],
            'created_at': ['exact', 'gte', 'lte'],
            'updated_at': ['exact', 'gte', 'lte'],
        }
    
    def filter_urgent(self, queryset, name, value):
        """Filter urgent deliveries (pickup within 3 days)"""
        if value:
            urgent_date = timezone.now().date() + timedelta(days=3)
            return queryset.filter(
                pickup_date__lte=urgent_date,
                pickup_date__gte=timezone.now().date(),
                status='OPEN'
            )
        return queryset
    
    def filter_available_today(self, queryset, name, value):
        """Filter listings available for pickup today"""
        if value:
            today = timezone.now().date()
            return queryset.filter(
                pickup_date=today,
                status='OPEN'
            )
        return queryset
    
    def filter_high_value(self, queryset, name, value):
        """Filter high-value cargo (estimated value > 100,000)"""
        if value:
            return queryset.filter(estimated_value__gt=100000)
        elif value is False:
            return queryset.filter(estimated_value__lte=100000)
        return queryset
    
    def filter_has_photos(self, queryset, name, value):
        """Filter listings that have photos"""
        if value:
            return queryset.filter(cargo_photos__isnull=False).distinct()
        elif value is False:
            return queryset.filter(cargo_photos__isnull=True)
        return queryset
    
    def filter_route_contains(self, queryset, name, value):
        """Filter by pickup or delivery location containing the value"""
        if value:
            return queryset.filter(
                models.Q(pickup_location__icontains=value) |
                models.Q(delivery_location__icontains=value)
            )
        return queryset


class CargoTypeFilter(django_filters.FilterSet):
    """
    Filter set for CargoType model
    """
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')
    
    class Meta:
        model = CargoType
        fields = ['name', 'description']


# Custom filter methods that can be used in views
class CargoFilterMixin:
    """
    Mixin that provides common filtering methods for cargo-related views
    """
    
    def filter_by_proximity(self, queryset, location, radius_km=50):
        """
        Filter cargo listings by proximity to a location
        Note: This is a basic implementation. For production use,
        consider using PostGIS or similar for proper geo-spatial queries
        """
        # Basic implementation using string matching
        # In production, you'd want to use actual coordinates and distance calculations
        return queryset.filter(
            models.Q(pickup_location__icontains=location) |
            models.Q(delivery_location__icontains=location)
        )
    
    def filter_by_user_preferences(self, queryset, user):
        """
        Filter cargo listings based on user preferences
        This could be expanded to include user's preferred routes, cargo types, etc.
        """
        # Example implementation - you can expand based on user profile
        if not user.is_authenticated:
            return queryset
        
        # Filter out user's own listings by default
        queryset = queryset.exclude(posted_by=user)
        
        # Add more user-specific filtering logic here
        # For example, preferred cargo types, routes, etc.
        
        return queryset
    
    def filter_by_compatibility(self, queryset, max_weight=None, max_volume=None):
        """
        Filter cargo based on transport compatibility
        """
        filters = models.Q()
        
        if max_weight:
            filters &= models.Q(weight__lte=max_weight)
        
        if max_volume:
            filters &= models.Q(volume__lte=max_volume)
        
        return queryset.filter(filters)
    
    def filter_by_timeline(self, queryset, available_from=None, available_until=None):
        """
        Filter cargo based on availability timeline
        """
        filters = models.Q()
        
        if available_from:
            filters &= models.Q(pickup_date__gte=available_from)
        
        if available_until:
            filters &= models.Q(delivery_date__lte=available_until)
        
        return queryset.filter(filters)


# Predefined filter sets for common use cases
class OpenCargoFilter(CargoListingFilter):
    """Filter for open cargo listings only"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.queryset.filter(status='OPEN')


class UrgentCargoFilter(CargoListingFilter):
    """Filter for urgent cargo (pickup within 7 days)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        urgent_date = timezone.now().date() + timedelta(days=7)
        self.queryset = self.queryset.filter(
            pickup_date__lte=urgent_date,
            pickup_date__gte=timezone.now().date(),
            status='OPEN'
        )


class RecentCargoFilter(CargoListingFilter):
    """Filter for recently posted cargo (within last 7 days)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        recent_date = timezone.now() - timedelta(days=7)
        self.queryset = self.queryset.filter(created_at__gte=recent_date)


# Custom filter backends for advanced filtering
from rest_framework import filters

class CargoSearchFilter(filters.BaseFilterBackend):
    """
    Custom search filter for cargo listings
    Provides more intelligent search across multiple fields
    """
    
    def filter_queryset(self, request, queryset, view):
        search_terms = request.query_params.get('search', '').strip()
        
        if not search_terms:
            return queryset
        
        # Split search terms
        terms = search_terms.split()
        
        # Build search query
        search_query = models.Q()
        
        for term in terms:
            term_query = (
                models.Q(title__icontains=term) |
                models.Q(description__icontains=term) |
                models.Q(pickup_location__icontains=term) |
                models.Q(delivery_location__icontains=term) |
                models.Q(cargo_type__icontains=term) |
                models.Q(additional_requirements__icontains=term)
            )
            search_query &= term_query
        
        return queryset.filter(search_query)


class CargoOrderingFilter(filters.OrderingFilter):
    """
    Custom ordering filter for cargo listings
    Adds intelligent ordering options
    """
    
    def get_valid_fields(self, queryset, view, context={}):
        valid_fields = super().get_valid_fields(queryset, view, context)
        
        # Add custom ordering fields
        custom_fields = [
            ('urgency', 'urgency'),
            ('value_per_weight', 'value_per_weight'),
            ('distance', 'distance'),  # Would require geo calculations
        ]
        
        valid_fields.extend(custom_fields)
        return valid_fields
    
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        
        if ordering:
            # Handle custom ordering
            if 'urgency' in ordering:
                # Order by pickup date (most urgent first)
                queryset = queryset.extra(
                    select={'urgency': 'DATEDIFF(pickup_date, CURDATE())'}
                ).order_by('urgency')
            
            elif 'value_per_weight' in ordering:
                # Order by value per weight ratio
                queryset = queryset.extra(
                    select={'value_per_weight': 'estimated_value / weight'}
                ).order_by('-value_per_weight')
            
            else:
                # Use default ordering
                queryset = queryset.order_by(*ordering)
        
        return queryset


# Filter validation utilities
class FilterValidator:
    """
    Utility class for validating filter parameters
    """
    
    @staticmethod
    def validate_date_range(start_date, end_date):
        """Validate that end_date is after start_date"""
        if start_date and end_date and start_date > end_date:
            raise django_filters.ValidationError("End date must be after start date")
    
    @staticmethod
    def validate_numeric_range(min_val, max_val, field_name):
        """Validate that max value is greater than min value"""
        if min_val is not None and max_val is not None and min_val > max_val:
            raise django_filters.ValidationError(f"Maximum {field_name} must be greater than minimum")
    
    @staticmethod
    def validate_budget_range(budget_min, budget_max):
        """Validate budget range"""
        FilterValidator.validate_numeric_range(budget_min, budget_max, "budget")
        
        if budget_min is not None and budget_min < 0:
            raise django_filters.ValidationError("Minimum budget cannot be negative")
    
    @staticmethod
    def validate_weight_range(weight_min, weight_max):
        """Validate weight range"""
        FilterValidator.validate_numeric_range(weight_min, weight_max, "weight")
        
        if weight_min is not None and weight_min < 0:
            raise django_filters.ValidationError("Minimum weight cannot be negative")