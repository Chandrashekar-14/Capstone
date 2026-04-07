from django.urls import path
from django.contrib.auth import views as auth_views
from .views import login_view, student_dashboard, placement_dashboard, logout_view
from .views import placement_dashboard, student_list
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),

    # Student
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.student_profile, name='student_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('readiness-score/', views.readiness_score, name='readiness_score'),
    path('skill-gap/', views.skill_gap_analyzer, name='skill_gap'),
    path('placement-insights/', views.placement_insights, name='placement_insights'),
    path('logout/', logout_view, name='logout'), 

    # Placement Dashboard (Admin/Placement side)
    path('placement/', views.placement_dashboard, name='placement_dashboard'),
    path('students/', views.student_list, name='student_list'),
    path('companies/', views.companies_list, name='companies_list'),
    path('companies/delete/<int:company_id>/', views.delete_company, name='delete_company'),
    path('jobs/', views.jobs_list, name='jobs_list'),
    path('reports/', views.reports_list, name='reports_list'),
    path('ml-weight-analyzer/', views.ml_weight_analyzer, name='ml_weight_analyzer'),
    path('retrain-ml-weights/', views.retrain_ml_weights, name='retrain_ml_weights'),
]