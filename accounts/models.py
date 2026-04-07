# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import json

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('placement', 'Placement'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    branch = models.CharField(max_length=100)
    year = models.IntegerField()
    cgpa = models.FloatField()
    skills = models.IntegerField(default=0)
    academics = models.IntegerField(default=0)
    practice = models.IntegerField(default=0)
    projects = models.IntegerField(default=0)
    aptitude = models.IntegerField(default=0)
    achievements = models.TextField(blank=True, null=True) 
    placed = models.BooleanField(default=False) 
    
    company = models.CharField(max_length=100, blank=True, null=True)
    applied_companies = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)  # store as comma-separated

    def __str__(self):
        return self.user.username

    def get_achievements(self):
        """Return achievements as a list for the template loop."""
        if not self.achievements:
            return []
        try:
            return json.loads(self.achievements)
        except:
            return [a.strip() for a in self.achievements.split(',')]

    def get_applied_companies(self):
        if not self.applied_companies:
            return []
        try:
            return json.loads(self.applied_companies)
        except Exception:
            return [c.strip() for c in self.applied_companies.split(',') if c.strip()]


class Company(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    requirements = models.TextField()  # JSON format: skill1:score, skill2:score, etc.
    min_cgpa = models.FloatField(default=0.0)
    min_skills_score = models.IntegerField(default=0)
    min_academics_score = models.IntegerField(default=0)
    salary = models.CharField(max_length=100, blank=True, null=True)
    positions_available = models.IntegerField(default=1)
    roles = models.TextField(blank=True, null=True)  # JSON format: role1, role2, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_requirements(self):
        """Parse requirements from JSON"""
        if not self.requirements:
            return {}
        try:
            return json.loads(self.requirements)
        except:
            return {}
    
    def get_roles(self):
        """Get roles as list"""
        if not self.roles:
            return []
        try:
            return json.loads(self.roles)
        except:
            return [r.strip() for r in self.roles.split(',')]
