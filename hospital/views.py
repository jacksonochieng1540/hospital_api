from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    User, Department, Doctor, Patient, Appointment,
    MedicalRecord, Prescription, Billing
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    DepartmentSerializer, DoctorSerializer, DoctorCreateSerializer,
    PatientSerializer, PatientCreateSerializer, AppointmentSerializer,
    MedicalRecordSerializer, PrescriptionSerializer, BillingSerializer,
    ChangePasswordSerializer, DepartmentSummarySerializer, DoctorSummarySerializer
)
from .permissions import (
    IsAdminUser, IsDoctor, IsPatient, IsDoctorOrAdmin,
    IsOwnerOrAdmin, IsPatientOwnerOrDoctor, IsAppointmentParticipant,
    CanManageBilling
)
from .pagination import StandardResultsSetPagination, LargeResultsSetPagination


# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user.
    POST /api/auth/register/
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login user and return authentication token.
    POST /api/auth/login/
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        login(request, user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout user and delete authentication token.
    POST /api/auth/logout/
    """
    try:
        request.user.auth_token.delete()
        logout(request)
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password.
    POST /api/auth/change-password/
    """
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        # Update token
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        
        return Response({
            'message': 'Password changed successfully',
            'token': token.key
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Get current authenticated user details.
    GET /api/auth/me/
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# User ViewSet
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    Provides CRUD operations for users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'last_name']
    ordering = ['-date_joined']


# Department ViewSet
class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Department model.
    All authenticated users can view, only admins can modify.
    """
    queryset = Department.objects.annotate(doctor_count=Count('doctors'))
    serializer_class = DepartmentSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'floor_number']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'floor_number', 'created_at']
    ordering = ['name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def doctors(self, request, pk=None):
        """
        Get all doctors in a specific department.
        GET /api/departments/{id}/doctors/
        """
        department = self.get_object()
        doctors = department.doctors.all()
        serializer = DoctorSerializer(doctors, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get department summary for quick listings.
        GET /api/departments/summary/
        """
        departments = self.filter_queryset(self.get_queryset())
        serializer = DepartmentSummarySerializer(departments, many=True)
        return Response(serializer.data)


# Doctor ViewSet
class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Doctor model.
    Different serializers for create and list/retrieve.
    """
    queryset = Doctor.objects.select_related('user', 'department').all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['specialization', 'department', 'is_available']
    search_fields = ['user__first_name', 'user__last_name', 'license_number']
    ordering_fields = ['user__last_name', 'years_of_experience', 'consultation_fee']
    ordering = ['user__last_name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DoctorCreateSerializer
        return DoctorSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        """
        Get all appointments for a specific doctor.
        GET /api/doctors/{id}/appointments/
        """
        doctor = self.get_object()
        appointments = doctor.appointments.all()
        
        # Filter by date if provided
        date = request.query_params.get('date', None)
        if date:
            appointments = appointments.filter(appointment_date=date)
        
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def toggle_availability(self, request, pk=None):
        """
        Toggle doctor availability.
        PATCH /api/doctors/{id}/toggle_availability/
        """
        doctor = self.get_object()
        doctor.is_available = not doctor.is_available
        doctor.save()
        serializer = self.get_serializer(doctor)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Get all available doctors.
        GET /api/doctors/available/
        """
        doctors = self.filter_queryset(self.get_queryset().filter(is_available=True))
        page = self.paginate_queryset(doctors)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(doctors, many=True)
        return Response(serializer.data)


# Patient ViewSet
class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Patient model.
    Patients can view their own profile, admins and doctors can view all.
    """
    queryset = Patient.objects.select_related('user').all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['blood_group']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    ordering_fields = ['user__last_name', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PatientCreateSerializer
        return PatientSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsAuthenticated]
        elif self.action in ['list']:
            permission_classes = [IsAuthenticated, IsDoctorOrAdmin]
        else:
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'doctor']:
            return Patient.objects.all()
        elif user.role == 'patient':
            return Patient.objects.filter(user=user)
        return Patient.objects.none()
    
    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        """
        Get all appointments for a specific patient.
        GET /api/patients/{id}/appointments/
        """
        patient = self.get_object()
        appointments = patient.appointments.all()
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def medical_records(self, request, pk=None):
        """
        Get all medical records for a specific patient.
        GET /api/patients/{id}/medical_records/
        """
        patient = self.get_object()
        records = patient.medical_records.all()
        serializer = MedicalRecordSerializer(records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def billings(self, request, pk=None):
        """
        Get all billings for a specific patient.
        GET /api/patients/{id}/billings/
        """
        patient = self.get_object()
        billings = patient.billings.all()
        serializer = BillingSerializer(billings, many=True)
        return Response(serializer.data)


# Appointment ViewSet
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Appointment model.
    Patients can create and view their appointments.
    Doctors can view their appointments and update status.
    """
    queryset = Appointment.objects.select_related('patient__user', 'doctor__user').all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsAppointmentParticipant]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'appointment_date', 'doctor', 'patient']
    search_fields = ['patient__user__first_name', 'patient__user__last_name', 'reason']
    ordering_fields = ['appointment_date', 'appointment_time', 'created_at']
    ordering = ['-appointment_date', '-appointment_time']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Appointment.objects.all()
        elif user.role == 'doctor':
            if hasattr(user, 'doctor_profile'):
                return Appointment.objects.filter(doctor=user.doctor_profile)
        elif user.role == 'patient':
            if hasattr(user, 'patient_profile'):
                return Appointment.objects.filter(patient=user.patient_profile)
        return Appointment.objects.none()
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Update appointment status.
        PATCH /api/appointments/{id}/update_status/
        """
        appointment = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Appointment.STATUS_CHOICES):
            return Response({
                'error': 'Invalid status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        appointment.status = new_status
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get upcoming appointments.
        GET /api/appointments/upcoming/
        """
        from datetime import date
        appointments = self.filter_queryset(
            self.get_queryset().filter(
                appointment_date__gte=date.today(),
                status__in=['scheduled', 'confirmed']
            )
        )
        page = self.paginate_queryset(appointments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)


# MedicalRecord ViewSet
class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MedicalRecord model.
    Only doctors can create, patients can view their own.
    """
    queryset = MedicalRecord.objects.select_related('patient__user', 'doctor__user').prefetch_related('prescriptions').all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated, IsPatientOwnerOrDoctor]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['patient', 'doctor', 'is_confidential']
    search_fields = ['diagnosis', 'symptoms', 'patient__user__first_name', 'patient__user__last_name']
    ordering_fields = ['visit_date', 'created_at']
    ordering = ['-visit_date']
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'doctor']:
            return MedicalRecord.objects.all()
        elif user.role == 'patient':
            if hasattr(user, 'patient_profile'):
                return MedicalRecord.objects.filter(patient=user.patient_profile)
        return MedicalRecord.objects.none()
    
    def perform_create(self, serializer):
        # Automatically set doctor to current user if they're a doctor
        if self.request.user.role == 'doctor' and hasattr(self.request.user, 'doctor_profile'):
            serializer.save(doctor=self.request.user.doctor_profile)
        else:
            serializer.save()


# Prescription ViewSet
class PrescriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Prescription model.
    Only doctors can create and update prescriptions.
    """
    queryset = Prescription.objects.select_related('medical_record__patient__user').all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated, IsDoctorOrAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'medical_record']
    search_fields = ['medication_name', 'medical_record__patient__user__first_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['patch'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a prescription.
        PATCH /api/prescriptions/{id}/deactivate/
        """
        prescription = self.get_object()
        prescription.is_active = False
        prescription.save()
        serializer = self.get_serializer(prescription)
        return Response(serializer.data)


# Billing ViewSet
class BillingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Billing model.
    Admins and receptionists can manage, patients can view their own.
    """
    queryset = Billing.objects.select_related('patient__user', 'appointment').all()
    serializer_class = BillingSerializer
    permission_classes = [IsAuthenticated, CanManageBilling]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['payment_status', 'payment_method', 'patient']
    search_fields = ['invoice_number', 'patient__user__first_name', 'patient__user__last_name']
    ordering_fields = ['created_at', 'total_amount', 'payment_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'receptionist']:
            return Billing.objects.all()
        elif user.role == 'patient':
            if hasattr(user, 'patient_profile'):
                return Billing.objects.filter(patient=user.patient_profile)
        return Billing.objects.none()
    
    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        """
        Record a payment for billing.
        POST /api/billings/{id}/record_payment/
        Body: {"amount": 100.00, "payment_method": "cash"}
        """
        billing = self.get_object()
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method')
        
        if not amount:
            return Response({
                'error': 'Amount is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = float(amount)
        except ValueError:
            return Response({
                'error': 'Invalid amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update payment
        from decimal import Decimal
        from django.utils import timezone
        
        billing.paid_amount += Decimal(str(amount))
        
        if billing.paid_amount >= billing.total_amount:
            billing.payment_status = 'paid'
            billing.payment_date = timezone.now()
        elif billing.paid_amount > 0:
            billing.payment_status = 'partial'
        
        if payment_method:
            billing.payment_method = payment_method
        
        billing.save()
        serializer = self.get_serializer(billing)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Get all pending billings.
        GET /api/billings/pending/
        """
        billings = self.filter_queryset(
            self.get_queryset().filter(payment_status='pending')
        )
        page = self.paginate_queryset(billings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(billings, many=True)
        return Response(serializer.data)


# Dashboard/Statistics View
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDoctorOrAdmin])
def dashboard_stats(request):
    """
    Get dashboard statistics.
    GET /api/dashboard/stats/
    """
    from datetime import date, timedelta
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    stats = {
        'total_patients': Patient.objects.count(),
        'total_doctors': Doctor.objects.count(),
        'total_departments': Department.objects.count(),
        'appointments_today': Appointment.objects.filter(appointment_date=today).count(),
        'appointments_this_week': Appointment.objects.filter(appointment_date__gte=week_ago).count(),
        'pending_billings': Billing.objects.filter(payment_status='pending').count(),
        'available_doctors': Doctor.objects.filter(is_available=True).count(),
    }
    
    if request.user.role == 'doctor':
        if hasattr(request.user, 'doctor_profile'):
            doctor = request.user.doctor_profile
            stats['my_appointments_today'] = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=today
            ).count()
            stats['my_upcoming_appointments'] = Appointment.objects.filter(
                doctor=doctor,
                appointment_date__gte=today,
                status__in=['scheduled', 'confirmed']
            ).count()
    
    return Response(stats)
