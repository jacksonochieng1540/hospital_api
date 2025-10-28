from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('receptionist', 'Receptionist'),
        ('patient', 'Patient'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    head_of_department = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='headed_departments',
        limit_choices_to={'role': 'doctor'}
    )
    floor_number = models.IntegerField(validators=[MinValueValidator(0)])
    phone_extension = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Doctor(models.Model):
    SPECIALIZATION_CHOICES = (
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
        ('gynecology', 'Gynecology'),
        ('dermatology', 'Dermatology'),
        ('psychiatry', 'Psychiatry'),
        ('general', 'General Medicine'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='doctors')
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES)
    license_number = models.CharField(max_length=50, unique=True)
    years_of_experience = models.IntegerField(validators=[MinValueValidator(0)])
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    qualification = models.TextField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'doctors'
        ordering = ['user__last_name']
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"


class Patient(models.Model):
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A Positive'),
        ('A-', 'A Negative'),
        ('B+', 'B Positive'),
        ('B-', 'B Negative'),
        ('AB+', 'AB Positive'),
        ('AB-', 'AB Negative'),
        ('O+', 'O Positive'),
        ('O-', 'O Negative'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    allergies = models.TextField(blank=True, help_text="Comma-separated list of allergies")
    chronic_conditions = models.TextField(blank=True, help_text="Existing medical conditions")
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=15)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.user.get_full_name()


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration_minutes = models.IntegerField(default=30, validators=[MinValueValidator(15)])
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'appointments'
        ordering = ['-appointment_date', '-appointment_time']
        unique_together = ['doctor', 'appointment_date', 'appointment_time']
    
    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.appointment_date}"


class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name='medical_records')
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_record')
    visit_date = models.DateTimeField(auto_now_add=True)
    diagnosis = models.TextField()
    symptoms = models.TextField()
    treatment_plan = models.TextField()
    vital_signs = models.JSONField(default=dict, help_text="Blood pressure, temperature, pulse, etc.")
    is_confidential = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medical_records'
        ordering = ['-visit_date']
    
    def __str__(self):
        return f"Record for {self.patient} on {self.visit_date.date()}"


class Prescription(models.Model):
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='prescriptions')
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100, help_text="e.g., Once daily, Twice daily")
    duration_days = models.IntegerField(validators=[MinValueValidator(1)])
    instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prescriptions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.medication_name} for {self.medical_record.patient}"


class Billing(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('insurance', 'Insurance'),
        ('bank_transfer', 'Bank Transfer'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='billings')
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='billing')
    invoice_number = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billings'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.patient}"
    
    @property
    def balance(self):
        return self.total_amount - self.paid_amount
