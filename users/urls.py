from django.urls import path
from users.views import LoginView, RegisterView, AdminLoginView, AdminRegisterView, UserViewSet, ChangePasswordView, PasswordResetRequestView, PasswordResetConfirmView
 
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('admin-register/', AdminRegisterView.as_view(), name='admin-register'),
    path('admin-login/', AdminLoginView.as_view(), name='admin-login'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('', UserViewSet.as_view(), name='user-list'),
]
