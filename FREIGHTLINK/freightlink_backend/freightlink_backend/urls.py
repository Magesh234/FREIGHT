from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.routers import DefaultRouter
from accounts.views import UserProfileDetailUpdateView, ProfilePictureUploadView
from messaging.views import ConversationViewSet
from support.views import FAQListView, ArticleListView, ServiceListView
from .views import DashboardSummaryView, HistoryView
from django.http import JsonResponse

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'csrfToken': request.META.get('CSRF_COOKIE')})


router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/csrf/', get_csrf_token, name='csrf'),
    path('api/', include(router.urls)),
    
    path('', include('cargo.urls')),
    path('api/trucks/', include('trucks.urls')),
    path('api/bids/', include('bids.urls')),
    path('api/bookings/', include('bookings.urls')),
    
    
    # Disable CSRF for auth endpoints - Apply csrf_exempt to Djoser URLs
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),

    # Custom Profile endpoints
    path('api/profile/', UserProfileDetailUpdateView.as_view(), name='user-profile'),
    path('api/profile/picture/upload/', ProfilePictureUploadView.as_view(), name='profile-picture-upload'),

    

    # Support endpoints
    path('api/faqs/', FAQListView.as_view(), name='faq-list'),
    path('api/articles/', ArticleListView.as_view(), name='article-list'),
    path('api/services/', ServiceListView.as_view(), name='service-list'),

    # Dashboard and History
    path('api/dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('api/history/', HistoryView.as_view(), name='user-history'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)