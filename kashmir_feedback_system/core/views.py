# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout, get_user_model # Import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test # Import user_passes_test
from django.views.decorators.http import require_POST


from .models import Profile, Department, Feedback, FeedbackCategory
from .forms import SignupForm, GiveFeedbackForm, EditProfileForm 

User = get_user_model() # Get the active User model

# --- Helper functions for role checks (can be defined here or in a separate utils.py) ---
def is_student(user):
    return hasattr(user, 'profile') and user.profile.role == 'STUDENT'

def is_coordinator(user):
    return hasattr(user, 'profile') and user.profile.role == 'COORDINATOR'

def is_admin(user): # For future use
    return hasattr(user, 'profile') and user.profile.role == 'ADMIN' or user.is_superuser


# ... (landing_page_view, signup_view, login_view, logout_view as before) ...
def landing_page_view(request):
    return render(request, 'core/landing_page.html')

def signup_view(request):
    # ... (signup_view code as established) ...
    if request.user.is_authenticated:
        return redirect('core:student_dashboard')
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save()
            messages.success(request, f"Account created successfully for {profile.user.username}! Please log in to continue.")
            return redirect('core:login')
        else:
            messages.error(request, "Please correct the errors highlighted below.")
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        # Smart redirection based on role
        if hasattr(request.user, 'profile'):
            if request.user.profile.role == 'COORDINATOR':
                return redirect('core:coordinator_dashboard')
            elif request.user.profile.role == 'ADMIN':
                pass # return redirect('core:admin_dashboard') # TODO: Create admin dashboard URL
            # Default to student dashboard if role is STUDENT or profile doesn't specify other known roles
        return redirect('core:student_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            display_name = user.username 
            if hasattr(user, 'profile') and user.profile and user.profile.full_name:
                display_name = user.profile.full_name
            messages.info(request, f"Welcome back, {display_name}!")
            
            # Smart redirection after login
            if hasattr(user, 'profile'):
                if user.profile.role == 'COORDINATOR':
                    return redirect('core:coordinator_dashboard')
                elif user.profile.role == 'ADMIN':
                    pass # return redirect('core:admin_dashboard')
            return redirect('core:student_dashboard') # Default for students
        else:
            messages.error(request, "Invalid Enrollment ID or password. Please check your credentials and try again.")
    else:
        form = AuthenticationForm()
        # ... (form field styling as before) ...
        form.fields['username'].widget.attrs.update({'placeholder': 'Enrollment ID', 'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-custom-blue focus:bg-white focus:outline-none text-sm text-gray-700 placeholder-gray-400'})
        form.fields['username'].label = ''
        form.fields['password'].widget.attrs.update({'placeholder': 'Password', 'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-custom-blue focus:bg-white focus:outline-none text-sm text-gray-700 placeholder-gray-400'})
        form.fields['password'].label = ''
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    # ... (logout_view code as established) ...
    auth_logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('core:landing_page')

@login_required(login_url='core:login')
@user_passes_test(is_student, login_url='core:landing_page') # Check if user is a student
def student_dashboard_view(request):
    # The role check is now more robust with user_passes_test, 
    # but an explicit check here is fine as a double measure or if you need specific logic.
    # if not hasattr(request.user, 'profile') or request.user.profile.role != 'STUDENT':
    #     messages.error(request, "Access denied to this dashboard.") 
    #     auth_logout(request) 
    #     return redirect('core:login')
        
    past_feedbacks = Feedback.objects.filter(student=request.user).select_related('category', 'department_at_submission').order_by('-timestamp')
    return render(request, 'core/student_dashboard.html', {'past_feedbacks': past_feedbacks})


@login_required(login_url='core:login')
@user_passes_test(is_student, login_url='core:landing_page')
def give_feedback_view(request):
    # ... (give_feedback_view code as established, role check might be redundant due to decorator) ...
    # if not hasattr(request.user, 'profile') or not request.user.profile.department:
    #     messages.error(request, "Your profile is incomplete (missing department). Please update your profile.")
    #     return redirect('core:student_dashboard') 
    # if request.user.profile.role != 'STUDENT': # This check is now handled by @user_passes_test
    #     messages.error(request, "Only students can submit feedback.")
    #     return redirect('core:student_dashboard')

    rating_labels_map = Feedback.RATING_DESCRIPTIVE_LABELS 
    available_categories_for_js = []
    all_db_categories = FeedbackCategory.objects.all().order_by('name')
    for cat_obj in all_db_categories:
        available_categories_for_js.append({'id': str(cat_obj.id), 'value_key': cat_obj.name, 'display_name': cat_obj.get_name_display()})
    
    if request.method == 'POST':
        form = GiveFeedbackForm(request.POST, request.FILES, user=request.user) 
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.student = request.user
            feedback.department_at_submission = request.user.profile.department
            if feedback.input_method == 'AUDIO' and feedback.audio_feedback: pass
            feedback.save()
            messages.success(request, "Thank you! Your feedback has been submitted successfully.")
            return redirect('core:student_dashboard')
        else:
            messages.error(request, "Please correct the errors highlighted below.")
    else:
        form = GiveFeedbackForm(user=request.user)
    context = {'form': form, 'available_categories_data': available_categories_for_js, 'rating_labels_data': rating_labels_map}
    return render(request, 'core/give_feedback.html', context)


@login_required(login_url='core:login')
def view_feedback_detail(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    
    can_view = False
    if feedback.student == request.user: # Student can view their own
        can_view = True
    elif hasattr(request.user, 'profile') and request.user.profile.role == 'COORDINATOR':
        # Coordinator can view feedback from their own department
        if feedback.department_at_submission == request.user.profile.department:
            can_view = True
    # TODO: Add elif for ADMIN role to view any feedback
    # elif hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN':
    #     can_view = True
    
    if not can_view:
        messages.error(request, "You are not authorized to view this feedback.")
        # Redirect to their own dashboard or a general access denied page
        if hasattr(request.user, 'profile') and request.user.profile.role == 'COORDINATOR':
            return redirect('core:coordinator_dashboard')
        return redirect('core:student_dashboard')

    category_value_key = feedback.category.name 
    rating_labels_map = Feedback.RATING_DESCRIPTIVE_LABELS
    context = {
        'feedback': feedback,
        'category_value_key': category_value_key,
        'rating_labels_data': rating_labels_map,
    }
    return render(request, 'core/view_feedback_detail.html', context)

@login_required(login_url='core:login')
@require_POST 
def delete_feedback_view(request, feedback_id):
    # ... (delete_feedback_view code as established) ...
    feedback = get_object_or_404(Feedback, id=feedback_id)
    if feedback.student != request.user: # Students can only delete their own
        messages.error(request, "You are not authorized to delete this feedback.")
        return redirect('core:student_dashboard')
    feedback.delete()
    messages.success(request, "Your feedback submission has been successfully deleted.")
    return redirect('core:student_dashboard')

@login_required(login_url='core:login')
@user_passes_test(is_student, login_url='core:landing_page') # Only students can edit their student profile page
def edit_profile_view(request):
    # ... (edit_profile_view code as established) ...
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('core:student_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EditProfileForm(instance=profile)
    context = {'form': form, 'profile': profile }
    return render(request, 'core/edit_profile.html', context)

# --- UPDATED COORDINATOR DASHBOARD VIEW ---
@login_required(login_url='core:login')
@user_passes_test(is_coordinator, login_url='core:landing_page')
def coordinator_dashboard_view(request):
    coordinator_profile = request.user.profile
    department = coordinator_profile.department

    if not department:
        messages.error(request, "Your coordinator profile is not associated with a department. Please contact an administrator.")
        auth_logout(request)
        return redirect('core:login')

    # Fetch students belonging to this coordinator's department
    students_in_department = User.objects.filter(
        profile__department=department,
        profile__role='STUDENT'
    ).select_related('profile').order_by('username')

    # Fetch feedback submitted by students from this coordinator's department
    # We filter on Feedback.department_at_submission
    department_feedback = Feedback.objects.filter(
        department_at_submission=department
    ).select_related('student', 'category').order_by('-timestamp')
    # For student name on feedback, if not anonymous: feedback.student.profile.full_name or feedback.student.username

    context = {
        'coordinator_name': coordinator_profile.full_name or request.user.username,
        'department_name': department.name,
        'students': students_in_department,
        'department_feedback_list': department_feedback, # Pass feedback to template
    }
    return render(request, 'core/coordinator_dashboard.html', context)
# --- END OF UPDATED VIEW ---