# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

def profile_photo_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/profile_photos/<username>/<filename>
    return f'profile_photos/{instance.user.username}/{filename}'

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# Removed Subject model as it's no longer used for feedback differentiation

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
    CATEGORY_CHOICES = [
        ('TEACHING', 'Teaching'), 
        ('INFRASTRUCTURE', 'Infrastructure'), 
        ('TRANSPORT', 'Transport'),
        ('EXTRACURRICULAR', 'Extracurricular Activities'), 
        ('STAFF_BEHAVIOUR', 'Staff Behaviour'),
        ('CANTEEN', 'Canteen'), 
        ('LIBRARY', 'Library'),
    ]
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    # REMOVED: requires_subject_selection field

    def __str__(self):
        return self.get_name_display()

class CategoryQuestion(models.Model):
    category = models.ForeignKey(FeedbackCategory, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500, help_text="The question text.")
    order = models.PositiveIntegerField(default=0, help_text="Order for questions (1-5).") # e.g., 1, 2, 3, 4, 5

    class Meta:
        ordering = ['category', 'order']
        # Ensure order is unique per category if you have exactly 5 questions always
        # Ensure question text is unique per category (optional, but can be good)
        unique_together = [('category', 'order'), ('category', 'text')] 

    def __str__(self):
        return f"{self.category.get_name_display()} - Q{self.order}: {self.text[:50]}..."

class Feedback(models.Model):
    # Descriptive labels for ratings (used in templates/JS)
    RATING_DESCRIPTIVE_LABELS = {
        1: 'Very Poor', 2: 'Poor', 3: 'Average', 4: 'Good', 5: 'Excellent'
    }
    # Choices for the model field (stores numeric value)
    RATING_CHOICES_NUMERIC = [(val, label) for val, label in RATING_DESCRIPTIVE_LABELS.items()]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks_given')
    category = models.ForeignKey(FeedbackCategory, on_delete=models.PROTECT, related_name='feedbacks')
    # REMOVED: subject field
    department_at_submission = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=False, related_name='submitted_feedbacks')

    rating1 = models.IntegerField(choices=RATING_CHOICES_NUMERIC, null=True, blank=True, help_text="Rating for question 1 of the category")
    rating2 = models.IntegerField(choices=RATING_CHOICES_NUMERIC, null=True, blank=True, help_text="Rating for question 2 of the category")
    rating3 = models.IntegerField(choices=RATING_CHOICES_NUMERIC, null=True, blank=True, help_text="Rating for question 3 of the category")
    rating4 = models.IntegerField(choices=RATING_CHOICES_NUMERIC, null=True, blank=True, help_text="Rating for question 4 of the category")
    rating5 = models.IntegerField(choices=RATING_CHOICES_NUMERIC, null=True, blank=True, help_text="Rating for question 5 of the category")

    INPUT_METHOD_CHOICES = [
        ('TEXT', 'Text Input'),
        ('AUDIO', 'Audio Recording'),
    ]
    input_method = models.CharField(max_length=10, choices=INPUT_METHOD_CHOICES, default='TEXT')
    
    text_feedback = models.TextField(blank=True, null=True, help_text="Typed feedback or transcribed audio.")
    audio_feedback = models.FileField(upload_to='feedback_audio/', null=True, blank=True, help_text="Uploaded/recorded audio file.")

    is_anonymous = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        anon_status = " (Anonymous)" if self.is_anonymous else ""
        student_identifier = self.student.username # Assuming username is enrollment_id
        # Removed subject_info from this string representation
        return f"Feedback by {student_identifier} for {self.category.get_name_display()}{anon_status} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"