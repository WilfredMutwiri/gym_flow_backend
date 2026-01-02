from django.urls import path
from .views import WorkoutDayListView

urlpatterns = [
    path('', WorkoutDayListView.as_view(), name='workout-day-list'),
]
