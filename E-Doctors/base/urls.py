from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('login/', views.login, name="login"),
    path('logout/', views.logout_user, name="logout"),
    path('sign_up/', views.sign_up, name="sign_up"),
    path('doctor_profile/', views.doctor_profile, name="doctor_profile"),
    path('view_doctor_profile/<str:doctor_id>/', views.view_doctor_profile, name="view_doctor_profile"),
    path('edit_doctor_profile/', views.edit_doctor_profile, name="edit_doctor_profile"),
    path('patient_profile/', views.patient_profile, name="patient_profile"),
    path('edit_patient_profile/', views.edit_patient_profile, name="edit_patient_profile"),
    path('blogs/', views.blogs, name="blogs"),
    path('omicron/', views.omicron, name="omicron"),
    path('heart-attacks/', views.heart, name="heart-attacks"),
    path('healthy-food/', views.healthy, name="healthy-food"),
]
