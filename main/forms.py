from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import (
    Profile, Photo, Video, Post, Comment, Contact, 
    Message, Conversation, CallLog, Wallet, Transaction,
    ServiceBooking, SavedSearch, Invitation, UserSetting
)

# ==================== AUTHENTICATION FORMS ====================

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create profile with phone number
            user.profile.phone_number = self.cleaned_data['phone_number']
            user.profile.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

# ==================== PROFILE FORMS ====================

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'phone_number', 'whatsapp_number', 'gender', 'sexual_orientation',
            'age', 'nationality', 'county', 'city_town', 'location',
            'services_offered', 'hourly_rate_incall', 'hourly_rate_outcall',
            'is_available'
        ]
        widgets = {
            'services_offered': forms.Textarea(attrs={'rows': 3}),
            'location': forms.Textarea(attrs={'rows': 2}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'phone_number', 'whatsapp_number', 'gender', 'sexual_orientation',
            'age', 'nationality', 'county', 'city_town', 'location',
            'services_offered', 'hourly_rate_incall', 'hourly_rate_outcall',
            'is_available'
        ]
        widgets = {
            'services_offered': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Dinner Date, Travel Companion, Lesbian Show, etc.'}),
            'location': forms.Textarea(attrs={'rows': 2}),
        }

# ==================== MEDIA FORMS ====================

class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image', 'caption', 'is_primary']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Add a caption...'}),
        }

class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['video_file', 'title', 'description', 'thumbnail']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

# ==================== POST FORMS ====================

class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'post_type', 'image', 'video', 'location']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': "What's on your mind?",
                'class': 'form-control'
            }),
            'post_type': forms.Select(attrs={'class': 'form-select'}),
        }

class PostUpdateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image', 'video', 'location', 'is_archived', 'is_pinned']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Add a comment...',
                'class': 'form-control'
            }),
        }

# ==================== MESSAGING FORMS ====================

class ContactAddForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    
    class Meta:
        model = Contact
        fields = ['nickname']
    
    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("User does not exist")
        return username

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'message_type', 'media_file']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Type your message...',
                'class': 'form-control'
            }),
            'message_type': forms.HiddenInput(),
        }

class ConversationCreateForm(forms.Form):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        required=True
    )
    initial_message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Start the conversation...'}),
        required=False
    )

# ==================== PAYMENT FORMS ====================

class DepositForm(forms.ModelForm):
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=10,
        help_text="Minimum deposit: KES 10"
    )
    phone_number = forms.CharField(
        max_length=20,
        help_text="M-Pesa registered phone number"
    )
    
    class Meta:
        model = Transaction
        fields = ['amount', 'phone_number']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class WithdrawalForm(forms.ModelForm):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=100,
        help_text="Minimum withdrawal: KES 100"
    )
    
    class Meta:
        model = Transaction
        fields = ['amount']

class ServiceBookingForm(forms.ModelForm):
    service_provider_username = forms.CharField(max_length=150, required=True)
    
    class Meta:
        model = ServiceBooking
        fields = ['service_type', 'duration_hours', 'location_type', 'meeting_location', 'booking_date']
        widgets = {
            'booking_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'meeting_location': forms.Textarea(attrs={'rows': 2}),
        }
    
    def clean_service_provider_username(self):
        username = self.cleaned_data['service_provider_username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("Service provider does not exist")
        return username

# ==================== DISCOVERY & SETTINGS FORMS ====================

class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search profiles, posts, services...',
            'class': 'form-control'
        })
    )
    gender = forms.ChoiceField(
        choices=[('', 'Any')] + Profile.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    county = forms.CharField(max_length=100, required=False)
    min_age = forms.IntegerField(min_value=18, max_value=100, required=False)
    max_age = forms.IntegerField(min_value=18, max_value=100, required=False)
    services = forms.CharField(max_length=255, required=False)
    is_vip = forms.BooleanField(required=False)

class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ['invitee_email', 'invitee_phone']
        widgets = {
            'invitee_email': forms.EmailInput(attrs={'placeholder': 'friend@example.com'}),
            'invitee_phone': forms.TextInput(attrs={'placeholder': '07XXXXXXXX'}),
        }

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSetting
        fields = [
            'email_notifications', 'push_notifications', 'sms_notifications',
            'profile_visibility', 'show_online_status', 'allow_calls',
            'theme', 'language'
        ]
        widgets = {
            'profile_visibility': forms.Select(attrs={'class': 'form-select'}),
            'theme': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
        }

# ==================== CALL FORMS ====================

class CallInitiateForm(forms.Form):
    CALL_TYPE_CHOICES = [
        ('audio', 'Audio Call'),
        ('video', 'Video Call'),
    ]
    
    receiver_username = forms.CharField(max_length=150, required=True)
    call_type = forms.ChoiceField(choices=CALL_TYPE_CHOICES, widget=forms.RadioSelect)
    
    def clean_receiver_username(self):
        username = self.cleaned_data['receiver_username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("User does not exist")
        return username