from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from users.views import UserViewSet
from gym.views import (
    TrainerViewSet, MemberViewSet, AttendanceRecordViewSet, 
    ProgramViewSet, WorkoutDayViewSet, ExerciseViewSet, 
    WorkoutSetViewSet, SubscriptionPlanViewSet, 
    MemberSubscriptionViewSet, PaymentViewSet, 
    ProgressEntryViewSet, MessageViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'trainers', TrainerViewSet)
router.register(r'members', MemberViewSet)
router.register(r'attendance', AttendanceRecordViewSet)
router.register(r'programs', ProgramViewSet)
router.register(r'workout-days', WorkoutDayViewSet)
router.register(r'exercises', ExerciseViewSet)
router.register(r'workout-sets', WorkoutSetViewSet)
router.register(r'plans', SubscriptionPlanViewSet)
router.register(r'subscriptions', MemberSubscriptionViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'progress', ProgressEntryViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    
    # Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
