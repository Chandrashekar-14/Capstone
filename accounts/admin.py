# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Student

class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )

admin.site.register(User, CustomUserAdmin)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch', 'year', 'cgpa')