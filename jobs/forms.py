from django import forms
from .models import Job, Subscriber

class JobSubmissionForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company', 'location', 'description', 'url', 'category', 'employer_email']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

from django import forms
from .models import Subscriber

class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email',
                'class': 'form-control',
                'required': True
            })
        }
