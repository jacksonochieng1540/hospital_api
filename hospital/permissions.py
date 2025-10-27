# hospital/permissions.py

from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission to only allow admin users to access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsDoctor(permissions.BasePermission):
    """
    Permission to only allow doctors to access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'doctor'


class IsPatient(permissions.BasePermission):
    """
    Permission to only allow patients to access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'patient'


class IsDoctorOrAdmin(permissions.BasePermission):
    """
    Permission to allow doctors or admins to access.
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['doctor', 'admin'])


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to allow users to only access their own objects or admins.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.role == 'admin':
            return True
        
        # Check if object has a user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object is the user itself
        if obj == request.user:
            return True
        
        return False


class IsPatientOwnerOrDoctor(permissions.BasePermission):
    """
    Permission for medical records - patients can view their own,
    doctors can view and create records.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == 'admin':
            return True
        
        # Doctors can access medical records
        if request.user.role == 'doctor':
            return True
        
        # Patients can only view their own records
        if request.user.role == 'patient':
            if hasattr(request.user, 'patient_profile'):
                return obj.patient == request.user.patient_profile and request.method in permissions.SAFE_METHODS
        
        return False


class IsAppointmentParticipant(permissions.BasePermission):
    """
    Permission for appointments - patients and doctors involved in appointment.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == 'admin':
            return True
        
        # Doctor involved in appointment
        if request.user.role == 'doctor':
            if hasattr(request.user, 'doctor_profile'):
                return obj.doctor == request.user.doctor_profile
        
        # Patient involved in appointment
        if request.user.role == 'patient':
            if hasattr(request.user, 'patient_profile'):
                return obj.patient == request.user.patient_profile
        
        return False


class CanManageBilling(permissions.BasePermission):
    """
    Permission for billing - admins and receptionists can manage,
    patients can view their own.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin and receptionist have full access
        if request.user.role in ['admin', 'receptionist']:
            return True
        
        # Patients can view their own billing
        if request.user.role == 'patient':
            if hasattr(request.user, 'patient_profile'):
                return obj.patient == request.user.patient_profile and request.method in permissions.SAFE_METHODS
        
        return False


class ReadOnly(permissions.BasePermission):
    """
    Permission to only allow safe methods (GET, HEAD, OPTIONS).
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS