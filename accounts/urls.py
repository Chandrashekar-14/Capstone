from django.urls import path
from .views import login_view, student_dashboard, placement_dashboard
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('placement/', views.placement_dashboard, name='placement_dashboard'),
    path('profile/', views.student_profile, name='student_profile'),
    path('placement-insights/', views.placement_insights, name='placement_insights'),
    path('skill-gap/', views.skill_gap_analyzer, name='skill_gap'),
    path('readiness-score/', views.readiness_score, name='readiness_score'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]