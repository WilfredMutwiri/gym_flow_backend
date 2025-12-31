from rest_framework import viewsets, status, views
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model, authenticate
from .serializers import UserSerializer

User = get_user_model()

from .serializers import UserSerializer, RegisterSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from gym.permissions import IsAdminOrTrainer
from rest_framework import generics

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        elif user.role == 'trainer':
            return User.objects.filter(role__in=['member', 'trainer']) 
        return User.objects.filter(id=user.id) 

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

class LoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({'error': 'Please provide both email and password'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(email=email, password=password)
        
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.role == 'admin':
             return Response({'error': 'Admins must use the admin login portal.'}, status=status.HTTP_403_FORBIDDEN)
            
        token, _ = Token.objects.get_or_create(user=user)
        
        response_data = {
            'token': token.key,
            'user': UserSerializer(user).data
        }

        if hasattr(user, 'member_profile'):
            response_data['member_id'] = user.member_profile.id
        if hasattr(user, 'trainer_profile'):
            response_data['trainer_id'] = user.trainer_profile.id

        return Response(response_data)

class AdminLoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({'error': 'Please provide both email and password'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(email=email, password=password)
        
        if not user or user.role != 'admin':
            # Use generic error for security, or specific if needed. 
            # If user exists but is not admin, authenticate returns the user object.
            # But here `authenticate` will return user if password matches.
            # We check role.
            return Response({'error': 'Invalid credentials or unauthorized access.'}, status=status.HTTP_401_UNAUTHORIZED)
            
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
