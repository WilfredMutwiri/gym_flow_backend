from django.urls import path
from users.views import LoginView, RegisterView, AdminLoginView, AdminRegisterView, UserViewSet, ChangePasswordView
 
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('admin-register/', AdminRegisterView.as_view(), name='admin-register'),
    path('admin-login/', AdminLoginView.as_view(), name='admin-login'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('', UserViewSet.as_view(), name='user-list'),
]
