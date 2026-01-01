from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminRegisterTest(APITestCase):
    def test_admin_registration_success(self):
        url = reverse('admin-register')
        data = {
            'username': 'newadmin',
            'email': 'newadmin@example.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'Admin',
            'role': 'admin'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(email='newadmin@example.com').count(), 1)
        self.assertEqual(User.objects.get(email='newadmin@example.com').role, 'admin')

    def test_admin_registration_invalid_role(self):
        url = reverse('admin-register')
        data = {
            'username': 'member_trying_to_be_admin',
            'email': 'member@example.com',
            'password': 'password123',
            'first_name': 'Member',
            'last_name': 'User',
            'role': 'member'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('role', response.data['errors'])
