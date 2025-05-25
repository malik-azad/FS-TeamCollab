# core/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse # Kept for potential future API needs, but not used by current subject removal

# Removed Subject from models import as it's assumed to be deleted
from .models import Profile, Department, Feedback, FeedbackCategory, CategoryQuestion 
from .forms import SignupForm, GiveFeedbackForm


def landing_page_view(request):
    return render(request, 'core/landing_page.html')

def signup_view(request):
    if request.user.is_authenticated:
        # TODO: Consider role-based dashboard redirection here too
        return redirect('core:student_dashboard')

    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save()
            # User is not auto-logged in; redirected to login page
            messages.success(request, f"Account created successfully for {profile.user.username}! Please log in to continue.")
            return redirect('core:login')
        else:
            messages.error(request, "Please correct the errors highlighted below.")
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form} )

def login_view(request):
    if request.user.is_authenticated:
        # TODO: Implement role-based redirection
        # if hasattr(request.user, 'profile'):
        #     if request.user.profile.role == 'COORDINATOR':
        #         return redirect('core:coordinator_dashboard') 
        #     elif request.user.profile.role == 'ADMIN':
        #         return redirect('core:admin_dashboard')
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
            
            # TODO: Implement role-based redirection after login
            return redirect('core:student_dashboard')
        else:
            messages.error(request, "Invalid Enrollment ID or password. Please check your credentials and try again.")
    else:
        form = AuthenticationForm()
        form.fields['username'].widget.attrs.update(
            {'placeholder': 'Enrollment ID', 'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-custom-blue focus:bg-white focus:outline-none text-sm text-gray-700 placeholder-gray-400'}
        )
        form.fields['username'].label = ''
        form.fields['password'].widget.attrs.update(
            {'placeholder': 'Password', 'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-custom-blue focus:bg-white focus:outline-none text-sm text-gray-700 placeholder-gray-400'}
        )
        form.fields['password'].label = ''
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('core:landing_page')

@login_required(login_url='core:login')
def student_dashboard_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'STUDENT':
        messages.error(request, "Access denied to this dashboard.") 
        auth_logout(request) 
        return redirect('core:login')
        
    past_feedbacks = Feedback.objects.filter(student=request.user).order_by('-timestamp')
    return render(request, 'core/student_dashboard.html', {'past_feedbacks': past_feedbacks})

@login_required(login_url='core:login')
def give_feedback_view(request):
    # Ensure user is a student and has a profile with a department
    if not hasattr(request.user, 'profile') or not request.user.profile.department:
        messages.error(request, "Your profile is incomplete (missing department). Please update your profile.")
        # TODO: Consider redirecting to a dedicated profile edit page
        return redirect('core:student_dashboard') 

    if request.user.profile.role != 'STUDENT':
        messages.error(request, "Only students can submit feedback.")
        # TODO: Redirect to their appropriate dashboard if not student (though @login_required and student_dashboard check should handle most cases)
        return redirect('core:student_dashboard')

    categories_with_questions = {}
    # Get descriptive rating labels from the Feedback model
    rating_labels_map = Feedback.RATING_DESCRIPTIVE_LABELS 

    all_categories = FeedbackCategory.objects.prefetch_related('questions').order_by('name')
    for cat in all_categories:
        categories_with_questions[str(cat.id)] = {
            'name': cat.get_name_display(),
            # REMOVED: 'requires_subject' key, as subject selection is removed
            'questions': list(cat.questions.order_by('order').values_list('text', flat=True))
        }

    # REMOVED: department_subjects logic, as subject selection is removed

    if request.method == 'POST':
        # Pass user to form, though it's not used for subject filtering anymore, 
        # it's good practice if the form might need user context for other things later.
        form = GiveFeedbackForm(request.POST, request.FILES, user=request.user) 
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.student = request.user
            feedback.department_at_submission = request.user.profile.department
            # REMOVED: feedback.subject = form.cleaned_data.get('subject') as subject is gone
            
            if feedback.input_method == 'AUDIO' and feedback.audio_feedback:
                # Placeholder for audio transcription logic (Phase 4)
                # For now, text_feedback might be empty or have a placeholder like "[Audio Submitted]"
                # if you want to differentiate it.
                pass

            feedback.save()
            messages.success(request, "Thank you! Your feedback has been submitted successfully.")
            return redirect('core:student_dashboard')
        else:
            messages.error(request, "Please correct the errors highlighted below.")
    else:
        form = GiveFeedbackForm(user=request.user)

    context = {
        'form': form,
        'categories_with_questions_json': categories_with_questions,
        'rating_labels_json': rating_labels_map, 
        # REMOVED: 'department_subjects_json' from context
    }
    return render(request, 'core/give_feedback.html', context)
