from django import forms
from .models import Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['cgpa', 'skills', 'academics', 'practice', 'projects', 'aptitude', 'achievements', 'applied_companies']
        widgets = {
            'applied_companies': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Enter applied companies separated by commas'
            })
        }
