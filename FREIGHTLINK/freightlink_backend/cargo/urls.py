from django.urls import path, include
from rest_framework.routers import DefaultRouter
# REMOVE this import - it's causing the conflict
# from rest_framework.urlpatterns import format_suffix_patterns
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'cargo-types', views.CargoTypeViewSet, basename='cargotype')
router.register(r'cargo-listings', views.CargoListingViewSet, basename='cargolisting')
router.register(r'cargo-photos', views.CargoPhotoViewSet, basename='cargophoto')

# URL patterns
urlpatterns = [
    # Include router URLs - DefaultRouter already handles format suffixes
    path('api/', include(router.urls)),
    
    # API documentation (if using DRF browsable API)
    path('api-auth/', include('rest_framework.urls')),
]

# REMOVE this line - DefaultRouter already provides format suffix support
# urlpatterns = format_suffix_patterns(urlpatterns)

# The router creates the following endpoints:
"""
Cargo Types:
- GET /api/cargo-types/ - List all cargo types
- GET /api/cargo-types.json - Same as above but with JSON format
- POST /api/cargo-types/ - Create new cargo type (staff only)
- GET /api/cargo-types/{id}/ - Retrieve specific cargo type
- PUT/PATCH /api/cargo-types/{id}/ - Update cargo type (staff only)
- DELETE /api/cargo-types/{id}/ - Delete cargo type (staff only)

Cargo Listings:
- GET /api/cargo-listings/ - List cargo listings (with filtering)
- GET /api/cargo-listings.json - Same as above but with JSON format
- POST /api/cargo-listings/ - Create new cargo listing
- GET /api/cargo-listings/{id}/ - Retrieve specific cargo listing
- PUT/PATCH /api/cargo-listings/{id}/ - Update cargo listing (owner only)
- DELETE /api/cargo-listings/{id}/ - Delete cargo listing (owner only)
- POST /api/cargo-listings/{id}/update_status/ - Update listing status
- GET /api/cargo-listings/my_listings/ - Get current user's listings
- GET /api/cargo-listings/statistics/ - Get cargo statistics
- POST /api/cargo-listings/{id}/upload_photo/ - Upload photo to listing
- DELETE /api/cargo-listings/{id}/photos/{photo_id}/ - Delete photo from listing

Cargo Photos:
- GET /api/cargo-photos/ - List cargo photos (filterable by cargo_id)
- POST /api/cargo-photos/ - Upload new photo
- GET /api/cargo-photos/{id}/ - Retrieve specific photo
- PUT/PATCH /api/cargo-photos/{id}/ - Update photo (owner only)
- DELETE /api/cargo-photos/{id}/ - Delete photo (owner only)

Format Support:
The DefaultRouter automatically provides format suffix support:
- /api/cargo-types/ - Default format (usually JSON)
- /api/cargo-types.json - Explicit JSON format
- /api/cargo-types.api - Browsable API format

Filtering Examples:
- /api/cargo-listings/?status=OPEN - Filter by status
- /api/cargo-listings/?cargo_type=general&status_in=OPEN,IN_PROGRESS - Multiple filters
- /api/cargo-listings/?budget_min=1000&budget_max=5000 - Budget range
- /api/cargo-listings/?pickup_location__icontains=nairobi - Location search
- /api/cargo-listings/?urgent=true - Urgent deliveries only
- /api/cargo-listings/?has_photos=true - Only listings with photos
- /api/cargo-listings/?pickup_date_after=2025-06-01 - Date filtering
- /api/cargo-listings/?search=electronics nairobi - Text search
- /api/cargo-listings/?ordering=-created_at,budget - Ordering
- /api/cargo-listings/?my_listings=true - User's own listings
"""