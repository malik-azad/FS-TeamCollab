# core/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Helper function for profile photo upload path
def profile_photo_path(instance, filename):
    # Stores profile photos in a folder named after the username
    return f'profile_photos/{instance.user.username}/{filename}'

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Profile(models.Model):
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('COORDINATOR', 'Coordinator'),
        ('ADMIN', 'Admin'),
    ]
    # Batch years from 2015 to next year
    BATCH_YEAR_CHOICES = [
        (year, str(year)) for year in range(2015, timezone.now().year + 2)
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    full_name = models.CharField(max_length=255, blank=True, null=True)
    enrollment_no = models.CharField(
        max_length=50, unique=True,
        help_text="Display/Record Enrollment No. (Mirrors login ID)",
        blank=True, null=True
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='STUDENT'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='profiles'
    )
    batch_start_year = models.IntegerField(
        choices=BATCH_YEAR_CHOICES, null=True, blank=True
    )
    profile_photo = models.ImageField(
        upload_to=profile_photo_path, null=True, blank=True
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Set to True once the coordinator approves the registration."
    )

    def __str__(self):
        display_name = self.full_name if self.full_name else self.user.username
        verified_status = " (Verified)" if self.is_verified else " (Pending)"
        return f"{display_name} - {self.get_role_display()}{verified_status}"

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
    name = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, unique=True
    )
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.get_name_display()

class Feedback(models.Model):
    # Descriptive labels for ratings
    RATING_DESCRIPTIVE_LABELS = {
        1: 'Very Poor',
        2: 'Poor',
        3: 'Average',
        4: 'Good',
        5: 'Excellent'
    }
    RATING_CHOICES_NUMERIC = [
        (val, label) for val, label in RATING_DESCRIPTIVE_LABELS.items()
    ]

        # --- NEW: Choices for the Sentiment field ---
    SENTIMENT_CHOICES = [
        ('POSITIVE', 'Positive'),
        ('NEGATIVE', 'Negative'),
        ('NEUTRAL', 'Neutral'),
    ]
    # --- END OF NEW ---


    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='feedbacks_given'
    )
    category = models.ForeignKey(
        FeedbackCategory, on_delete=models.PROTECT, related_name='feedbacks'
    )
    department_at_submission = models.ForeignKey(
        Department, on_delete=models.SET_NULL,
        null=True, blank=False, related_name='submitted_feedbacks'
    )

    # Ratings for 5 questions
    rating1 = models.IntegerField(
        choices=RATING_CHOICES_NUMERIC, null=True, blank=True,
        help_text="Rating for question 1"
    )
    rating2 = models.IntegerField(
        choices=RATING_CHOICES_NUMERIC, null=True, blank=True,
        help_text="Rating for question 2"
    )
    rating3 = models.IntegerField(
        choices=RATING_CHOICES_NUMERIC, null=True, blank=True,
        help_text="Rating for question 3"
    )
    rating4 = models.IntegerField(
        choices=RATING_CHOICES_NUMERIC, null=True, blank=True,
        help_text="Rating for question 4"
    )
    rating5 = models.IntegerField(
        choices=RATING_CHOICES_NUMERIC, null=True, blank=True,
        help_text="Rating for question 5"
    )

    # Input method: text or audio
    INPUT_METHOD_CHOICES = [
        ('TEXT', 'Text Input'),
        ('AUDIO', 'Audio Recording'),
    ]
    input_method = models.CharField(
        max_length=10, choices=INPUT_METHOD_CHOICES, default='TEXT'
    )

    text_feedback = models.TextField(
        blank=True, null=True,
        help_text="Typed feedback or (future) transcribed audio."
    )
    audio_feedback = models.FileField(
        upload_to='feedback_audio/', null=True, blank=True,
        help_text="Uploaded/recorded audio file."
    )

    is_anonymous = models.BooleanField(default=False)
    # Field to allow revoking anonymity
    anonymity_revoked = models.BooleanField(
        default=False,
        help_text="If True, the student has chosen to reveal their identity for this anonymous feedback."
    )

    
    # --- NEW SENTIMENT FIELD ---
    sentiment = models.CharField(
        max_length=10, 
        choices=SENTIMENT_CHOICES, 
        null=True, 
        blank=True, 
        help_text="The analyzed sentiment of the feedback text."
    )
    # --- END OF NEW FIELD ---

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        # Show anonymity status in string representation
        anon_status = ""
        if self.is_anonymous and not self.anonymity_revoked:
            anon_status = " (Anonymous)"
        elif self.is_anonymous and self.anonymity_revoked:
            anon_status = " (Anonymity Revoked)"

        student_identifier = self.student.username
        return (
            f"Feedback by {student_identifier} for "
            f"{self.category.get_name_display()}{anon_status} "
            f"on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
        )