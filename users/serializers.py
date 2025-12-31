from rest_framework import serializers
from django.contrib.auth import get_user_model
from gym.models import Member, Trainer
import datetime

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'phone', 'role', 'avatar', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'role']

    def validate_role(self, value):
        if value not in ['member', 'trainer']:
            raise serializers.ValidationError("Role must be 'member' or 'trainer'.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data['role']
        )
        
        if user.role == 'member':
            Member.objects.create(
                user=user,
                date_of_birth=datetime.date(2000, 1, 1), # Default placeholder
                gender='Other', # Default
                address='', 
                join_date=datetime.date.today()
            )
        elif user.role == 'trainer':
            Trainer.objects.create(
                user=user,
                hire_date=datetime.date.today()
            )
            
        return user
