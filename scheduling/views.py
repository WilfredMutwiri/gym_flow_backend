from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Session
from .serializers import SessionSerializer
from core.models import Member, Trainer
from attendance.models import AttendanceRecord
from rest_framework.permissions import IsAuthenticated
from shared.responses import (
    handle_success,
    handle_error,
    handle_validation_error,
    handle_not_found,
)

class SessionListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Sessions'],
        operation_summary='List sessions',
        manual_parameters=[
            openapi.Parameter('trainer_id', openapi.IN_QUERY, description="Filter by trainer ID", type=openapi.TYPE_INTEGER),
        ],
        responses={200: SessionSerializer(many=True)}
    )
    def get(self, request):
        user = request.user
        queryset = Session.objects.select_related('member__user', 'trainer__user').all()
        
        if user.role == 'member':
            queryset = queryset.filter(member__user=user)
        elif user.role == 'trainer':
            queryset = queryset.filter(trainer__user=user)
            
        trainer_id = request.query_params.get('trainer_id')
        if trainer_id:
            queryset = queryset.filter(trainer_id=trainer_id)
            
        serializer = SessionSerializer(queryset, many=True)
        return handle_success(data=serializer.data, message="Sessions retrieved successfully")

    @swagger_auto_schema(
        tags=['Sessions'],
        operation_summary='Book a session',
        request_body=SessionSerializer,
        responses={201: SessionSerializer()}
    )
    def post(self, request):
        data = request.data.copy()
        if request.user.role == 'member':
            try:
                member = Member.objects.get(user=request.user)
                data['member'] = member.id
            except Member.DoesNotExist:
                return handle_error(message="Member profile not found")
        
        serializer = SessionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Session booked successfully", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class SessionDetailView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            session = Session.objects.get(pk=pk)
            if user.role == 'member':
                if session.member.user != user:
                    return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            elif user.role == 'trainer':
                if session.trainer.user != user:
                    return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)
            return session
        except Session.DoesNotExist:
            return handle_not_found(message="Session not found")

    @swagger_auto_schema(tags=['Sessions'], operation_summary='Get session details', responses={200: SessionSerializer()})
    def get(self, request, pk):
        session = self.get_object(pk, request.user)
        if isinstance(session, Response): return session
        serializer = SessionSerializer(session)
        return handle_success(data=serializer.data, message="Session details retrieved successfully")

    @swagger_auto_schema(tags=['Sessions'], operation_summary='Update session', request_body=SessionSerializer)
    def patch(self, request, pk):
        session = self.get_object(pk, request.user)
        if isinstance(session, Response): return session
        
        old_status = session.status
        serializer = SessionSerializer(session, data=request.data, partial=True)
        if serializer.is_valid():
            updated_session = serializer.save()
            
            if old_status != 'completed' and updated_session.status == 'completed':
                session_date = updated_session.start_time.date()
                if not AttendanceRecord.objects.filter(member=updated_session.member, date=session_date).exists():
                    AttendanceRecord.objects.create(
                        member=updated_session.member,
                        check_in_time=updated_session.start_time,
                        date=session_date,
                        method='session'
                    )

            return handle_success(data=serializer.data, message="Session updated successfully")
        return handle_validation_error(errors=serializer.errors)

    @swagger_auto_schema(tags=['Sessions'], operation_summary='Cancel session')
    def delete(self, request, pk):
        session = self.get_object(pk, request.user)
        if isinstance(session, Response): return session
        session.status = 'cancelled'
        session.save()
        return handle_success(message="Session cancelled successfully")
