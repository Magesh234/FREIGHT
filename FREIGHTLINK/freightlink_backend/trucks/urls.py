# urls.py
from django.urls import path
from . import views
from .views import AvailableTrucksView

app_name = 'trucks'

urlpatterns = [
    # Main truck CRUD operations
    path('', views.TruckListCreateView.as_view(), name='truck-list-create'),
    path('<int:pk>/', views.TruckDetailView.as_view(), name='truck-detail'),
    path('trucks/available/', AvailableTrucksView.as_view(), name='available-trucks'),
    
    # User's trucks
    path('my-trucks/', views.MyTrucksView.as_view(), name='my-trucks'),
    
    # Image management
    path('<int:truck_id>/images/', views.TruckImageUploadView.as_view(), name='truck-image-upload'),
    path('images/<int:pk>/', views.TruckImageDeleteView.as_view(), name='truck-image-delete'),
    
    # Search and filters
    path('search/', views.truck_search, name='truck-search'),
    path('types/', views.truck_types, name='truck-types'),
]