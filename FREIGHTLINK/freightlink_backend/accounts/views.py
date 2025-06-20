from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.middleware.csrf import get_token
from .models import User, UserProfile
from .serializers import UserProfileSerializer, UserSerializer, UserCreateSerializer
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

# CSRF token endpoint
@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Endpoint to get CSRF token for frontend
    """
    return JsonResponse({'csrfToken': get_token(request)})

@method_decorator(csrf_exempt, name='dispatch')
class SignupView(APIView):
    permission_classes = [permissions.AllowAny]  # Allow unauthenticated users to register

    def post(self, request):
        # Use UserCreateSerializer for user registration
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Return success response with user data
            user_serializer = UserSerializer(user)
            return Response({
                "message": "User created successfully! Please check your email for verification.",
                "user": user_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                "detail": "Email and password are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Try to get user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                "detail": "Invalid credentials."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate using username (since Django's default auth uses username)
        user = authenticate(request, username=user.username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                user_serializer = UserSerializer(user)
                return Response({
                    "message": "Login successful!",
                    "user": user_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "detail": "Account is disabled."
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                "detail": "Invalid credentials."
            }, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from django.contrib.auth import logout
        logout(request)
        return Response({
            "message": "Logged out successfully."
        }, status=status.HTTP_200_OK)

class UserProfileDetailUpdateView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Get or create profile for the current user
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get current authenticated user's data"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class ProfilePictureUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        # Get or create user profile
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile_picture = request.FILES.get('profile_picture')

        if not profile_picture:
            return Response({
                "detail": "No profile picture provided."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate file type (optional)
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if profile_picture.content_type not in allowed_types:
            return Response({
                "detail": "Invalid file type. Please upload a JPEG, PNG, GIF, or WebP image."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size (optional, e.g., 5MB limit)
        max_size = 5 * 1024 * 1024  # 5MB
        if profile_picture.size > max_size:
            return Response({
                "detail": "File too large. Please upload an image smaller than 5MB."
            }, status=status.HTTP_400_BAD_REQUEST)

        user_profile.profile_picture = profile_picture
        user_profile.save()

        serializer = UserProfileSerializer(user_profile)
        return Response({
            "message": "Profile picture updated successfully.",
            "profile": serializer.data
        }, status=status.HTTP_200_OK)

# Alternative class-based view with CSRF handling
@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFTokenView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return Response({'csrfToken': get_token(request)})

# Services view (if you need this for your frontend)
class ServicesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Mock services data - replace with your actual services model
        services = [
            {
                "id": 1,
                "title": "Web Development",
                "description": "Custom web applications and websites",
                "icon_class": "bi bi-code-slash",
                "features": ["Responsive Design", "Modern Technologies", "SEO Optimized"]
            },
            {
                "id": 2,
                "title": "Mobile Development",
                "description": "iOS and Android applications",
                "icon_class": "bi bi-phone",
                "features": ["Cross Platform", "Native Performance", "App Store Ready"]
            },
            {
                "id": 3,
                "title": "Consulting",
                "description": "Technical consulting and architecture",
                "icon_class": "bi bi-lightbulb",
                "features": ["Expert Advice", "Architecture Planning", "Best Practices"]
            }
        ]
        return Response(services, status=status.HTTP_200_OK)