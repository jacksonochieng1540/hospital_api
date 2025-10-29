from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'doctors', views.DoctorViewSet, basename='doctor')
router.register(r'patients', views.PatientViewSet, basename='patient')
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')
router.register(r'medical-records', views.MedicalRecordViewSet, basename='medical-record')
router.register(r'prescriptions', views.PrescriptionViewSet, basename='prescription')
router.register(r'billings', views.BillingViewSet, basename='billing')

urlpatterns = [
    path('auth/register/', views.register_user, name='register'),
    path('auth/login/', views.login_user, name='login'),
    path('auth/logout/', views.logout_user, name='logout'),
    path('auth/change-password/', views.change_password, name='change-password'),
    path('auth/me/', views.get_current_user, name='current-user'),
    
 
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    

    path('', include(router.urls)),
]
