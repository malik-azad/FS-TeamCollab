# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.db.models import Count, Q # Import Count and Q for aggregation
import google.generativeai as genai
import json

from .models import Profile, Department, Feedback, FeedbackCategory 
from .forms import SignupForm, GiveFeedbackForm, EditProfileForm 

User = get_user_model()

# --- Helper functions for role checks (Unchanged) ---
def is_student(user): return hasattr(user, 'profile') and user.profile.role == 'STUDENT'
def is_coordinator(user): return hasattr(user, 'profile') and user.profile.role == 'COORDINATOR'
def is_admin(user): return hasattr(user, 'profile') and user.profile.role == 'ADMIN' or user.is_superuser

# --- All views up to edit_profile_view are UNCHANGED from our last stable version ---
# ... (pending_verification_view, landing_page_view, signup_view, login_view, logout_view) ...
# ... (student_dashboard_view, give_feedback_view, view_feedback_detail, delete_feedback_view, edit_profile_view) ...
def pending_verification_view(request):
    return render(request, 'core/pending_verification.html')
def landing_page_view(request):
    return render(request, 'core/landing_page.html')
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('core:student_dashboard')
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('core:pending_verification')
        else: messages.error(request, "Please correct the errors highlighted below.")
    else: form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})
def login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile'):
            if request.user.profile.role == 'COORDINATOR': return redirect('core:coordinator_dashboard')
        return redirect('core:student_dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            display_name = user.username 
            if hasattr(user, 'profile') and user.profile and user.profile.full_name: display_name = user.profile.full_name
            messages.info(request, f"Welcome back, {display_name}!")
            if hasattr(user, 'profile'):
                if user.profile.role == 'COORDINATOR': return redirect('core:coordinator_dashboard')
            return redirect('core:student_dashboard')
        else:
            username = request.POST.get('username')
            if username:
                try:
                    user_check = User.objects.get(username=username)
                    if not user_check.is_active:
                        messages.warning(request, "This account exists but is pending verification. Please wait for your department coordinator to approve your registration.")
                        return redirect('core:login')
                except User.DoesNotExist: pass
            messages.error(request, "Invalid Enrollment ID or password. Please check your credentials and try again.")
    else:
        form = AuthenticationForm()
        form.fields['username'].widget.attrs.update({'placeholder': 'Enrollment ID', 'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-custom-blue focus:bg-white focus:outline-none text-sm text-gray-700 placeholder-gray-400'})
        form.fields['username'].label = ''
        form.fields['password'].widget.attrs.update({'placeholder': 'Password', 'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-custom-blue focus:bg-white focus:outline-none text-sm text-gray-700 placeholder-gray-400'})
        form.fields['password'].label = ''
    return render(request, 'core/login.html', {'form': form})
def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('core:landing_page')
@login_required(login_url='core:login')
@user_passes_test(is_student, login_url='core:landing_page')
def student_dashboard_view(request):
    past_feedbacks = Feedback.objects.filter(student=request.user).select_related('category', 'department_at_submission').order_by('-timestamp')
    return render(request, 'core/student_dashboard.html', {'past_feedbacks': past_feedbacks})




# --- Hardcoded questions map (Unchanged) ---
HARDCODED_CATEGORY_QUESTIONS = {
    'TEACHING': [ "Clarity of explanations?", "Instructor engagement?", "Course content relevance?", "Fairness of grading?", "Overall teaching effectiveness?" ],
    'INFRASTRUCTURE': [ "Classroom/lab conditions?", "IT resources (Wi-Fi, PCs)?", "Library resources/space?", "Sports facilities?", "Overall campus infrastructure?" ],
    'TRANSPORT': [ "Transport punctuality?", "Bus comfort & safety?", "Route accessibility?", "Transport staff behavior?", "Overall transport satisfaction?" ],
    'EXTRACURRICULAR': [ "Variety/quality of activities?", "Support for student clubs?", "Sports/cultural event opportunities?", "Communication about activities?", "Overall extracurricular satisfaction?" ],
    'STAFF_BEHAVIOUR': [ "Administrative staff professionalism?", "Support staff helpfulness?", "Faculty accessibility (non-academic)?", "Fairness in staff dealings?", "Overall experience with staff?" ],
    'CANTEEN': [ "Food quality/taste?", "Variety of food options?", "Canteen hygiene?", "Value for money?", "Overall canteen satisfaction?" ],
    'LIBRARY': [ "Book/journal availability?", "Library staff helpfulness?", "Study environment comfort?", "Digital resource access?", "Overall library effectiveness?" ]
}


# --- NEW HELPER FUNCTION FOR AUDIO TRANSCRIPTION ---
def transcribe_audio_with_gemini(audio_file_path):
    """
    Transcribes an audio file using the Google Gemini API.
    Returns the transcribed text or None if an error occurs.
    """
    if not settings.GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY not configured for transcription.")
        return None
        
    try:
        print(f"Attempting to transcribe audio file: {audio_file_path}")
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # Upload the file to Google's service first
        audio_file = genai.upload_file(path=audio_file_path)
        print(f"File uploaded successfully. URI: {audio_file.uri}")

        # Create the model instance that can handle audio
        model = genai.GenerativeModel('models/gemini-2.5-pro') # A model that supports audio input

        # Make the API call with the file and a simple prompt
        response = model.generate_content([
            "Please transcribe the following audio.", 
            audio_file
        ])

        # Clean up the uploaded file from Google's service
        genai.delete_file(audio_file.name)
        print(f"Temporary file {audio_file.name} deleted from Google service.")

        if response.text:
            print("Transcription successful.")
            return response.text.strip()
        else:
            print("Transcription failed: AI returned an empty response.")
            return "[Transcription failed or audio was empty]"

    except Exception as e:
        print(f"ERROR during audio transcription: {e}")
        # In case of error, we can return a placeholder text
        return f"[Audio transcription failed due to an error: {e}]"


# --- NEW HELPER FUNCTION FOR SENTIMENT ANALYSIS ---
def analyze_sentiment_with_gemini(text):
    """
    Analyzes the sentiment of a given text using the Google Gemini API.
    Returns 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'.
    """
    if not settings.GOOGLE_API_KEY or not text:
        return None

    try:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt = (
            "Analyze the sentiment of the following student feedback. "
            "Classify it as either 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'. "
            "Respond with only one of those three words, without any additional text or punctuation.\n\n"
            "Feedback: \"" + text + "\""
        )

        response = model.generate_content(prompt)
        
        # Clean up the response to get just the keyword
        sentiment = response.text.strip().upper()
        
        if sentiment in ['POSITIVE', 'NEGATIVE', 'NEUTRAL']:
            print(f"Sentiment analysis successful. Result: {sentiment}")
            return sentiment
        else:
            print(f"Sentiment analysis returned an unexpected value: {sentiment}")
            return 'NEUTRAL' # Default to Neutral if the response is not as expected

    except Exception as e:
        print(f"ERROR during sentiment analysis: {e}")
        return None

# --- give_feedback_view (UPDATED with logic for rating-only sentiment analysis) ---
@login_required(login_url='core:login')
@user_passes_test(is_student, login_url='core:landing_page')
def give_feedback_view(request):
    # ... (initial checks and data prep as before) ...
    if not hasattr(request.user, 'profile') or not request.user.profile.department:
        messages.error(request, "Your profile is incomplete. Please update your profile.")
        return redirect('core:student_dashboard')
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
            
            feedback.save() # Save first to handle file uploads

            text_to_analyze = feedback.text_feedback
            # Check for transcription
            if feedback.input_method == 'AUDIO' and feedback.audio_feedback:
                transcribed_text = transcribe_audio_with_gemini(feedback.audio_feedback.path)
                if transcribed_text:
                    feedback.text_feedback = transcribed_text
                    text_to_analyze = transcribed_text
            
            # --- NEW LOGIC FOR SENTIMENT ANALYSIS ---
            has_text_content = text_to_analyze and text_to_analyze.strip()
            # Check if any rating was actually submitted
            ratings_data = [feedback.rating1, feedback.rating2, feedback.rating3, feedback.rating4, feedback.rating5]
            has_any_rating = any(r is not None for r in ratings_data)

            # If there's no text but there ARE ratings, construct a synthetic text for analysis
            if not has_text_content and has_any_rating:
                print("No text found, but ratings exist. Generating synthetic text for sentiment analysis.")
                synthetic_text_parts = []
                category_key = feedback.category.name
                questions = HARDCODED_CATEGORY_QUESTIONS.get(category_key, [])
                
                for i, rating_val in enumerate(ratings_data):
                    if rating_val is not None and i < len(questions):
                        question = questions[i]
                        rating_label = Feedback.RATING_DESCRIPTIVE_LABELS.get(rating_val, "")
                        synthetic_text_parts.append(f"For the question '{question}', the rating given was '{rating_label}'.")
                
                text_to_analyze = " ".join(synthetic_text_parts)
                print(f"Synthetic text for analysis: {text_to_analyze}")
            
            # Now, perform sentiment analysis if we have any text (real or synthetic)
            if text_to_analyze and text_to_analyze.strip():
                sentiment_result = analyze_sentiment_with_gemini(text_to_analyze)
                if sentiment_result:
                    feedback.sentiment = sentiment_result
            # --- END OF NEW LOGIC ---
            
            # Save the final object with transcription and/or sentiment
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
    if feedback.student == request.user: can_view = True
    elif hasattr(request.user, 'profile') and request.user.profile.role == 'COORDINATOR' and feedback.department_at_submission == request.user.profile.department: can_view = True
    if not can_view:
        messages.error(request, "You are not authorized to view this feedback.")
        if hasattr(request.user, 'profile') and request.user.profile.role == 'COORDINATOR': return redirect('core:coordinator_dashboard')
        return redirect('core:student_dashboard')
    category_value_key = feedback.category.name 
    rating_labels_map = Feedback.RATING_DESCRIPTIVE_LABELS
    context = {'feedback': feedback, 'category_value_key': category_value_key, 'rating_labels_data': rating_labels_map}
    return render(request, 'core/view_feedback_detail.html', context)
@login_required(login_url='core:login')
@require_POST 
def delete_feedback_view(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    if feedback.student != request.user:
        messages.error(request, "You are not authorized to delete this feedback.")
        return redirect('core:student_dashboard')
    feedback.delete()
    messages.success(request, "Your feedback submission has been successfully deleted.")
    return redirect('core:student_dashboard')
@login_required(login_url='core:login')
@user_passes_test(is_student, login_url='core:landing_page')
def edit_profile_view(request):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('core:student_dashboard')
        else: messages.error(request, "Please correct the errors below.")
    else: form = EditProfileForm(instance=profile)
    context = {'form': form, 'profile': profile }
    return render(request, 'core/edit_profile.html', context)
@login_required(login_url='core:login')
@user_passes_test(is_coordinator, login_url='core:landing_page')
def coordinator_dashboard_view(request):
    coordinator_profile = request.user.profile
    department = coordinator_profile.department
    if not department:
        messages.error(request, "Your coordinator profile is not associated with a department. Please contact an administrator.")
        auth_logout(request)
        return redirect('core:login')
    pending_students = User.objects.filter(profile__department=department, profile__role='STUDENT', is_active=False)
    verified_student_count = User.objects.filter(profile__department=department, profile__role='STUDENT', is_active=True).count()
    department_feedback_count = Feedback.objects.filter(department_at_submission=department).count()
    context = {'coordinator_name': coordinator_profile.full_name or request.user.username, 'department_name': department.name, 'pending_students': pending_students, 'pending_students_count': pending_students.count(), 'verified_student_count': verified_student_count, 'department_feedback_count': department_feedback_count,}
    return render(request, 'core/coordinator_dashboard.html', context)
@login_required(login_url='core:login')
@user_passes_test(is_coordinator, login_url='core:landing_page')
def manage_students_view(request):
    coordinator_profile = request.user.profile
    department = coordinator_profile.department
    students_in_department = User.objects.filter(profile__department=department, profile__role='STUDENT', is_active=True).select_related('profile').order_by('username')
    context = {'department_name': department.name if department else "N/A", 'students': students_in_department,}
    return render(request, 'core/manage_students.html', context)
@login_required(login_url='core:login')
@user_passes_test(is_coordinator, login_url='core:landing_page')
def view_department_feedback_view(request):
    coordinator_profile = request.user.profile
    department = coordinator_profile.department
    department_feedback_query = Feedback.objects.filter(department_at_submission=department).select_related('student', 'student__profile', 'category').order_by('-timestamp')
    time_filter = request.GET.get('time_filter', '')
    category_filter = request.GET.get('category_filter', '')
    if time_filter == 'week': department_feedback_query = department_feedback_query.filter(timestamp__gte=timezone.now() - timedelta(days=7))
    elif time_filter == 'month': department_feedback_query = department_feedback_query.filter(timestamp__gte=timezone.now() - timedelta(days=30))
    if category_filter: department_feedback_query = department_feedback_query.filter(category__id=category_filter)
    all_categories = FeedbackCategory.objects.all().order_by('name')
    context = {'department_name': department.name if department else "N/A", 'department_feedback_list': department_feedback_query, 'all_categories': all_categories, 'current_time_filter': time_filter, 'current_category_filter': category_filter,}
    return render(request, 'core/view_department_feedback.html', context)
@login_required(login_url='core:login')
@user_passes_test(is_coordinator, login_url='core:landing_page')
@require_POST
def approve_student_view(request, student_id):
    student_to_approve = get_object_or_404(User, id=student_id, profile__role='STUDENT')
    if student_to_approve.profile.department != request.user.profile.department:
        messages.error(request, "You are not authorized to approve students from other departments.")
        return redirect('core:coordinator_dashboard')
    student_to_approve.is_active = True
    student_to_approve.profile.is_verified = True
    student_to_approve.save()
    student_to_approve.profile.save()
    messages.success(request, f"Student '{student_to_approve.username}' has been approved and can now log in.")
    return redirect('core:coordinator_dashboard')
@login_required(login_url='core:login')
@user_passes_test(is_coordinator, login_url='core:landing_page')
@require_POST
def reject_student_view(request, student_id):
    student_to_reject = get_object_or_404(User, id=student_id, profile__role='STUDENT')
    if student_to_reject.profile.department != request.user.profile.department:
        messages.error(request, "You are not authorized to reject students from other departments.")
        return redirect('core:coordinator_dashboard')
    username = student_to_reject.username
    student_to_reject.delete()
    messages.warning(request, f"The pending registration for '{username}' has been rejected and deleted.")
    return redirect('core:coordinator_dashboard')
@login_required(login_url='core:login')
@user_passes_test(is_student, login_url='core:landing_page')
@require_POST
def revoke_anonymity_view(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    if feedback.student != request.user:
        messages.error(request, "You are not authorized to modify this feedback.")
        return redirect('core:student_dashboard')
    if not feedback.is_anonymous:
        messages.warning(request, "This feedback was not submitted anonymously.")
        return redirect('core:student_dashboard')
    feedback.anonymity_revoked = True
    feedback.save()
    messages.success(request, "You have successfully revealed your identity for this feedback.")
    return redirect('core:student_dashboard')


# --- Hardcoded questions map, now moved to the backend for use in summarization ---
HARDCODED_CATEGORY_QUESTIONS = {
    'TEACHING': [ "Clarity of explanations?", "Instructor engagement?", "Course content relevance?", "Fairness of grading?", "Overall teaching effectiveness?" ],
    'INFRASTRUCTURE': [ "Classroom/lab conditions?", "IT resources (Wi-Fi, PCs)?", "Library resources/space?", "Sports facilities?", "Overall campus infrastructure?" ],
    'TRANSPORT': [ "Transport punctuality?", "Bus comfort & safety?", "Route accessibility?", "Transport staff behavior?", "Overall transport satisfaction?" ],
    'EXTRACURRICULAR': [ "Variety/quality of activities?", "Support for student clubs?", "Sports/cultural event opportunities?", "Communication about activities?", "Overall extracurricular satisfaction?" ],
    'STAFF_BEHAVIOUR': [ "Administrative staff professionalism?", "Support staff helpfulness?", "Faculty accessibility (non-academic)?", "Fairness in staff dealings?", "Overall experience with staff?" ],
    'CANTEEN': [ "Food quality/taste?", "Variety of food options?", "Canteen hygiene?", "Value for money?", "Overall canteen satisfaction?" ],
    'LIBRARY': [ "Book/journal availability?", "Library staff helpfulness?", "Study environment comfort?", "Digital resource access?", "Overall effectiveness of library services?" ]
}


# --- UPDATED AI SUMMARIZATION VIEW (WITH RATINGS CONTEXT) ---
@login_required(login_url='core:login')
@user_passes_test(is_coordinator, login_url='core:landing_page')
@require_POST
def summarize_feedback_view(request):
    if not settings.GOOGLE_API_KEY:
        return JsonResponse({'error': 'AI service is not configured on the server.'}, status=503)
    
    try:
        data = json.loads(request.body)
        feedback_ids = data.get('feedback_ids')
        if not feedback_ids or not isinstance(feedback_ids, list):
            return HttpResponseBadRequest("Invalid or missing 'feedback_ids'.")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON format.")

    coordinator_department = request.user.profile.department
    feedback_entries = Feedback.objects.filter(id__in=feedback_ids, department_at_submission=coordinator_department)
    
    if feedback_entries.count() != len(feedback_ids):
        return JsonResponse({'error': 'Authorization error: You can only summarize feedback from your own department.'}, status=403)

    # --- Build the rich context string ---
    all_feedback_context = ""
    for entry in feedback_entries:
        context_str = f"Feedback Entry #{entry.id}:\n"
        context_str += f"- Category: {entry.category.get_name_display()}\n"
        
        # Add ratings with questions
        entry_questions = HARDCODED_CATEGORY_QUESTIONS.get(entry.category.name)
        if entry_questions:
            context_str += "- Ratings Given:\n"
            ratings = [entry.rating1, entry.rating2, entry.rating3, entry.rating4, entry.rating5]
            for i, rating_val in enumerate(ratings):
                question = entry_questions[i]
                if rating_val is not None:
                    rating_label = Feedback.RATING_DESCRIPTIVE_LABELS.get(rating_val, "N/A")
                    context_str += f'  - "{question}": {rating_label} ({rating_val}/5)\n'
                else:
                    context_str += f'  - "{question}": Not Rated\n'

        # Add text comment if it exists
        if entry.text_feedback and entry.text_feedback.strip():
            context_str += f"- Student's Comment: \"{entry.text_feedback.strip()}\"\n"
        
        # Add a separator for the AI
        all_feedback_context += context_str + "\n---\n\n"
    
    if not all_feedback_context.strip():
        return JsonResponse({'summary': 'No feedback content (neither text nor ratings) was found in the selected entries to summarize.'})

    try:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # New prompt
        prompt = (
            "You are an assistant for a university department coordinator. "
            "Your task is to analyze and summarize the following structured student feedback entries, which are separated by '---'. "
            "For each entry, you will be given the category, specific ratings for predefined questions, and sometimes a text comment. "
            "Your summary should be concise, in 3 to 5 key bullet points.(7 lines max) "
            "Synthesize information from BOTH the ratings and the text comments to identify patterns, common themes, and actionable insights. "
            "For example, if ratings for 'Clarity' are consistently low and comments mention 'fast lectures', connect these two points. "
            "Format your output using markdown for bullet points (e.g., Point 1).\n\n"
            "Here is the feedback:\n\n"
            f"{all_feedback_context}"
        )

        response = model.generate_content(prompt)
        
        summary_text = ""
        if response.parts:
            summary_text = ''.join(part.text for part in response.parts)
        else:
            summary_text = "The AI was unable to generate a summary for this content, possibly due to safety filters or other restrictions."
            print("Gemini response was blocked or empty. Full response:", response.prompt_feedback)

        return JsonResponse({'summary': summary_text})

    except Exception as e:
        print(f"Google Gemini API Error: {e}")
        return JsonResponse({'error': 'An error occurred with the AI service. Please check the server logs.'}, status=500)
    

    # --- NEW VIEW FOR ANALYTICS PAGE ---
@login_required(login_url='core:login')
@user_passes_test(is_coordinator, login_url='core:landing_page')
def analytics_view(request):
    coordinator_profile = request.user.profile
    department = coordinator_profile.department

    if not department:
        messages.error(request, "Your coordinator profile is not associated with a department.")
        return redirect('core:coordinator_dashboard')

    # Get all feedback for the department
    department_feedback = Feedback.objects.filter(department_at_submission=department)

    # 1. Overall Sentiment Distribution (for Pie Chart)
    sentiment_distribution = department_feedback.values('sentiment').annotate(count=Count('id')).order_by('sentiment')
    
    # Format for Chart.js
    pie_chart_data = {
        'labels': [],
        'data': [],
    }
    for item in sentiment_distribution:
        # We only want to chart valid sentiments
        if item['sentiment'] in ['POSITIVE', 'NEGATIVE', 'NEUTRAL']:
            pie_chart_data['labels'].append(item['sentiment'].capitalize())
            pie_chart_data['data'].append(item['count'])

    # 2. Sentiment by Category (for Bar Chart)
    # This query groups by category and then counts positive/negative sentiments within each group
    sentiment_by_category = (
        department_feedback
        .filter(sentiment__in=['POSITIVE', 'NEGATIVE']) # Only focus on positive/negative for this chart
        .values('category__name') # Group by the category's display name
        .annotate(
            positive_count=Count('id', filter=Q(sentiment='POSITIVE')),
            negative_count=Count('id', filter=Q(sentiment='NEGATIVE'))
        )
        .order_by('category__name')
    )
    
    # Format for Chart.js
    bar_chart_data = {
        'labels': [],
        'positive_data': [],
        'negative_data': [],
    }
    # We also need to get the human-readable category names
    category_names_map = dict(FeedbackCategory.CATEGORY_CHOICES) # Get {'TEACHING': 'Teaching', ...}
    for item in sentiment_by_category:
        display_name = category_names_map.get(item['category__name'], item['category__name'])
        bar_chart_data['labels'].append(display_name)
        bar_chart_data['positive_data'].append(item['positive_count'])
        bar_chart_data['negative_data'].append(item['negative_count'])

    context = {
        'department_name': department.name,
        'pie_chart_data': pie_chart_data,
        'bar_chart_data': bar_chart_data,
    }
    return render(request, 'core/analytics.html', context)
# --- END OF NEW VIEW ---