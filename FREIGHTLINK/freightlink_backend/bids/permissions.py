from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.shipper == request.user


class IsBidder(permissions.BasePermission):
    """
    Custom permission to only allow bidders to modify their bids.
    """
    def has_object_permission(self, request, view, obj):
        # Allow read access to both bidder and listing owner
        if request.method in permissions.SAFE_METHODS:
            return (obj.bidder == request.user or 
                   obj.cargo_listing.shipper == request.user)
        
        # Write permissions only for the bidder
        return obj.bidder == request.user


class IsShipperOrBidder(permissions.BasePermission):
    """
    Custom permission to allow access to bids for both shipper and bidder.
    """
    def has_object_permission(self, request, view, obj):
        return (obj.bidder == request.user or 
                obj.cargo_listing.shipper == request.user)


class IsNotificationRecipient(permissions.BasePermission):
    """
    Custom permission to only allow notification recipients to access their notifications.
    """
    def has_object_permission(self, request, view, obj):
        return obj.recipient == request.user


class CannotBidOnOwnListing(permissions.BasePermission):
    """
    Custom permission to prevent users from bidding on their own freight listings.
    """
    def has_permission(self, request, view):
        if request.method == 'POST' and 'cargo_listing_id' in request.data:
            from .models import CargoListing
            try:
                listing = CargoListing.objects.get(
                    id=request.data['cargo_listing_id']
                )
                return listing.shipper != request.user
            except CargoListing.DoesNotExist:
                return True  # Let the serializer handle this validation
        return True