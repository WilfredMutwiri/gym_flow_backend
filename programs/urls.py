from django.urls import path
from .views import (
    ProgramListView, ProgramDetailView, AssignProgramView, 
    WorkoutDayListView, WorkoutSetListView, ExerciseListView
)

urlpatterns = [
    path('', ProgramListView.as_view(), name='program-list'),
    path('<int:pk>/', ProgramDetailView.as_view(), name='program-detail'),
    path('<int:pk>/assign/', AssignProgramView.as_view(), name='program-assign'),
    path('days/', WorkoutDayListView.as_view(), name='workout-day-list'),
    path('sets/', WorkoutSetListView.as_view(), name='workout-set-list'),
    path('exercises/', ExerciseListView.as_view(), name='exercise-list'),
]
