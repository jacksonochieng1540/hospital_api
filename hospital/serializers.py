# hospital/serializers.py

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import (
    User, Department, Doctor, Patient, Appointment, 
    MedicalRecord, Prescription, Billing
)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with password validation.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password")
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2', 
                  'first_name', 'last_name', 'role', 'phone', 'address', 'date_of_birth')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with read-only fields.
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                  'full_name', 'role', 'phone', 'address', 'date_of_birth', 
                  'profile_picture', 'date_joined', 'is_active')
        read_only_fields = ('id', 'date_joined')
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user authentication.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs


class DepartmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Department model with nested head of department info.
    """
    head_of_department_name = serializers.SerializerMethodField()
    doctor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_head_of_department_name(self, obj):
        if obj.head_of_department:
            return obj.head_of_department.get_full_name()
        return None
    
    def get_doctor_count(self, obj):
        return obj.doctors.count()


class DoctorSerializer(serializers.ModelSerializer):
    """
    Serializer for Doctor model with user details.
    """
    user_details = UserSerializer(source='user', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Doctor
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class DoctorCreateSerializer(serializers.ModelSerializer):
    """
    Separate serializer for creating doctors with user creation.
    """
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Doctor
        fields = ('user_id', 'department', 'specialization', 'license_number', 
                  'years_of_experience', 'consultation_fee', 'qualification', 'is_available')
    
    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value, role='doctor')
        except User.DoesNotExist:
            raise serializers.ValidationError("User must exist and have 'doctor' role")
        
        if hasattr(user, 'doctor_profile'):
            raise serializers.ValidationError("This user already has a doctor profile")
        
        return value
    
    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        doctor = Doctor.objects.create(user=user, **validated_data)
        return doctor


class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer for Patient model with user details.
    """
    user_details = UserSerializer(source='user', read_only=True)
    appointment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_appointment_count(self, obj):
        return obj.appointments.count()


class PatientCreateSerializer(serializers.ModelSerializer):
    """
    Separate serializer for creating patients.
    """
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Patient
        fields = ('user_id', 'blood_group', 'allergies', 'chronic_conditions', 
                  'emergency_contact_name', 'emergency_contact_phone', 
                  'insurance_provider', 'insurance_number')
    
    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value, role='patient')
        except User.DoesNotExist:
            raise serializers.ValidationError("User must exist and have 'patient' role")
        
        if hasattr(user, 'patient_profile'):
            raise serializers.ValidationError("This user already has a patient profile")
        
        return value
    
    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        patient = Patient.objects.create(user=user, **validated_data)
        return patient


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Appointment model with nested details.
    """
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    doctor_specialization = serializers.CharField(source='doctor.specialization', read_only=True)
    
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        # Check for conflicting appointments
        doctor = attrs.get('doctor')
        appointment_date = attrs.get('appointment_date')
        appointment_time = attrs.get('appointment_time')
        
        if doctor and appointment_date and appointment_time:
            # Exclude current instance if updating
            existing = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            )
            
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            
            if existing.exists():
                raise serializers.ValidationError(
                    "This doctor already has an appointment at this time"
                )
        
        return attrs


class PrescriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for Prescription model.
    """
    patient_name = serializers.CharField(source='medical_record.patient.user.get_full_name', read_only=True)
    
    class Meta:
        model = Prescription
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class MedicalRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for MedicalRecord with nested prescriptions.
    """
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = ('id', 'visit_date', 'created_at', 'updated_at')


class BillingSerializer(serializers.ModelSerializer):
    """
    Serializer for Billing model with calculated fields.
    """
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Billing
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'balance')
    
    def validate(self, attrs):
        paid_amount = attrs.get('paid_amount', 0)
        total_amount = attrs.get('total_amount')
        
        if self.instance:
            total_amount = total_amount or self.instance.total_amount
        
        if paid_amount > total_amount:
            raise serializers.ValidationError(
                {"paid_amount": "Paid amount cannot exceed total amount"}
            )
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True, label="Confirm New Password")
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


# Summary serializers for dashboard/statistics
class DepartmentSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for department listings"""
    doctor_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Department
        fields = ('id', 'name', 'floor_number', 'doctor_count', 'is_active')


class DoctorSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for doctor listings"""
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Doctor
        fields = ('id', 'name', 'specialization', 'consultation_fee', 'is_available')