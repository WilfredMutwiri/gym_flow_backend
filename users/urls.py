from django.urls import path
from users.views import LoginView, RegisterView, AdminLoginView, UserViewSet
 
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('admin-login/', AdminLoginView.as_view(), name='admin-login'),
    path('', UserViewSet.as_view(), name='user-list'),
]
