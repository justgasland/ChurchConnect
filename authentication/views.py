from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    UpdateProfileSerializer
)


class RegisterView(generics.CreateAPIView):
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Handle user registration"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Prepare response data
        user_data = UserSerializer(user).data
        
        return Response({
            'success': True,
            'message': 'Registration successful! Welcome to ChurchConnect.',
            'data': {
                'user': user_data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    API endpoint for user login
    POST /api/auth/login/
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    
    def post(self, request):
        """Handle user login"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Prepare response data
        user_data = UserSerializer(user).data
        
        return Response({
            'success': True,
            'message': 'Login successful!',
            'data': {
                'user': user_data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    API endpoint for user logout
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle user logout"""
        try:
            # Get refresh token from request
            refresh_token = request.data.get('refresh_token')
            
            if refresh_token:
                # Blacklist the refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Logout user from Django session
            logout(request)
            
            return Response({
                'success': True,
                'message': 'Logout successful!'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': 'An error occurred during logout.',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to get and update user profile
    GET /api/auth/profile/
    PUT/PATCH /api/auth/profile/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateProfileSerializer
    
    def get_object(self):
        """Return the current authenticated user"""
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        """Get current user profile"""
        user = self.get_object()
        serializer = UserSerializer(user)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Update user profile"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return updated user data
        user_serializer = UserSerializer(instance)
        
        return Response({
            'success': True,
            'message': 'Profile updated successfully!',
            'data': user_serializer.data
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    API endpoint to change user password
    POST /api/auth/change-password/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def post(self, request):
        """Handle password change"""
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Password changed successfully!'
        }, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    """
    API endpoint to list all users (Admin only)
    GET /api/auth/users/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter users based on role"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Super admin can see all users
        if user.is_super_admin():
            return queryset
        
        # Denomination admin sees users in their denomination
        # if user.is_denomination_admin() and user.denomination:
        #     return queryset.filter(denomination=user.denomination)
        
        # Church admin sees users in their church
        # if user.is_church_admin() and user.church_branch:
        #     return queryset.filter(church_branch=user.church_branch)
        
        # Regular members only see themselves
        return queryset.filter(id=user.id)
    
    def list(self, request, *args, **kwargs):
        """List users with custom response"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class UserDetailView(generics.RetrieveAPIView):
    """
    API endpoint to get a specific user's details
    GET /api/auth/users/<id>/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def retrieve(self, request, *args, **kwargs):
        """Get user details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    


    