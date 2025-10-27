# hospital/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Department, Doctor, Patient, Appointment,
    MedicalRecord, Prescription, Billing
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for custom User model.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'address', 'date_of_birth', 'profile_picture')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'email', 'first_name', 'last_name')
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Department model.
    """
    list_display = ('name', 'head_of_department', 'floor_number', 'is_active', 'created_at')
    list_filter = ('is_active', 'floor_number', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'head_of_department')
        }),
        ('Location & Contact', {
            'fields': ('floor_number', 'phone_extension')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """
    Admin interface for Doctor model.
    """
    list_display = ('get_full_name', 'specialization', 'department', 'license_number', 
                    'years_of_experience', 'consultation_fee', 'is_available')
    list_filter = ('specialization', 'department', 'is_available', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'license_number')
    ordering = ('user__last_name',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Professional Details', {
            'fields': ('department', 'specialization', 'license_number', 
                      'years_of_experience', 'qualification')
        }),
        ('Consultation', {
            'fields': ('consultation_fee', 'is_available')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__last_name'


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """
    Admin interface for Patient model.
    """
    list_display = ('get_full_name', 'blood_group', 'emergency_contact_name', 
                    'emergency_contact_phone', 'created_at')
    list_filter = ('blood_group', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 
                    'emergency_contact_name', 'insurance_number')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Medical Information', {
            'fields': ('blood_group', 'allergies', 'chronic_conditions')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Insurance', {
            'fields': ('insurance_provider', 'insurance_number')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__last_name'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Appointment model.
    """
    list_display = ('get_patient_name', 'get_doctor_name', 'appointment_date', 
                    'appointment_time', 'status', 'created_at')
    list_filter = ('status', 'appointment_date', 'doctor', 'created_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name',
                    'doctor__user__first_name', 'doctor__user__last_name', 'reason')
    ordering = ('-appointment_date', '-appointment_time')
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Participants', {
            'fields': ('patient', 'doctor')
        }),
        ('Schedule', {
            'fields': ('appointment_date', 'appointment_time', 'duration_minutes')
        }),
        ('Details', {
            'fields': ('reason', 'status', 'notes')
        }),
    )
    
    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'patient__user__last_name'
    
    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name()
    get_doctor_name.short_description = 'Doctor'
    get_doctor_name.admin_order_field = 'doctor__user__last_name'


class PrescriptionInline(admin.TabularInline):
    """
    Inline admin for Prescription in MedicalRecord.
    """
    model = Prescription
    extra = 1
    fields = ('medication_name', 'dosage', 'frequency', 'duration_days', 'is_active')


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for MedicalRecord model.
    """
    list_display = ('get_patient_name', 'get_doctor_name', 'visit_date', 'is_confidential')
    list_filter = ('is_confidential', 'visit_date', 'doctor')
    search_fields = ('patient__user__first_name', 'patient__user__last_name',
                    'diagnosis', 'symptoms')
    ordering = ('-visit_date',)
    date_hierarchy = 'visit_date'
    inlines = [PrescriptionInline]
    
    fieldsets = (
        ('Participants', {
            'fields': ('patient', 'doctor', 'appointment')
        }),
        ('Medical Details', {
            'fields': ('diagnosis', 'symptoms', 'treatment_plan', 'vital_signs')
        }),
        ('Privacy', {
            'fields': ('is_confidential',)
        }),
    )
    
    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'patient__user__last_name'
    
    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name() if obj.doctor else 'N/A'
    get_doctor_name.short_description = 'Doctor'


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    """
    Admin interface for Prescription model.
    """
    list_display = ('medication_name', 'get_patient_name', 'dosage', 'frequency', 
                    'duration_days', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('medication_name', 'medical_record__patient__user__first_name',
                    'medical_record__patient__user__last_name')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Medical Record', {
            'fields': ('medical_record',)
        }),
        ('Medication Details', {
            'fields': ('medication_name', 'dosage', 'frequency', 'duration_days')
        }),
        ('Instructions', {
            'fields': ('instructions', 'is_active')
        }),
    )
    
    def get_patient_name(self, obj):
        return obj.medical_record.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'


@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    """
    Admin interface for Billing model.
    """
    list_display = ('invoice_number', 'get_patient_name', 'total_amount', 
                    'paid_amount', 'get_balance', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'payment_method', 'created_at')
    search_fields = ('invoice_number', 'patient__user__first_name', 
                    'patient__user__last_name', 'description')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Participants', {
            'fields': ('patient', 'appointment')
        }),
        ('Invoice Details', {
            'fields': ('invoice_number', 'description')
        }),
        ('Payment Information', {
            'fields': ('total_amount', 'paid_amount', 'payment_status', 
                      'payment_method', 'payment_date')
        }),
    )
    
    readonly_fields = ('get_balance',)
    
    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'patient__user__last_name'
    
    def get_balance(self, obj):
        return obj.balance
    get_balance.short_description = 'Balance'
