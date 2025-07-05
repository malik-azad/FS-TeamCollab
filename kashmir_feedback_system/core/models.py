# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

def profile_photo_path(instance, filename):
    return f'profile_photos/{instance.user.username}/{filename}'

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# Subject model is completely removed.
# CategoryQuestion model is completely removed.

class Profile(models.Model):
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('COORDINATOR', 'Coordinator'),
        ('ADMIN', 'Admin'),
    ]
    BATCH_YEAR_CHOICES = [(year, str(year)) for year in range(2015, timezone.now().year + 2)]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, blank=True, null=True) 
    enrollment_no = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Display/Record Enrollment No. (Mirrors login ID)", 
        blank=True, 
        null=True   
    ) 
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='profiles')
    batch_start_year = models.IntegerField(choices=BATCH_YEAR_CHOICES, null=True, blank=True)
    profile_photo = models.ImageField(upload_to=profile_photo_path, null=True, blank=True)

    def __str__(self):
        display_name = self.full_name if self.full_name else self.user.username
        return f"{display_name} - {self.get_role_display()}"

class FeedbackCategory(models.Model):
    # These CATEGORY_CHOICES values (e.g., 'TEACHING', 'INFRASTRUCTURE') 
    # will be used as keys in the JavaScript for hardcoded questions.
    CATEGORY_CHOICES = [
        ('TEACHING', 'Teaching'), 
        ('INFRASTRUCTURE', 'Infrastructure'), 
        ('TRANSPORT', 'Transport'),
        ('EXTRACURRICULAR', 'Extracurricular Activities'), 
        ('STAFF_BEHAVIOUR', 'Staff Behaviour'),
        ('CANTEEN', 'Canteen'), 
        ('LIBRARY', 'Library'),
        # Add more fixed categories here if needed
    ]
    # The 'name' field will store the key (e.g., 'TEACHING')
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True) # Optional description

    def __str__(self):
        return self.get_name_display() # Shows the human-readable choice label

class Feedback(models.Model):
    RATING_DESCRIPTIVE_LABELS = {
        1: 'Very Poor', 2: 'Poor', 3: 'Average', 4: 'Good', 5: 'Excellent'
    }
    RATING_CHOICES_NUMERIC = [(val, label) for val, label in RATING_DESCRIPTIVE_LABELS.items()]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks_given')
    category = models.ForeignKey(FeedbackCategory, on_delete=models.PROTECT, related_name='feedbacks')
    department_at_submission = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=False, related_name='submitted_feedbacks')

    rating1 = models.IntegerField(choices=RATING_CHOICES_NUMERIC, null=True, blank=True, help_text="Rating for question 1")
    rating2 = models.IntegerField(choices=RATING_CHOICES_NUMERIC, null=True, blank=True, help_text="Rating for question 2")
    rating3 = models.IntegerField(choices=RATING_CHOICES_NUMERIC, null=True, blank=True, help_text="Rating for question 3")
    rating4 = models.IntegerField(choices=RATING_CHOICES_NUMERIC, null=True, blank=True, help_text="Rating for question 4")
    rating5 = models.IntegerField(choices=RATING_CHOICES_NUMERIC, null=True, blank=True, help_text="Rating for question 5")

    INPUT_METHOD_CHOICES = [
        ('TEXT', 'Text Input'),
        ('AUDIO', 'Audio Recording'),
    ]
    input_method = models.CharField(max_length=10, choices=INPUT_METHOD_CHOICES, default='TEXT')
    
    text_feedback = models.TextField(blank=True, null=True, help_text="Typed feedback or (future) transcribed audio.")
    audio_feedback = models.FileField(upload_to='feedback_audio/', null=True, blank=True, help_text="Uploaded/recorded audio file.")

    is_anonymous = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        anon_status = " (Anonymous)" if self.is_anonymous else ""
        student_identifier = self.student.username
        return f"Feedback by {student_identifier} for {self.category.get_name_display()}{anon_status} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"