# bookings/urls.py
from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Main booking endpoints
    path('', views.BookingListCreateView.as_view(), name='booking-list-create'),
    path('<int:pk>/', views.BookingDetailView.as_view(), name='booking-detail'),
    
    # User-specific booking views
    path('my-bookings/', views.MyBookingsView.as_view(), name='my-bookings'),
    path('truck-bookings/', views.TruckBookingsView.as_view(), name='truck-bookings'),
    
    # Booking status updates
    path('<int:booking_id>/status-update/', views.BookingStatusUpdateView.as_view(), name='booking-status-update'),
    
    # Document uploads
    path('<int:booking_id>/documents/', views.BookingDocumentUploadView.as_view(), name='booking-document-upload'),
    
    # Utility endpoints
    path('available-trucks/', views.available_trucks, name='available-trucks'),
    path('statistics/', views.booking_statistics, name='booking-statistics'),
]