from rest_framework import status, views
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Program, WorkoutDay, Exercise, WorkoutSet
from .serializers import ProgramSerializer, WorkoutDaySerializer, ExerciseSerializer, WorkoutSetSerializer
from core.models import Member, Trainer
from shared.permissions import IsAdminOrTrainer, IsAdminUser
from rest_framework.permissions import IsAuthenticated
from shared.responses import (
    handle_success,
    handle_error,
    handle_validation_error,
    handle_not_found,
)

class ProgramListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Programs'], operation_summary='List all programs')
    def get(self, request):
        member_id = request.query_params.get('member')
        if member_id:
            programs = Program.objects.filter(assigned_members__id=member_id).select_related('created_by__user').prefetch_related('workout_days__exercises__exercise', 'assigned_members__user')
        else:
            programs = Program.objects.select_related('created_by__user').prefetch_related('workout_days__exercises__exercise', 'assigned_members__user').all()
        serializer = ProgramSerializer(programs, many=True)
        return handle_success(data=serializer.data, message="Programs retrieved successfully", status_code=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Programs'], operation_summary='Create a new program', request_body=ProgramSerializer)
    def post(self, request):
        if not request.user.role == 'admin':
             return handle_error(message="Only admins can create programs", status_code=status.HTTP_403_FORBIDDEN)
        
        serializer = ProgramSerializer(data=request.data)
        if serializer.is_valid():
            if hasattr(request.user, 'trainer_profile'):
                serializer.save(created_by=request.user.trainer_profile)
            else:
                serializer.save()
            return handle_success(data=serializer.data, message="Program created successfully", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class ProgramDetailView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Program.objects.get(pk=pk)
        except Program.DoesNotExist:
            return None

    @swagger_auto_schema(tags=['Programs'], operation_summary='Get program details')
    def get(self, request, pk):
        program = self.get_object(pk)
        if not program:
            return handle_not_found()
        serializer = ProgramSerializer(program)
        return handle_success(data=serializer.data, message="Program details retrieved successfully", status_code=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Programs'], operation_summary='Update program')
    def put(self, request, pk):
        program = self.get_object(pk)
        if not program:
            return handle_not_found()
        serializer = ProgramSerializer(program, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Program updated successfully", status_code=status.HTTP_200_OK)
        return handle_validation_error(errors=serializer.errors)

    def patch(self, request, pk):
        program = self.get_object(pk)
        if not program:
            return handle_not_found()
        
        assigned_members_ids = request.data.get('assigned_members')
        if assigned_members_ids is not None:
            data = {k: v for k, v in request.data.items() if k != 'assigned_members'}
            if data:
                serializer = ProgramSerializer(program, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return handle_validation_error(errors=serializer.errors)
            
            program.assigned_members.set(assigned_members_ids)
            updated_serializer = ProgramSerializer(program)
            return handle_success(data=updated_serializer.data, message="Program updated successfully", status_code=status.HTTP_200_OK)
        else:
            return self.put(request, pk)

    def delete(self, request, pk):
        program = self.get_object(pk)
        if not program:
            return handle_not_found()
        program.delete()
        return handle_success(message="Program deleted successfully", status_code=status.HTTP_200_OK)

class AssignProgramView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Programs'], 
        operation_summary='Assign program to member',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'member_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the member')
            },
            required=['member_id']
        )
    )
    def post(self, request, pk):
        try:
            program = Program.objects.get(pk=pk)
            member_id = request.data.get('member_id')
            
            if not member_id:
                return handle_validation_error(errors={"member_id": "Member ID is required"})

            try:
                member = Member.objects.get(id=member_id)
            except Member.DoesNotExist:
                return handle_not_found(message="Member not found")
            
            if request.user.role not in ['admin', 'trainer']:
                 return handle_error(message="Unauthorized", status_code=status.HTTP_403_FORBIDDEN)

            program.assigned_members.add(member)
            return handle_success(message="Program assigned successfully")
            
        except Program.DoesNotExist:
            return handle_not_found(message="Program not found")

class WorkoutDayListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Workouts'], operation_summary='Create workout day', request_body=WorkoutDaySerializer)
    def post(self, request):
        serializer = WorkoutDaySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Workout day created successfully", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class WorkoutSetListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Workouts'], operation_summary='Add exercise to workout day', request_body=WorkoutSetSerializer)
    def post(self, request):
        data = request.data.copy()
        
        exercise_input = data.get('exercise')
        if exercise_input and isinstance(exercise_input, str) and not str(exercise_input).isdigit():
            exercise, created = Exercise.objects.get_or_create(
                name=exercise_input,
                defaults={
                    'muscle_group': 'General',
                    'description': 'Custom exercise added by admin'
                }
            )
            data['exercise'] = exercise.id
            
        serializer = WorkoutSetSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return handle_success(data=serializer.data, message="Exercise added to workout day", status_code=status.HTTP_201_CREATED)
        return handle_validation_error(errors=serializer.errors)

class ExerciseListView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Workouts'], operation_summary='List all exercises')
    def get(self, request):
        exercises = Exercise.objects.all()
        serializer = ExerciseSerializer(exercises, many=True)
        return handle_success(data=serializer.data, message="Exercises retrieved successfully", status_code=status.HTTP_200_OK)
