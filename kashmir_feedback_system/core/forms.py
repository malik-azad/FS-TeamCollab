# core/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Profile, Department, Feedback, FeedbackCategory 

# --- Signup Form (Remains Unchanged from previous stable version) ---
class SignupForm(forms.ModelForm):
    enrollment_id = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'placeholder': 'Enrollment ID (This will be your login ID)'})
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by('name'),
        empty_label="Select Department",
        widget=forms.Select()
    )
    batch_start_year = forms.ChoiceField(
        choices=[('', 'Select Batch Start Year')] + Profile.BATCH_YEAR_CHOICES,
        widget=forms.Select()
    )
    full_name = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'placeholder': 'Full Name (Optional)'}))

    class Meta:
        model = Profile
        fields = ['full_name', 'enrollment_no', 'department', 'batch_start_year', 'profile_photo']
        widgets = {
            'profile_photo': forms.ClearableFileInput(),
            'enrollment_no': forms.HiddenInput(), 
        }

    field_order = ['enrollment_id', 'email', 'password', 'full_name', 'department', 'batch_start_year', 'profile_photo']

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
             self.fields['profile_photo'].widget.attrs.update({'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-custom-blue-light file:text-custom-blue hover:file:bg-custom-blue-darker'})

    def clean_enrollment_id(self):
        enrollment_id = self.cleaned_data.get('enrollment_id')
        if User.objects.filter(username=enrollment_id).exists():
            raise forms.ValidationError("This Enrollment ID is already registered. Please try to login.")
        return enrollment_id

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['enrollment_id'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )
        full_name_val = self.cleaned_data.get('full_name')
        if full_name_val:
            parts = full_name_val.split(' ', 1)
            user.first_name = parts[0]
            if len(parts) > 1:
                user.last_name = parts[1]
        user.save()

        profile = super().save(commit=False)
        profile.user = user
        profile.role = 'STUDENT'
        profile.enrollment_no = self.cleaned_data['enrollment_id']
        
        if commit:
            profile.save()
        return profile

# --- Give Feedback Form ---
class GiveFeedbackForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=FeedbackCategory.objects.all().order_by('name'),
        empty_label="Select Feedback Category",
        widget=forms.Select() # Basic widget, styling primarily in template/JS if needed
    )
    
    

    input_method = forms.ChoiceField(
        choices=Feedback.INPUT_METHOD_CHOICES,
        widget=forms.RadioSelect(), # Basic widget
        initial='TEXT'
    )

    rating1 = forms.TypedChoiceField(choices=Feedback.RATING_CHOICES_NUMERIC, coerce=int, empty_value=None, widget=forms.RadioSelect, required=False)
    rating2 = forms.TypedChoiceField(choices=Feedback.RATING_CHOICES_NUMERIC, coerce=int, empty_value=None, widget=forms.RadioSelect, required=False)
    rating3 = forms.TypedChoiceField(choices=Feedback.RATING_CHOICES_NUMERIC, coerce=int, empty_value=None, widget=forms.RadioSelect, required=False)
    rating4 = forms.TypedChoiceField(choices=Feedback.RATING_CHOICES_NUMERIC, coerce=int, empty_value=None, widget=forms.RadioSelect, required=False)
    rating5 = forms.TypedChoiceField(choices=Feedback.RATING_CHOICES_NUMERIC, coerce=int, empty_value=None, widget=forms.RadioSelect, required=False)
    
    is_anonymous = forms.BooleanField(required=False, widget=forms.CheckboxInput()) # Basic widget

    class Meta:
        model = Feedback
        fields = [
            'category', # REMOVED 'subject' from this list
            'input_method', 'text_feedback', 'audio_feedback',
            'rating1', 'rating2', 'rating3', 'rating4', 'rating5',
            'is_anonymous'
        ]
        widgets = {
            'text_feedback': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Type your detailed feedback here...'}),
            'audio_feedback': forms.ClearableFileInput(), 
        }

    def __init__(self, *args, **kwargs):
        # user argument is still accepted but not used for subject filtering anymore
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)

        # Apply common Tailwind classes or rely on template for more detailed styling
        common_input_classes = 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-custom-blue focus:bg-white focus:outline-none text-sm text-gray-700 placeholder-gray-400'
        self.fields['category'].widget.attrs.update({'class': common_input_classes})
     
        
        # For input_method (RadioSelect), styling individual radios is best in template/JS
        # For text_feedback, placeholder is set in Meta.widgets, class can be added here or in template
        self.fields['text_feedback'].widget.attrs.update({'class': common_input_classes})
        
        # For audio_feedback (ClearableFileInput)
        self.fields['audio_feedback'].widget.attrs.update({'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-custom-blue-light file:text-custom-blue hover:file:bg-custom-blue-darker'})
        
        # For rating fields (RadioSelect), a wrapper class can be useful if Django creates one
        # The actual radio buttons are styled by JS/CSS in the template
        for i in range(1, 6):
            field_name = f'rating{i}'
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'rating-radio-group-wrapper'}) # For potential wrapper
        
        # For is_anonymous (CheckboxInput)
        self.fields['is_anonymous'].widget.attrs.update({'class': 'h-4 w-4 text-custom-blue focus:ring-custom-blue-dark border-gray-300 rounded'})


    def clean(self):
        cleaned_data = super().clean()
        

        input_method = cleaned_data.get('input_method')
        text_feedback = cleaned_data.get('text_feedback', '') 
        audio_feedback = cleaned_data.get('audio_feedback')   

        has_text = bool(text_feedback.strip()) 
        has_audio = bool(audio_feedback)
        # rating fields will be None if not selected, due to TypedChoiceField's empty_value=None
        has_any_rating = any(cleaned_data.get(f'rating{i}') is not None for i in range(1, 6))

        if input_method == 'TEXT':
            if not has_text and not has_any_rating: 
                self.add_error('text_feedback', 'Please provide detailed feedback or answer rating questions when selecting Text Input.')
        elif input_method == 'AUDIO':
            if not has_audio and not has_any_rating: 
                self.add_error('audio_feedback', 'Please upload/record audio or answer rating questions when selecting Audio Recording.')
        
        if not has_text and not has_audio and not has_any_rating:
            self.add_error(None, "Please provide at least one form of feedback: either text, an audio recording, or at least one rating.")
            
        return cleaned_data