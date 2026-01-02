from django.urls import path
from .views import SessionListView, SessionDetailView

urlpatterns = [
    path('', SessionListView.as_view(), name='session-list'),
    path('<int:pk>/', SessionDetailView.as_view(), name='session-detail'),
]
