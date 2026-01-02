from django.urls import path
from .views import ProgressEntryListView

urlpatterns = [
    path('', ProgressEntryListView.as_view(), name='progress-list'),
]
