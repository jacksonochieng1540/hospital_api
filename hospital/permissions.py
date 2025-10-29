from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'doctor'


class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'patient'


class IsDoctorOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['doctor', 'admin'])


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
     
        if obj == request.user:
            return True
        
        return False


class IsPatientOwnerOrDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        
        if request.user.role == 'doctor':
            return True
        
        
        if request.user.role == 'patient':
            if hasattr(request.user, 'patient_profile'):
                return obj.patient == request.user.patient_profile and request.method in permissions.SAFE_METHODS
        
        return False


class IsAppointmentParticipant(permissions.BasePermission):
  
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
      
        if request.user.role == 'admin':
            return True
        
        if request.user.role == 'doctor':
            if hasattr(request.user, 'doctor_profile'):
                return obj.doctor == request.user.doctor_profile
        
        if request.user.role == 'patient':
            if hasattr(request.user, 'patient_profile'):
                return obj.patient == request.user.patient_profile
        
        return False


class CanManageBilling(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
  
        if request.user.role in ['admin', 'receptionist']:
            return True
        
        if request.user.role == 'patient':
            if hasattr(request.user, 'patient_profile'):
                return obj.patient == request.user.patient_profile and request.method in permissions.SAFE_METHODS
        
        return False


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
