from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from collections import defaultdict
from datetime import datetime
from django.db.models import Count, Sum, F
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@ensure_csrf_cookie
def get_user_profile(request):

    user = request.user

    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
    }), status.HTTP_200_OK

@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_csrf_token(request):
    """
    Get CSRF token for frontend JavaScript usage
    """
    return JsonResponse({
        'csrfToken': get_token(request),
        'status': 'success'
    })




class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user

        total_cargo_listings = CargoListing.objects.filter(owner=user).count()
        active_cargo_listings = CargoListing.objects.filter(owner=user, status='active').count()
        completed_orders_as_customer = Order.objects.filter(customer=user, status='completed').count()
        completed_orders_as_driver = Order.objects.filter(driver=user, status='completed').count()

        # Assuming 'earnings' come from completed orders where the user is the driver
        # And 'spending' comes from completed orders where the user is the customer
        total_earnings = Order.objects.filter(driver=user, status='completed').aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_spending = Order.objects.filter(customer=user, status='completed').aggregate(Sum('total_price'))['total_price__sum'] or 0

        # For recent activity, you might combine different models based on their timestamps
        recent_orders = Order.objects.filter(Q(customer=user) | Q(driver=user)).order_by('-order_date')[:5]
        recent_payments = Payment.objects.filter(user=user).order_by('-payment_date')[:5]

        # Example of how you might structure recent activity for history.html
        history_data = []
        for order in recent_orders:
            history_data.append({
                'id': f"ORDER-{order.id}",
                'type': 'Order Update',
                'description': f"Order #{order.id} status changed to {order.status}",
                'date': order.order_date.strftime('%Y-%m-%d %H:%M'),
                'status': order.status.capitalize(), # For frontend styling
            })
        for payment in recent_payments:
            history_data.append({
                'id': f"PAY-{payment.id}",
                'type': 'Payment',
                'description': f"Payment of {payment.amount} {payment.currency} ({payment.status})",
                'date': payment.payment_date.strftime('%Y-%m-%d %H:%M'),
                'status': payment.status.capitalize(),
            })
        # Sort history data by date, most recent first
        history_data.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d %H:%M'), reverse=True)


        data = {
            'totalCargoListings': total_cargo_listings,
            'activeCargoListings': active_cargo_listings,
            'completedOrdersAsCustomer': completed_orders_as_customer,
            'completedOrdersAsDriver': completed_orders_as_driver,
            'totalEarnings': total_earnings,
            'totalSpending': total_spending,
            'recentActivity': history_data, # Directly provide history data for frontend
            'truckBookings': TruckListing.objects.filter(owner=user).count(), # Example
        }
        return Response(data)

class HistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        history_items = []

        # Fetch relevant orders
        orders = Order.objects.filter(Q(customer=user) | Q(driver=user)).order_by('-order_date')
        for order in orders:
            history_items.append({
                'id': f"ORDER-{order.id}",
                'type': 'Order',
                'description': f"Order #{order.id} for {order.cargo_listing.title if order.cargo_listing else 'N/A'} was {order.status}",
                'date': order.order_date.isoformat(),
                'status': order.get_status_display(),
            })

        # Fetch relevant payments
        payments = Payment.objects.filter(user=user).order_by('-payment_date')
        for payment in payments:
            history_items.append({
                'id': f"PAY-{payment.id}",
                'type': 'Payment',
                'description': f"Payment of {payment.amount} {payment.currency} for {payment.order.id if payment.order else 'N/A'} - {payment.status}",
                'date': payment.payment_date.isoformat(),
                'status': payment.get_status_display(),
            })

        # Fetch profile updates (if you track them explicitly, or infer from UserProfile last_updated)
        # For simplicity, let's add a dummy entry if profile was recently updated
        profile = user.profile
        if profile.updated_at and (datetime.now().date() - profile.updated_at.date()).days < 30: # If updated in last 30 days
             history_items.append({
                'id': f"PROFILE-{user.id}",
                'type': 'Profile Update',
                'description': 'Your profile information was updated.',
                'date': profile.updated_at.isoformat(),
                'status': 'Info',
            })

        # Sort all history items by date
        history_items.sort(key=lambda x: x['date'], reverse=True)

        return Response(history_items)