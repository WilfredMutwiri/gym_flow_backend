from django.urls import path
from .views import WorkoutSetListView

urlpatterns = [
    path('', WorkoutSetListView.as_view(), name='workout-set-list'),
]
