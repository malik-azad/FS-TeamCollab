# core/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import Profile, Department, Feedback, FeedbackCategory 

# -------------------------------
# SignupForm: Handles user signup
# -------------------------------
class SignupForm(forms.ModelForm):
    # Enrollment ID field (used as login ID)
    enrollment_id = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'placeholder': 'Enrollment ID (This will be your login ID)'})
    )
    # Email field
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    # Password field
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    # Department selection
    department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by('name'),
        empty_label="Select Department",
        widget=forms.Select()
    )
    # Batch start year selection
    batch_start_year = forms.ChoiceField(
        choices=[('', 'Select Batch Start Year')] + Profile.BATCH_YEAR_CHOICES,
        widget=forms.Select()
    )
    # Optional full name field
    full_name = forms.CharField(
        max_length=255, 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Full Name (Optional)'})
    )

    class Meta:
        model = Profile
        fields = ['full_name', 'enrollment_no', 'department', 'batch_start_year', 'profile_photo']
        widgets = {
            'profile_photo': forms.ClearableFileInput(),
            'enrollment_no': forms.HiddenInput(), 
        }

    # Initialization: Add CSS classes to widgets for styling
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-custom-blue focus:bg-white focus:outline-none text-sm text-gray-700 placeholder-gray-400'
        select_classes = input_classes
        self.fields['enrollment_id'].widget.attrs.update({'class': input_classes})
        self.fields['email'].widget.attrs.update({'class': input_classes})
        self.fields['password'].widget.attrs.update({'class': input_classes})
        if 'full_name' in self.fields:
            self.fields['full_name'].widget.attrs.update({'class': input_classes})
        self.fields['department'].widget.attrs.update({'class': select_classes})
        self.fields['batch_start_year'].widget.attrs.update({'class': select_classes})
        if 'profile_photo' in self.fields and self.fields['profile_photo']:
            self.fields['profile_photo'].widget.attrs.update({
                'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-custom-blue-light file:text-custom-blue hover:file:bg-custom-blue-darker'
            })

    # Validate enrollment_id: must be unique
    def clean_enrollment_id(self):
        enrollment_id = self.cleaned_data.get('enrollment_id')
        if User.objects.filter(username=enrollment_id).exists():
            raise forms.ValidationError("This Enrollment ID is already registered. Please try to login.")
        return enrollment_id

    # Validate email: must be unique
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

    # Save method: creates User and Profile
    def save(self, commit=True):
        # Create user with is_active=False
        user = User.objects.create_user(
            username=self.cleaned_data['enrollment_id'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            is_active=False # User cannot log in until this is set to True by a coordinator
        )
        # Set first and last name if provided
        full_name_val = self.cleaned_data.get('full_name')
        if full_name_val:
            parts = full_name_val.split(' ', 1)
            user.first_name = parts[0]
            if len(parts) > 1:
                user.last_name = parts[1]
        # Save user
        user.save()

        # Create profile
        profile = super().save(commit=False)
        profile.user = user
        profile.role = 'STUDENT'
        profile.enrollment_no = self.cleaned_data['enrollment_id']
        # The profile's is_verified field defaults to False, which is correct
        
        if commit:
            profile.save()
        return profile

# ------------------------------------------------
# GiveFeedbackForm: Handles giving feedback
# ------------------------------------------------
class GiveFeedbackForm(forms.ModelForm):
    # Feedback category selection
    category = forms.ModelChoiceField(
        queryset=FeedbackCategory.objects.all().order_by('name'),
        empty_label="Select Feedback Category",
        widget=forms.Select()
    )
    # Input method: text or audio
    input_method = forms.ChoiceField(
        choices=Feedback.INPUT_METHOD_CHOICES,
        widget=forms.RadioSelect(),
        initial='TEXT'
    )
    # Numeric ratings (1-5)
    rating1 = forms.TypedChoiceField(
        choices=Feedback.RATING_CHOICES_NUMERIC,
        coerce=int,
        empty_value=None,
        widget=forms.RadioSelect,
        required=False
    )
    rating2 = forms.TypedChoiceField(
        choices=Feedback.RATING_CHOICES_NUMERIC,
        coerce=int,
        empty_value=None,
        widget=forms.RadioSelect,
        required=False
    )
    rating3 = forms.TypedChoiceField(
        choices=Feedback.RATING_CHOICES_NUMERIC,
        coerce=int,
        empty_value=None,
        widget=forms.RadioSelect,
        required=False
    )
    rating4 = forms.TypedChoiceField(
        choices=Feedback.RATING_CHOICES_NUMERIC,
        coerce=int,
        empty_value=None,
        widget=forms.RadioSelect,
        required=False
    )
    rating5 = forms.TypedChoiceField(
        choices=Feedback.RATING_CHOICES_NUMERIC,
        coerce=int,
        empty_value=None,
        widget=forms.RadioSelect,
        required=False
    )
    # Anonymous feedback option
    is_anonymous = forms.BooleanField(required=False, widget=forms.CheckboxInput())

    class Meta:
        model = Feedback
        fields = [
            'category', 'input_method', 'text_feedback', 'audio_feedback',
            'rating1', 'rating2', 'rating3', 'rating4', 'rating5', 'is_anonymous'
        ]
        widgets = {
            'text_feedback': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Type your detailed feedback here...'}),
            'audio_feedback': forms.ClearableFileInput(),
        }

    # Initialization: Add CSS classes to widgets for styling
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        common_input_classes = 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-custom-blue focus:bg-white focus:outline-none text-sm text-gray-700 placeholder-gray-400'
        self.fields['category'].widget.attrs.update({'class': common_input_classes})
        self.fields['text_feedback'].widget.attrs.update({'class': common_input_classes})
        self.fields['audio_feedback'].widget.attrs.update({
            'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-custom-blue-light file:text-custom-blue hover:file:bg-custom-blue-darker'
        })
        self.fields['is_anonymous'].widget.attrs.update({
            'class': 'h-4 w-4 text-custom-blue focus:ring-custom-blue-dark border-gray-300 rounded'
        })
        self.fields['input_method'].widget.attrs.update({'class': 'input-method-radio-group'})
        for i in range(1, 6):
            field_name = f'rating{i}'
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'rating-radio-group-wrapper'})

    # Clean method: Ensure at least one form of feedback is provided
    def clean(self):
        cleaned_data = super().clean()
        input_method = cleaned_data.get('input_method')
        text_feedback = cleaned_data.get('text_feedback', '')
        audio_feedback = cleaned_data.get('audio_feedback')
        has_text = bool(text_feedback.strip())
        has_audio = bool(audio_feedback)
        has_any_rating = any(cleaned_data.get(f'rating{i}') is not None for i in range(1, 6))
        if input_method == 'TEXT' and not has_text and not has_any_rating:
            self.add_error('text_feedback', 'Please provide detailed feedback or answer rating questions when selecting Text Input.')
        elif input_method == 'AUDIO' and not has_audio and not has_any_rating:
            self.add_error('audio_feedback', 'Please upload/record audio or answer rating questions when selecting Audio Recording.')
        if not has_text and not has_audio and not has_any_rating:
            self.add_error(None, "Please provide at least one form of feedback: either text, an audio recording, or at least one rating.")
        return cleaned_data

# ------------------------------------------------
# EditProfileForm: Handles editing user profile
# ------------------------------------------------
class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'profile_photo']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Your Full Name'}),
            'profile_photo': forms.ClearableFileInput(),
        }

    # Initialization: Add CSS classes to widgets for styling
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-custom-blue focus:bg-white focus:outline-none text-sm text-gray-700 placeholder-gray-400'
        if 'full_name' in self.fields:
            self.fields['full_name'].widget.attrs.update({'class': input_classes})
        if 'profile_photo' in self.fields and self.fields['profile_photo']:
            self.fields['profile_photo'].widget.attrs.update({
                'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-custom-blue-light file:text-custom-blue hover:file:bg-custom-blue-darker'
            })