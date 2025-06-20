from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'bids'

# URL patterns for the freight bidding system
urlpatterns = [
    # Freight Listings
    path('listings/', views.CargoListingListCreateView.as_view(), name='listing-list-create'),
    path('listings/<uuid:pk>/', views.CargoListingDetailView.as_view(), name='listing-detail'),
    path('listings/my/', views.MyCargoListingsView.as_view(), name='my-listings'),
    path('listings/<uuid:listing_id>/bids/', views.ListingBidsView.as_view(), name='listing-bids'),
    
    # Bids
    path('bids/', views.BidListCreateView.as_view(), name='bid-list-create'),
    path('bids/<uuid:pk>/', views.BidDetailView.as_view(), name='bid-detail'),
    path('bids/my/', views.MyBidsView.as_view(), name='my-bids'),
    path('bids/<uuid:bid_id>/respond/', views.respond_to_bid, name='respond-to-bid'),
    
    # Notifications  
    path('notifications/', views.BidNotificationListView.as_view(), name='notification-list'),
    path('notifications/<uuid:notification_id>/read/', views.mark_notification_read, name='mark-notification-read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark-all-notifications-read'),
    
    # Statistics and Dashboard
    path('statistics/', views.BidStatisticsView.as_view(), name='bid-statistics'),
    path('dashboard/', views.dashboard_summary, name='dashboard-summary'),
]