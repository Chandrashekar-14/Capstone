from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Student
import json

# 🔐 LOGIN VIEW
def login_view(request):
    if request.method == 'POST':
        username = request.POST['email']   # using email field as username
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # 🔁 Role-based redirection
            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'placement':
                return redirect('placement_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


# 👨‍🎓 STUDENT DASHBOARD
@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('login')  # block unauthorized access
    return render(request, 'student_dashboard.html')


# 🏢 PLACEMENT DASHBOARD
@login_required
def placement_dashboard(request):
    if request.user.role != 'placement':
        return redirect('login')  # block unauthorized access
    return render(request, 'placement_dashboard.html')

# accounts/views.py
from django.shortcuts import render

def student_dashboard(request):
    return render(request, 'student_dashboard.html')

def student_profile(request):
    return render(request, 'student_profile.html')

def placement_insights(request):
    return render(request, 'placement_insights.html')

def skill_gap_analyzer(request):
    return render(request, 'skill_gap.html')

def readiness_score(request):
    return render(request, 'readiness_score.html')

def logout_view(request):
    # logic for logout
    pass

@login_required
def student_profile(request):
    # Only allow students
    if request.user.role != 'student':
        return redirect('login')

    # Get the logged-in student's record
    student = get_object_or_404(Student, user=request.user)

    # Calculate placement readiness
    readiness_score = round(
        (student.skills + student.academics + student.practice + student.projects + student.aptitude) / 5
    )

    # Prepare data for template
    student_data = {
        'name': student.user.get_full_name() or student.user.username,
        'branch': student.branch,
        'year': student.year,
        'cgpa': student.cgpa,
        'readiness_score': readiness_score,
        'achievements': student.get_achievements()  # must return a list
    }

    return render(request, 'student_profile.html', {'student': student_data})