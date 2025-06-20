from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class BidCreationThrottle(UserRateThrottle):
    """
    Throttle for bid creation to prevent spam bidding.
    Allows 10 bids per hour per user.
    """
    scope = 'bid_creation'
    rate = '10/hour'


class ListingCreationThrottle(UserRateThrottle):
    """
    Throttle for freight listing creation.
    Allows 5 listings per hour per user.
    """
    scope = 'listing_creation'
    rate = '5/hour'


class NotificationThrottle(UserRateThrottle):
    """
    Throttle for notification operations.
    Allows 60 requests per minute per user.
    """
    scope = 'notifications'
    rate = '60/min'


class GeneralUserThrottle(UserRateThrottle):
    """
    General throttle for authenticated users.
    Allows 1000 requests per hour per user.
    """
    scope = 'user'
    rate = '1000/hour'


class GeneralAnonThrottle(AnonRateThrottle):
    """
    General throttle for anonymous users.
    Allows 100 requests per hour per IP.
    """
    scope = 'anon'
    rate = '100/hour'