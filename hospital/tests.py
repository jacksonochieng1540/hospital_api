from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from datetime import date, time, timedelta
from decimal import Decimal

from .models import (
    User, Department, Doctor, Patient, Appointment,
    MedicalRecord, Prescription, Billing
)


class UserAuthenticationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        
    def test_user_registration(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'patient'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(User.objects.count(), 1)
    
    def test_user_login(self):
        user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            email='test@example.com'
        )
        data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
    
    def test_user_logout(self):
        user = User.objects.create_user(username='testuser', password='test123')
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Token.objects.filter(user=user).exists())


class DepartmentTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )
        self.token = Token.objects.create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
    def test_create_department(self):
        url = reverse('department-list')
        data = {
            'name': 'Cardiology',
            'description': 'Heart department',
            'floor_number': 3
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Department.objects.count(), 1)
    
    def test_list_departments(self):
        Department.objects.create(name='Cardiology', floor_number=3)
        Department.objects.create(name='Neurology', floor_number=4)
        
        url = reverse('department-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filter_departments(self):
        Department.objects.create(name='Active Dept', floor_number=1, is_active=True)
        Department.objects.create(name='Inactive Dept', floor_number=2, is_active=False)
        
        url = reverse('department-list')
        response = self.client.get(url, {'is_active': 'true'})
        self.assertEqual(len(response.data['results']), 1)


class DoctorTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            password='doctor123',
            role='doctor',
            first_name='John',
            last_name='Doe'
        )
        self.department = Department.objects.create(
            name='Cardiology',
            floor_number=3
        )
        self.token = Token.objects.create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_create_doctor_profile(self):
        url = reverse('doctor-list')
        data = {
            'user_id': self.doctor_user.id,
            'department': self.department.id,
            'specialization': 'cardiology',
            'license_number': 'DOC12345',
            'years_of_experience': 10,
            'consultation_fee': '150.00',
            'qualification': 'MD, MBBS'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Doctor.objects.count(), 1)
    
    def test_get_available_doctors(self):
        Doctor.objects.create(
            user=self.doctor_user,
            department=self.department,
            specialization='cardiology',
            license_number='DOC123',
            years_of_experience=10,
            consultation_fee=Decimal('150.00'),
            qualification='MD',
            is_available=True
        )
        
        url = reverse('doctor-available')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class AppointmentTests(APITestCase): 
    def setUp(self):
        self.patient_user = User.objects.create_user(
            username='patient1',
            password='patient123',
            role='patient'
        )
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            password='doctor123',
            role='doctor'
        )
        
        
        self.department = Department.objects.create(
            name='Cardiology',
            floor_number=3
        )
     
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            department=self.department,
            specialization='cardiology',
            license_number='DOC123',
            years_of_experience=10,
            consultation_fee=Decimal('150.00'),
            qualification='MD'
        )
        
     
        self.patient = Patient.objects.create(
            user=self.patient_user,
            blood_group='A+',
            emergency_contact_name='Jane Doe',
            emergency_contact_phone='1234567890'
        )
        
        self.token = Token.objects.create(user=self.patient_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_create_appointment(self):
        url = reverse('appointment-list')
        tomorrow = date.today() + timedelta(days=1)
        data = {
            'patient': self.patient.id,
            'doctor': self.doctor.id,
            'appointment_date': tomorrow.isoformat(),
            'appointment_time': '10:00:00',
            'reason': 'Regular checkup',
            'duration_minutes': 30
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 1)
    
    def test_conflicting_appointment(self):
        tomorrow = date.today() + timedelta(days=1)
        
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=tomorrow,
            appointment_time=time(10, 0),
            reason='Test',
            duration_minutes=30
        )
        
        
        url = reverse('appointment-list')
        data = {
            'patient': self.patient.id,
            'doctor': self.doctor.id,
            'appointment_date': tomorrow.isoformat(),
            'appointment_time': '10:00:00',
            'reason': 'Another checkup',
            'duration_minutes': 30
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_upcoming_appointments(self):
      
        tomorrow = date.today() + timedelta(days=1)
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=tomorrow,
            appointment_time=time(10, 0),
            reason='Test',
            duration_minutes=30,
            status='scheduled'
        )
        
        url = reverse('appointment-upcoming')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class MedicalRecordTests(APITestCase): 
    def setUp(self):
        
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            password='doctor123',
            role='doctor'
        )
        
      
        self.patient_user = User.objects.create_user(
            username='patient1',
            password='patient123',
            role='patient'
        )
        
        
        department = Department.objects.create(name='Cardiology', floor_number=3)
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            department=department,
            specialization='cardiology',
            license_number='DOC123',
            years_of_experience=10,
            consultation_fee=Decimal('150.00'),
            qualification='MD'
        )
        
     
        self.patient = Patient.objects.create(
            user=self.patient_user,
            blood_group='A+',
            emergency_contact_name='Jane Doe',
            emergency_contact_phone='1234567890'
        )
        
        self.token = Token.objects.create(user=self.doctor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_create_medical_record(self):
        url = reverse('medical-record-list')
        data = {
            'patient': self.patient.id,
            'diagnosis': 'Hypertension',
            'symptoms': 'High blood pressure, headache',
            'treatment_plan': 'Medication and lifestyle changes',
            'vital_signs': {
                'blood_pressure': '140/90',
                'temperature': '98.6',
                'pulse': '72'
            }
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MedicalRecord.objects.count(), 1)
      
        record = MedicalRecord.objects.first()
        self.assertEqual(record.doctor, self.doctor)
    
    def test_patient_can_view_own_records(self):
       
        MedicalRecord.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            diagnosis='Common Cold',
            symptoms='Cough, fever',
            treatment_plan='Rest and fluids',
            vital_signs={}
        )
        
       
        patient_token = Token.objects.create(user=self.patient_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {patient_token.key}')
        
        url = reverse('medical-record-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class BillingTests(APITestCase):
    def setUp(self):
       
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )
       
        patient_user = User.objects.create_user(
            username='patient1',
            password='patient123',
            role='patient'
        )
        self.patient = Patient.objects.create(
            user=patient_user,
            blood_group='A+',
            emergency_contact_name='Jane Doe',
            emergency_contact_phone='1234567890'
        )
        
        self.token = Token.objects.create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_create_billing(self):
        url = reverse('billing-list')
        data = {
            'patient': self.patient.id,
            'invoice_number': 'INV-001',
            'total_amount': '500.00',
            'description': 'Consultation and medication'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Billing.objects.count(), 1)
    
    def test_record_payment(self):
        billing = Billing.objects.create(
            patient=self.patient,
            invoice_number='INV-001',
            total_amount=Decimal('500.00'),
            description='Test'
        )
        
        url = reverse('billing-record-payment', kwargs={'pk': billing.id})
        data = {
            'amount': '250.00',
            'payment_method': 'cash'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        billing.refresh_from_db()
        self.assertEqual(billing.paid_amount, Decimal('250.00'))
        self.assertEqual(billing.payment_status, 'partial')
    
    def test_full_payment_updates_status(self):
        billing = Billing.objects.create(
            patient=self.patient,
            invoice_number='INV-001',
            total_amount=Decimal('500.00'),
            description='Test'
        )
        
        url = reverse('billing-record-payment', kwargs={'pk': billing.id})
        data = {
            'amount': '500.00',
            'payment_method': 'card'
        }
        response = self.client.post(url, data)
        
        billing.refresh_from_db()
        self.assertEqual(billing.payment_status, 'paid')
        self.assertIsNotNone(billing.payment_date)


class PermissionTests(APITestCase):
    def setUp(self):
       
        self.patient_user = User.objects.create_user(
            username='patient1',
            password='patient123',
            role='patient'
        )
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            password='doctor123',
            role='doctor'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )
    
    def test_patient_cannot_create_department(self):
        token = Token.objects.create(user=self.patient_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        url = reverse('department-list')
        data = {'name': 'Test Dept', 'floor_number': 1}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_can_create_department(self):
        token = Token.objects.create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        url = reverse('department-list')
        data = {'name': 'Test Dept', 'floor_number': 1}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_unauthenticated_user_cannot_access_api(self):
        url = reverse('department-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PaginationTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )
        self.token = Token.objects.create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
       
        for i in range(15):
            Department.objects.create(
                name=f'Department {i}',
                floor_number=i % 5 + 1
            )
    
    def test_default_pagination(self):
        url = reverse('department-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(response.data['total_pages'], 2)
    
    def test_custom_page_size(self):
        url = reverse('department-list')
        response = self.client.get(url, {'page_size': 5})
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['total_pages'], 3)
    
    def test_page_navigation(self):
        url = reverse('department-list')
        
      
        response = self.client.get(url, {'page': 1, 'page_size': 10})
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
        
        
        response = self.client.get(url, {'page': 2, 'page_size': 10})
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNone(response.data['next'])
        self.assertIsNotNone(response.data['previous'])


class FilteringTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )
        self.token = Token.objects.create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        
        self.cardiology = Department.objects.create(
            name='Cardiology',
            floor_number=3,
            is_active=True
        )
        self.neurology = Department.objects.create(
            name='Neurology',
            floor_number=4,
            is_active=False
        )
        
     
        doctor_user = User.objects.create_user(
            username='doctor1',
            password='doc123',
            role='doctor',
            first_name='John',
            last_name='Smith'
        )
        Doctor.objects.create(
            user=doctor_user,
            department=self.cardiology,
            specialization='cardiology',
            license_number='DOC001',
            years_of_experience=10,
            consultation_fee=Decimal('150.00'),
            qualification='MD',
            is_available=True
        )
    
    def test_filter_departments_by_active_status(self):
        url = reverse('department-list')
        response = self.client.get(url, {'is_active': 'true'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Cardiology')
    
    def test_search_departments(self):
        url = reverse('department-list')
        response = self.client.get(url, {'search': 'Cardio'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Cardiology')
    
    def test_filter_doctors_by_specialization(self):
        url = reverse('doctor-list')
        response = self.client.get(url, {'specialization': 'cardiology'})
        self.assertEqual(len(response.data['results']), 1)
    
    def test_search_doctors_by_name(self):
        url = reverse('doctor-list')
        response = self.client.get(url, {'search': 'John'})
        self.assertEqual(len(response.data['results']), 1)
    
    def test_ordering_departments(self):
        url = reverse('department-list')
        response = self.client.get(url, {'ordering': 'name'})
        results = response.data['results']
        self.assertEqual(results[0]['name'], 'Cardiology')
        self.assertEqual(results[1]['name'], 'Neurology')
        
        response = self.client.get(url, {'ordering': '-name'})
        results = response.data['results']
        self.assertEqual(results[0]['name'], 'Neurology')
        self.assertEqual(results[1]['name'], 'Cardiology')



