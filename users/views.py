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
from notifications.models import Notification

from .serializers import UserSerializer, RegisterSerializer, AdminRegisterSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from shared.permissions import IsAdminOrTrainer
from rest_framework import generics
import os

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

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Users'],
        operation_summary='Request password reset',
        request_body=serializers.Serializer,
        responses={
            200: 'Password reset email sent',
            404: 'User not found',
        }
    )
    def post(self, request):
        from django.contrib.auth.tokens import default_token_generator
        from django.core.mail import send_mail
        from django.conf import settings
        
        email = request.data.get('email')
        if not email:
            return handle_validation_error(errors={'email': 'Email is required'})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            return handle_success(message="If an account exists with this email, a password reset link has been sent")

        # Generate token
        token = default_token_generator.make_token(user)
        
        # Frontend URL for password reset
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
        reset_link = f"{frontend_url}/reset-password?token={token}&email={email}"

        # Send email
        subject = "Reset Your FitHub Password"
        message = f"""
Hello {user.get_full_name()},

You requested to reset your password for your FitHub account.

Click the link below to reset your password:
{reset_link}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
The FitHub Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return handle_success(message="If an account exists with this email, a password reset link has been sent")
        except Exception as e:
            return handle_error(message=f"Failed to send email: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Users'],
        operation_summary='Confirm password reset',
        request_body=serializers.Serializer,
        responses={
            200: 'Password reset successful',
            400: 'Invalid or expired token',
        }
    )
    def post(self, request):
        from django.contrib.auth.tokens import default_token_generator
        
        email = request.data.get('email')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not all([email, token, new_password]):
            return handle_validation_error(errors={'fields': 'Email, token, and new password are required'})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return handle_error(message="Invalid reset link", status_code=status.HTTP_400_BAD_REQUEST)

        # Verify token
        if not default_token_generator.check_token(user, token):
            return handle_error(message="Invalid or expired reset link", status_code=status.HTTP_400_BAD_REQUEST)

        # Set new password
        user.set_password(new_password)
        user.save()

        return handle_success(message="Password has been reset successfully. You can now log in with your new password.")

class DebugEmailSettingsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from django.conf import settings
        import socket
        import urllib.request
        
        results = {}
        
        # Test 1: DNS Resolution
        try:
            results['DNS_SMTP'] = str(socket.gethostbyname_ex(settings.EMAIL_HOST))
        except Exception as e:
            results['DNS_SMTP'] = f"Failed: {str(e)}"

        try:
            results['DNS_GOOGLE'] = str(socket.gethostbyname_ex('google.com'))
        except Exception as e:
            results['DNS_GOOGLE'] = f"Failed: {str(e)}"

        # Test 2: HTTP Connectivity (Standard Port 443)
        try:
            with urllib.request.urlopen('https://www.google.com', timeout=5) as response:
                results['HTTP_TEST'] = f"Success (Status {response.status})"
        except Exception as e:
            results['HTTP_TEST'] = f"Failed: {str(e)}"

        # Test 3: Configured SMTP Port
        try:
            sock = socket.create_connection((settings.EMAIL_HOST, settings.EMAIL_PORT), timeout=5)
            results['SMTP_PORT_TEST'] = "Success"
            sock.close()
        except Exception as e:
            results['SMTP_PORT_TEST'] = f"Failed: {str(e)}"

        # Test 4: Force IPv4 SMTP
        try:
            # Get addr info for IPv4
            addr_info = socket.getaddrinfo(settings.EMAIL_HOST, settings.EMAIL_PORT, socket.AF_INET, socket.SOCK_STREAM)
            family, socktype, proto, canonname, sockaddr = addr_info[0]
            sock = socket.socket(family, socktype, proto)
            sock.settimeout(5)
            sock.connect(sockaddr)
            results['SMTP_IPV4_TEST'] = f"Success (Connected to {sockaddr})"
            sock.close()
        except Exception as e:
            results['SMTP_IPV4_TEST'] = f"Failed: {str(e)}"

        # Test 5: SendGrid Port 2525 (Alternative Port Check)
        try:
            sock = socket.create_connection(('smtp.sendgrid.net', 2525), timeout=5)
            results['SENDGRID_PORT_2525_TEST'] = "Success"
            sock.close()
        except Exception as e:
            results['SENDGRID_PORT_2525_TEST'] = f"Failed: {str(e)}"

        return Response({
            "EMAIL_CONFIG": {
                "HOST": settings.EMAIL_HOST,
                "PORT": settings.EMAIL_PORT,
                "USE_TLS": settings.EMAIL_USE_TLS,
                "USE_SSL": getattr(settings, 'EMAIL_USE_SSL', False),
                "USER_SET": bool(settings.EMAIL_HOST_USER),
                "PASSWORD_SET": bool(settings.EMAIL_HOST_PASSWORD),
            },
            "TEST_RESULTS": results,
        })
