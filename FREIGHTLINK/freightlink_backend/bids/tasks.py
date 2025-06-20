from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
import logging

from .models import Bid, BidNotification, BidStatistics

logger = logging.getLogger(__name__)


@shared_task
def send_bid_notification_email(notification_id):
    """
    Send email notification for bid-related events
    """
    try:
        notification = BidNotification.objects.select_related(
            'recipient', 'bid__cargo_listing'
        ).get(id=notification_id)
        
        subject_map = {
            'new_bid': f'New Bid Received - {notification.bid.cargo_listing.title}',
            'bid_accepted': f'Your Bid Was Accepted - {notification.bid.cargo_listing.title}',
            'bid_rejected': f'Your Bid Was Rejected - {notification.bid.cargo_listing.title}',
        }
        
        subject = subject_map.get(notification.notification_type, 'Freight App Notification')
        
        message = f"""
        Dear {notification.recipient.first_name or notification.recipient.username},
        
        {notification.message}
        
        Listing: {notification.bid.cargo_listing.title}
        Bid Amount: KSh {notification.bid.bid_amount:,.2f}
        
        Please log in to your account to view more details.
        
        Best regards,
        Freight App Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            fail_silently=False
        )
        
        logger.info(f"Email sent for notification {notification_id}")
        return f"Email sent successfully to {notification.recipient.email}"
        
    except BidNotification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return f"Notification {notification_id} not found"
    except Exception as e:
        logger.error(f"Failed to send email for notification {notification_id}: {str(e)}")
        return f"Failed to send email: {str(e)}"


@shared_task
def cleanup_expired_bids():
    """
    Mark expired bids as inactive and update their status
    """
    try:
        now = timezone.now()
        expired_bids = Bid.objects.filter(
            expires_at__lt=now,
            status='pending',
            is_active=True
        )
        
        expired_count = expired_bids.count()
        
        # Update expired bids
        expired_bids.update(
            is_active=False,
            status='expired',
            responded_at=now
        )
        
        logger.info(f"Marked {expired_count} bids as expired")
        return f"Processed {expired_count} expired bids"
        
    except Exception as e:
        logger.error(f"Error cleaning up expired bids: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def update_bid_statistics():
    """
    Update bid statistics for all users
    """
    try:
        from django.contrib.auth import get_user_model
        from django.db.models import Count, Avg
        
        User = get_user_model()
        updated_count = 0
        
        for user in User.objects.all():
            # Get or create statistics object
            stats, created = BidStatistics.objects.get_or_create(user=user)
            
            # Calculate bidder statistics
            bid_stats = Bid.objects.filter(bidder=user, is_active=True).aggregate(
                total_bids=Count('id'),
                accepted_bids=Count('id', filter=Q(status='accepted')),
                rejected_bids=Count('id', filter=Q(status='rejected')),
                avg_bid_amount=Avg('bid_amount')
            )
            
            # Calculate shipper statistics
            listing_stats = user.CargoListing_set.aggregate(
                total_listings=Count('id'),
                total_bids_received=Count('bids', filter=Q(bids__is_active=True))
            )
            
            avg_bids_per_listing = 0
            if listing_stats['total_listings'] > 0:
                avg_bids_per_listing = listing_stats['total_bids_received'] / listing_stats['total_listings']
            
            # Update statistics
            stats.total_bids_submitted = bid_stats['total_bids'] or 0
            stats.bids_accepted = bid_stats['accepted_bids'] or 0
            stats.bids_rejected = bid_stats['rejected_bids'] or 0
            stats.average_bid_amount = bid_stats['avg_bid_amount'] or 0
            stats.total_listings_posted = listing_stats['total_listings'] or 0
            stats.total_bids_received = listing_stats['total_bids_received'] or 0
            stats.average_bids_per_listing = avg_bids_per_listing
            
            stats.save()
            updated_count += 1
        
        logger.info(f"Updated statistics for {updated_count} users")
        return f"Updated statistics for {updated_count} users"
        
    except Exception as e:
        logger.error(f"Error updating bid statistics: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def send_bid_reminder_emails():
    """
    Send reminder emails for bids expiring within 24 hours
    """
    try:
        from datetime import timedelta
        
        now = timezone.now()
        tomorrow = now + timedelta(days=1)
        
        # Find bids expiring within 24 hours
        expiring_bids = Bid.objects.select_related(
            'bidder', 'cargo_listing__shipper'
        ).filter(
            expires_at__gte=now,
            expires_at__lte=tomorrow,
            status='pending',
            is_active=True
        )
        
        sent_count = 0
        
        for bid in expiring_bids:
            try:
                # Send reminder to shipper
                subject = f'Bid Expiring Soon - {bid.cargo_listing.title}'
                message = f"""
                Dear {bid.cargo_listing.shipper.first_name or bid.cargo_listing.shipper.username},
                
                A bid on your freight listing "{bid.cargo_listing.title}" is expiring soon.
                
                Bid Details:
                - Amount: KSh {bid.bid_amount:,.2f}
                - Bidder: {bid.bidder.username}
                - Expires at: {bid.expires_at.strftime('%Y-%m-%d %H:%M UTC')}
                
                Please log in to accept or reject this bid before it expires.
                
                Best regards,
                Freight App Team
                """
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[bid.cargo_listing.shipper.email],
                    fail_silently=True
                )
                
                sent_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send reminder email for bid {bid.id}: {str(e)}")
                continue
        
        logger.info(f"Sent {sent_count} bid reminder emails")
        return f"Sent {sent_count} reminder emails"
        
    except Exception as e:
        logger.error(f"Error sending bid reminder emails: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def cleanup_old_notifications():
    """
    Delete old read notifications (older than 30 days)
    """
    try:
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=30)
        
        old_notifications = BidNotification.objects.filter(
            is_read=True,
            sent_at__lt=cutoff_date
        )
        
        deleted_count = old_notifications.count()
        old_notifications.delete()
        
        logger.info(f"Deleted {deleted_count} old notifications")
        return f"Deleted {deleted_count} old notifications"
        
    except Exception as e:
        logger.error(f"Error cleaning up old notifications: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def generate_daily_report():
    """
    Generate daily activity report
    """
    try:
        from datetime import timedelta
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        yesterday = timezone.now() - timedelta(days=1)
        today = timezone.now()
        
        # Calculate daily statistics
        new_listings = Bid.objects.filter(
            cargo_listing__created_at__gte=yesterday,
            cargo_listing__created_at__lt=today
        ).count()
        
        new_bids = Bid.objects.filter(
            submitted_at__gte=yesterday,
            submitted_at__lt=today
        ).count()
        
        accepted_bids = Bid.objects.filter(
            responded_at__gte=yesterday,
            responded_at__lt=today,
            status='accepted'
        ).count()
        
        new_users = User.objects.filter(
            date_joined__gte=yesterday,
            date_joined__lt=today
        ).count()
        
        report = f"""
        Daily Activity Report - {yesterday.strftime('%Y-%m-%d')}
        
        New Freight Listings: {new_listings}
        New Bids Submitted: {new_bids}
        Bids Accepted: {accepted_bids}
        New User Registrations: {new_users}
        
        Generated at: {timezone.now().strftime('%Y-%m-%d %H:%M UTC')}
        """
        
        # Send report to administrators
        admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
        
        if admin_emails:
            send_mail(
                subject=f'Daily Activity Report - {yesterday.strftime("%Y-%m-%d")}',
                message=report,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(admin_emails),
                fail_silently=True
            )
        
        logger.info("Daily report generated and sent")
        return "Daily report generated successfully"
        
    except Exception as e:
        logger.error(f"Error generating daily report: {str(e)}")
        return f"Error: {str(e)}"