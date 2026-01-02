from django.urls import path
from .views import ExerciseListView

urlpatterns = [
    path('', ExerciseListView.as_view(), name='exercise-list'),
]
