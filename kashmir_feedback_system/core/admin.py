# core/admin.py
from django.contrib import admin
from .models import (
    Department, 
    Profile, 
    FeedbackCategory, 
    CategoryQuestion,
    Feedback
)

admin.site.register(Department)

admin.site.register(Profile)
admin.site.register(FeedbackCategory)
admin.site.register(CategoryQuestion) # Ensure this is registered
admin.site.register(Feedback)