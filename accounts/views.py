from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Student
from .ml_model import train_model, predict_student
from .forms import StudentForm
from collections import Counter
from django.shortcuts import render
from accounts.models import Student
from .ml_skill_gap import train_model, analyze_student
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.db.models import Q
import json
from .scoring import calculate_readiness_score, get_readiness_status, calculate_average_readiness

# 🔐 LOGIN VIEW
def login_view(request):
    if request.method == 'POST':
        username = request.POST['email']   # using email as username
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

@login_required
def student_dashboard(request):
    
    if request.user.role != 'student':
        return redirect('login')

    student = get_object_or_404(Student, user=request.user)

    # Calculate readiness score using unified system
    readiness_score = calculate_readiness_score(student)
    prediction_status = get_readiness_status(readiness_score)

    return render(request, 'student_dashboard.html', {
        'student': student,
        'readiness_score': readiness_score,
        'prediction_status': prediction_status
    })


# 🏢 PLACEMENT DASHBOARD
@login_required
def placement_dashboard(request):
    if request.user.role != 'placement':
        return redirect('login')  # block unauthorized access
    return render(request, 'placement_dashboard.html')


@login_required
def readiness_score(request):
    return render(request, 'readiness_score.html')


def logout_view(request):
    logout(request)  # ✅ clears session
    return redirect('login')

@login_required
def student_profile(request):
    if request.user.role != 'student':
        return redirect('login')

    student = get_object_or_404(Student, user=request.user)

    # Calculate placement readiness using unified system
    readiness_score = calculate_readiness_score(student)

    # Prepare data for template
    student_data = {
        'name': student.user.get_full_name() or student.user.username,
        'branch': student.branch,
        'year': student.year,
        'cgpa': student.cgpa,
        'skills': student.skills,
        'academics': student.academics,
        'practice': student.practice,
        'projects': student.projects,
        'aptitude': student.aptitude,
        'achievements': student.get_achievements(),  # returns a list
        'readiness_score': readiness_score
    }

    return render(request, 'student_profile.html', {'student': student_data})

def edit_profile(request):
    student = request.user.student

    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('student_profile')  # back to profile page
    else:
        form = StudentForm(instance=student)

    return render(request, 'edit_profile.html', {'form': form})

@login_required
def placement_insights(request):
    students = Student.objects.all()
    total_students = students.count()
    students_placed = students.filter(placed=True).count()
    students_not_placed = total_students - students_placed

    # Personal/student-specific placement insight
    student_insight = None
    if request.user.role == 'student':
        current_student = get_object_or_404(Student, user=request.user)
        applications = getattr(current_student, 'applications', 1 if current_student.placed else 0)
        offers = getattr(current_student, 'offers', 1 if current_student.placed else 0)
        success_rate = round((offers / applications) * 100, 2) if applications else 0
        student_insight = {
            'name': current_student.user.get_full_name() or current_student.user.username,
            'applications': applications,
            'offers': offers,
            'success_rate': success_rate,
            'status': 'Placed' if current_student.placed else 'Not Placed',
            'applied_companies': current_student.get_applied_companies(),
            'placed_company': current_student.company or 'N/A'
        }
    elif request.user.role == 'placement':
        student_id = request.GET.get('student_id')
        if student_id:
            current_student = get_object_or_404(Student, id=student_id)
            applications = getattr(current_student, 'applications', 1 if current_student.placed else 0)
            offers = getattr(current_student, 'offers', 1 if current_student.placed else 0)
            success_rate = round((offers / applications) * 100, 2) if applications else 0
            student_insight = {
                'name': current_student.user.get_full_name() or current_student.user.username,
                'applications': applications,
                'offers': offers,
                'success_rate': success_rate,
                'status': 'Placed' if current_student.placed else 'Not Placed',
                'applied_companies': current_student.get_applied_companies(),
                'placed_company': current_student.company or 'N/A'
            }

    # -----------------------------
    # Calculate average readiness dynamically using unified system
    # -----------------------------
    avg_readiness = calculate_average_readiness(students)

    # -----------------------------
    # Company-wise placements
    # -----------------------------
    company_counts = Counter([s.company for s in students if s.placed and getattr(s, 'company', None)])
    company_labels = list(company_counts.keys())
    company_values = list(company_counts.values())

    # -----------------------------
    # Batch-wise placement distribution
    # -----------------------------
    batch_counts = Counter([s.year for s in students if s.placed])
    batch_labels = sorted([f"Year {year}" for year in sorted(batch_counts.keys())])
    batch_values = [batch_counts[int(label.split()[-1])] for label in batch_labels]

    # -----------------------------
    # Readiness score distribution
    # -----------------------------
    bins = [0, 50, 60, 70, 80, 90, 100]
    bin_labels = ['0-50','51-60','61-70','71-80','81-90','91-100']
    readiness_counts = [0]*len(bin_labels)

    for s in students:
        score = (s.skills + s.academics + s.practice + s.projects + s.aptitude) / 5
        for i in range(len(bins)-1):
            if bins[i] < score <= bins[i+1]:
                readiness_counts[i] += 1
                break

    # -----------------------------
    # Recent placements (latest 10 placed students)
    # -----------------------------
    recent_placements = students.filter(placed=True).order_by('-id')[:10]

    context = {
        'student_insight': student_insight,
        'total_students': total_students,
        'students_placed': students_placed,
        'students_not_placed': students_not_placed,
        'avg_readiness': avg_readiness,
        'company_labels': company_labels,
        'company_counts': company_values,
        'batch_labels': batch_labels,
        'batch_counts': batch_values,
        'recent_placements': recent_placements,
    }

    return render(request, 'placement_insights.html', context)

@login_required
def skill_gap_analyzer(request):
    student = request.user.student

    # 🎯 Get role from form
    if request.method == "POST":
        target_role = request.POST.get("target_role")
    else:
        target_role = "Software Engineer"

    # 🔥 Train ML model
    model = train_model()

    # 🔥 ML Prediction using role-specific scoring
    result = analyze_student(student, model, target_role)

    # 🔥 Feature Importance (FIXED - readable)
    features = ["Skills", "Academics", "Practice", "Projects", "Aptitude"]

    if model:
        importance_values = model.feature_importances_
        importance = dict(zip(features, importance_values))
    else:
        importance = {}

    # 🎯 Role-based important skills
    role_requirements = {
        "Software Engineer": ["Skills", "Practice", "Projects"],
        "Data Scientist": ["Skills", "Academics", "Projects"],
        "Web Developer": ["Skills", "Projects"],
        "AI Engineer": ["Skills", "Academics", "Practice"]
    }

    priority_skills = role_requirements.get(target_role, [])

    # 🔥 Filter weak areas based on role
    filtered_weak = [
        skill for skill in result['weak_areas']
        if skill in priority_skills
    ]

    # 🤖 AI Recommendations (IMPROVED)
    recommendations = []

    if not filtered_weak:
        recommendations.append("You are on track! Keep improving consistently 🚀")

    for skill in filtered_weak:
        if skill == "Skills":
            recommendations.append("Practice coding daily (LeetCode / HackerRank)")
        elif skill == "Practice":
            recommendations.append("Focus on DSA patterns (Arrays, Trees, Graphs)")
        elif skill == "Projects":
            recommendations.append("Build 2–3 real-world projects")
        elif skill == "Aptitude":
            recommendations.append("Practice aptitude questions daily")
        elif skill == "Academics":
            recommendations.append("Revise core subjects (DBMS, OS, CN)")

    context = {
        "branch": student.branch,
        "target_role": target_role,

        # 📊 Current skills
        "current_skills": {
            "Skills": student.skills,
            "Academics": student.academics,
            "Practice": student.practice,
            "Projects": student.projects,
            "Aptitude": student.aptitude
        },

        # 🔥 ML OUTPUT
        "prediction": result.get("prediction", "No Data"),
        "probability": result.get("probability", 0),
        "strong_areas": result.get("strong_areas", []),
        "weak_areas": filtered_weak,
        "recommendations": recommendations,

        # 📊 ML Explainability
        "importance": importance,

        # 📈 Chart usage
        "student": student,

        # 📅 Year strategy
        "year_stats": {
            1: "Focus on basics",
            2: "Start DSA + projects",
            3: "Internships + advanced prep",
            4: "Placement preparation"
        }
    }

    return render(request, "skill_gap.html", context)

def logout_view(request):
    print("User before logout:", request.user)  # DEBUG: check logged-in user
    logout(request)  # ✅ this clears the session
    print("User after logout:", request.user)   # DEBUG: should show AnonymousUser
    return redirect('login')

import csv
from django.shortcuts import render, redirect
from .models import Student, User

def placement_dashboard(request):
    # -------------------------------
    # CSV Upload Handling
    # -------------------------------
    if request.method == "POST" and request.FILES.get('file'):
        file = request.FILES['file']
        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            username = row['username']
            user, created = User.objects.get_or_create(username=username)
            
            Student.objects.update_or_create(
                user=user,
                defaults={
                    'branch': row['branch'],
                    'year': row['year'],
                    'cgpa': row['cgpa'],
                    'skills': row['skills'],
                    'academics': row['academics'],
                    'practice': row['practice'],
                    'projects': row['projects'],
                    'aptitude': row['aptitude'],
                }
            )
        return redirect('placement_dashboard')

    # -------------------------------
    # Dashboard Calculations
    # -------------------------------
    students = Student.objects.all()
    total_students = students.count()
    total_companies = students.exclude(company__isnull=True).values('company').distinct().count()

    total_score = 0
    high = 0
    moderate = 0
    low = 0

    low_students = students.filter(
        skills__lt=50, academics__lt=50, practice__lt=50, projects__lt=50, aptitude__lt=50
    )

    for student in students:
        # 🎯 Calculate readiness score using unified system
        score = calculate_readiness_score(student)
        total_score += score

        if score >= 80:
            high += 1
        elif score >= 50:
            moderate += 1
        else:
            low += 1

    avg_readiness = round(total_score / total_students, 2) if total_students > 0 else 0
    placed_count = students.filter(placed=True).count()

    context = {
        'total_students': total_students,
        'avg_readiness': avg_readiness,
        'total_companies': total_companies,
        'high': high,
        'moderate': moderate,
        'low': low,
        'low_students': low_students,
        'placed_count': placed_count
    }

    return render(request, 'placement_dashboard.html', context)

def student_list(request):
    query = request.GET.get('q')

    students = Student.objects.all()

    if query:
        students = students.filter(
            Q(user__username__icontains=query) |
            Q(branch__icontains=query) |
            Q(company__icontains=query)
        )

    return render(request, 'students.html', {'students': students})

def companies_list(request):
    # Get all students who are placed and have a company
    placed_students = Student.objects.filter(placed=True).exclude(company__isnull=True).exclude(company='')
    
    # Extract unique companies and count placements
    companies_data = {}
    for student in placed_students:
        if student.company not in companies_data:
            companies_data[student.company] = []
        companies_data[student.company].append(student)
    
    # Convert to list format for template
    companies = [
        {
            'name': company,
            'count': len(students),
            'students': students
        }
        for company, students in sorted(companies_data.items())
    ]
    
    # Support search
    query = request.GET.get('q')
    if query:
        companies = [c for c in companies if query.lower() in c['name'].lower()]
    
    context = {
        'companies': companies,
        'total_companies': len(companies),
        'total_placements': placed_students.count()
    }
    
    return render(request, 'companies.html', context)

def jobs_list(request):
    # Get all placed students with a job role
    placed_students = Student.objects.filter(placed=True).exclude(role__isnull=True).exclude(role='')
    
    # Extract unique job roles and count placements
    jobs_data = {}
    for student in placed_students:
        if student.role not in jobs_data:
            jobs_data[student.role] = []
        jobs_data[student.role].append(student)
    
    # Convert to list format for template
    jobs = [
        {
            'title': role,
            'count': len(students),
            'students': students
        }
        for role, students in sorted(jobs_data.items())
    ]
    
    # Support search
    query = request.GET.get('q')
    if query:
        jobs = [j for j in jobs if query.lower() in j['title'].lower()]
    
    context = {
        'jobs': jobs,
        'total_jobs': len(jobs),
        'total_placements': placed_students.count()
    }
    
    return render(request, 'jobs.html', context)

def reports_list(request):
    students = Student.objects.all()
    total_students = students.count()
    placed_students = students.filter(placed=True).count()
    not_placed = total_students - placed_students
    
    # Placement percentage
    placement_percentage = round((placed_students / total_students * 100) if total_students > 0 else 0, 2)
    
    # Statistics by branch
    branches = {}
    for student in students:
        if student.branch not in branches:
            branches[student.branch] = {'total': 0, 'placed': 0}
        branches[student.branch]['total'] += 1
        if student.placed:
            branches[student.branch]['placed'] += 1
    
    branch_stats = [
        {
            'name': branch,
            'total': data['total'],
            'placed': data['placed'],
            'percentage': round((data['placed'] / data['total'] * 100) if data['total'] > 0 else 0, 2)
        }
        for branch, data in sorted(branches.items())
    ]
    
    # Statistics by year
    years = {}
    for student in students:
        if student.year not in years:
            years[student.year] = {'total': 0, 'placed': 0}
        years[student.year]['total'] += 1
        if student.placed:
            years[student.year]['placed'] += 1
    
    year_stats = [
        {
            'year': year,
            'total': data['total'],
            'placed': data['placed'],
            'percentage': round((data['placed'] / data['total'] * 100) if data['total'] > 0 else 0, 2)
        }
        for year, data in sorted(years.items())
    ]
    
    # Average readiness score using unified system
    avg_readiness = calculate_average_readiness(students)
    
    context = {
        'total_students': total_students,
        'placed_students': placed_students,
        'not_placed': not_placed,
        'placement_percentage': placement_percentage,
        'branch_stats': branch_stats,
        'year_stats': year_stats,
        'avg_readiness': avg_readiness,
    }
    
    return render(request, 'reports.html', context)