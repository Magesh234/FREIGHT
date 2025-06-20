from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the error
        view = context.get('view', None)
        request = context.get('request', None)
        
        error_info = {
            'view': view.__class__.__name__ if view else 'Unknown',
            'method': request.method if request else 'Unknown',
            'path': request.path if request else 'Unknown',
            'user': str(request.user) if request and request.user else 'Anonymous',
            'exception': str(exc),
            'status_code': response.status_code
        }
        
        if response.status_code >= 500:
            logger.error(f"Server Error: {error_info}")
        elif response.status_code >= 400:
            logger.warning(f"Client Error: {error_info}")
        
        # Customize the response format
        custom_response_data = {
            'error': True,
            'status_code': response.status_code,
            'message': get_error_message(exc, response),
            'details': response.data if isinstance(response.data, dict) else {'detail': response.data}
        }
        
        response.data = custom_response_data
    
    return response


def get_error_message(exc, response):
    """
    Get a user-friendly error message based on the exception type
    """
    if isinstance(exc, Http404):
        return "The requested resource was not found."
    
    if isinstance(exc, PermissionDenied):
        return "You don't have permission to perform this action."
    
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        return "The request data is invalid. Please check your input and try again."
    
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        return "Authentication credentials were not provided or are invalid."
    
    if response.status_code == status.HTTP_403_FORBIDDEN:
        return "You don't have permission to access this resource."
    
    if response.status_code == status.HTTP_404_NOT_FOUND:
        return "The requested resource was not found."
    
    if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return "This HTTP method is not allowed for this endpoint."
    
    if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return "Too many requests. Please slow down and try again later."
    
    if response.status_code >= 500:
        return "An internal server error occurred. Please try again later."
    
    # Default message
    return "An error occurred while processing your request."


class FreightAPIException(Exception):
    """
    Custom exception for freight-specific errors
    """
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST, details=None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class BidExpiredException(FreightAPIException):
    """
    Exception raised when trying to operate on an expired bid
    """
    def __init__(self, message="This bid has expired and cannot be modified."):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class ListingInactiveException(FreightAPIException):
    """
    Exception raised when trying to bid on an inactive listing
    """
    def __init__(self, message="This freight listing is no longer active."):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class DuplicateBidException(FreightAPIException):
    """
    Exception raised when a user tries to bid twice on the same listing
    """
    def __init__(self, message="You have already submitted a bid for this listing."):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class SelfBidException(FreightAPIException):
    """
    Exception raised when a user tries to bid on their own listing
    """
    def __init__(self, message="You cannot bid on your own freight listing."):
        super().__init__(message, status.HTTP_403_FORBIDDEN)