# core/admin.py
from django.contrib import admin
from .models import (
    Department, 
    Profile, 
    FeedbackCategory, 
    # CategoryQuestion, # Model removed
    Feedback
)

# To make the admin interface a bit more user-friendly for these models
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'enrollment_no', 'role', 'department', 'batch_start_year')
    list_filter = ('role', 'department', 'batch_start_year')
    search_fields = ('user__username', 'full_name', 'enrollment_no')
    raw_id_fields = ('user', 'department') # Useful for selecting user/department from a large list

class FeedbackCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_name_display_admin', 'description') # get_name_display is the human-readable choice
    search_fields = ('name',)

    def get_name_display_admin(self, obj):
        return obj.get_name_display()
    get_name_display_admin.short_description = 'Display Name' # Column header in admin

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('student_username', 'category_name', 'timestamp', 'sentiment', 'is_anonymous', 'department_at_submission')
    list_filter = ('category', 'timestamp', 'is_anonymous', 'department_at_submission')
    search_fields = ('student__username', 'text_feedback', 'category__name')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',) # Make timestamp read-only in detail view
    
    # For showing student username and category name more nicely
    def student_username(self, obj):
        return obj.student.username
    student_username.short_description = 'Student (Enrollment ID)'

    def category_name(self, obj):
        return obj.category.get_name_display()
    category_name.short_description = 'Category'


# Register your models here
admin.site.register(Department, DepartmentAdmin)
# admin.site.register(Subject) # Model removed
admin.site.register(Profile, ProfileAdmin)
admin.site.register(FeedbackCategory, FeedbackCategoryAdmin)
# admin.site.register(CategoryQuestion) # Model removed
admin.site.register(Feedback, FeedbackAdmin)