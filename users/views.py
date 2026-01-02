from rest_framework import viewsets, status, views, serializers
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model, authenticate
from .serializers import UserSerializer
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView,APIView
from drf_yasg.utils import swagger_auto_schema
from shared.responses import (
    handle_success,
    handle_error,
    handle_validation_error,
    handle_not_found,
)

User = get_user_model()
from gym.models import Notification

from .serializers import UserSerializer, RegisterSerializer, AdminRegisterSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from gym.permissions import IsAdminOrTrainer
from rest_framework import generics

class UserViewSet(APIView):
    @swagger_auto_schema(
        tags=['Users'],
        operation_summary='Get all users',
        responses={
            200: 'Users retrieved successfully',
            401: 'Unauthorized',
            403: 'Forbidden',
        }
    )  
    def get(self, request):
        queryset = self.get_queryset()
        serializer = UserSerializer(queryset, many=True)
        return handle_success(data=serializer.data, message="Users retrieved successfully", status_code=status.HTTP_200_OK)
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        elif user.role == 'trainer':
            return User.objects.filter(role__in=['member', 'trainer']) 
        return User.objects.filter(id=user.id) 

class RegisterView(APIView):
    
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Users'],
        operation_summary='Register a new user',
        request_body=RegisterSerializer,
        responses={
            201: 'User registered successfully',
            400: 'Bad request',
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            
            # Notify all admins about new registration
            admins = User.objects.filter(role='admin')
            for admin in admins:
                Notification.objects.create(
                    recipient=admin,
                    title="New Member Registration",
                    message=f"A new member has signed up: {user.get_full_name()} ({user.email})."
                )

            return  handle_success(
                data={
                    'token': token.key,
                    'user': UserSerializer(user).data
                },
                message='User registered successfully',
                status_code=status.HTTP_201_CREATED
            )
        return handle_error(
            errors=serializer.errors,
            message='User registration failed',
            status_code=status.HTTP_400_BAD_REQUEST
        )

class AdminRegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Users'],
        operation_summary='Register a new admin',
        request_body=AdminRegisterSerializer,
        responses={
            201: 'Admin registered successfully',
            400: 'Bad request',
        }
    )
    def post(self, request):
        serializer = AdminRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return  handle_success(
                data={
                    'token': token.key,
                    'user': UserSerializer(user).data
                },
                message='Admin registered successfully',
                status_code=status.HTTP_201_CREATED
            )
        return handle_error(
            errors=serializer.errors,
            message='Admin registration failed',
            status_code=status.HTTP_400_BAD_REQUEST
        )
 

class LoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return handle_error(
                message='Please provide both email and password',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(email=email, password=password)
        
        if not user:
            return handle_error(
                message='Invalid credentials',
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        if user.role == 'admin':
             return handle_error(
                message='Admins must use the admin login portal.',
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        token, _ = Token.objects.get_or_create(user=user)
        
        response_data = {
            'token': token.key,
            'user': UserSerializer(user).data
        }

        if hasattr(user, 'member_profile'):
            response_data['member_id'] = user.member_profile.id
        if hasattr(user, 'trainer_profile'):
            response_data['trainer_id'] = user.trainer_profile.id

        return  handle_success(
            data=response_data,
            message='Login successful',
            status_code=status.HTTP_200_OK
        )

class AdminLoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return  handle_error(
                message='Please provide both email and password',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(email=email, password=password)
        
        if not user:
            return handle_error(
                message='Invalid credentials.',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            
        if user.role != 'admin':
            return handle_error(
                message='Unauthorized access. Admin role required.',
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        token, _ = Token.objects.get_or_create(user=user)
        
        return  handle_success(
            data={
                'token': token.key,
                'user': UserSerializer(user).data
            },
            message='Login successful',
            status_code=status.HTTP_200_OK
        )

class ChangePasswordView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Users'],
        operation_summary='Change user password',
        request_body=serializers.Serializer, # Simplified for now
    )
    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not user.check_password(current_password):
            return handle_error(message="Incorrect current password", status_code=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return handle_error(message="New passwords do not match", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            user.set_password(new_password)
            user.save()
            return handle_success(message="Password updated successfully")
        except Exception as e:
            return handle_error(message=f"Failed to update password: {str(e)}")
