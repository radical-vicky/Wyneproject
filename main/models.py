# main/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import uuid

# ================================
# 1. PROFILE & USER MANAGEMENT
# ================================
# main/models.py - Update Profile model

class Profile(models.Model):
    """Extended user profile with all personal and service details"""
    
    GENDER_CHOICES = [
        ('Female', 'Female'),
        ('Male', 'Male'),
        ('Other', 'Other'),
    ]
    
    SEXUAL_ORIENTATION_CHOICES = [
        ('Bisexual', 'Bisexual'),
        ('Straight', 'Straight'),
        ('Gay', 'Gay'),
        ('Lesbian', 'Lesbian'),
        ('Other', 'Other'),
    ]
    
    # Core relationship
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Contact Information
    phone_number = models.CharField(max_length=20, unique=True, help_text="Primary contact number")
    whatsapp_number = models.CharField(max_length=20, blank=True, default='')
    
    # Personal Details - ADD DEFAULT VALUES
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='Other')
    sexual_orientation = models.CharField(max_length=20, choices=SEXUAL_ORIENTATION_CHOICES, default='Other')
    age = models.IntegerField(default=18)  # ADD DEFAULT
    nationality = models.CharField(max_length=100, default='Kenyan')
    county = models.CharField(max_length=100, default='Nairobi')
    city_town = models.CharField(max_length=100, default='Nairobi')
    location = models.TextField(help_text="Detailed location/CBD information", default='Nairobi CBD')
    
    # Service Information
    services_offered = models.TextField(
        help_text="Services separated by commas: Dinner Date, Travel Companion, etc.",
        default='Dinner Date'
    )
    hourly_rate_incall = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Incall rate per hour"
    )
    hourly_rate_outcall = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Outcall rate per hour"
    )
    
    # Status & Verification
    is_vip = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    
    # Statistics
    total_views = models.IntegerField(default=0)
    total_calls = models.IntegerField(default=0)
    total_bookings = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_vip', '-last_active']
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.username} - {self.city_town} ({'VIP' if self.is_vip else 'Standard'})"
    
    def get_services_list(self):
        """Convert services string to list"""
        return [s.strip() for s in self.services_offered.split(',') if s.strip()]
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create user profile, wallet, and settings when a new user is created
    """
    if created:
        # Create Profile with default values
        Profile.objects.create(
            user=instance,
            phone_number=f"0700000000{instance.id}",
            gender='Other',
            sexual_orientation='Other',
            age=25,
            nationality='Kenyan',
            county='Nairobi',
            city_town='Nairobi',
            location='Nairobi CBD',
            services_offered='Dinner Date'
        )
        
        # Create Wallet
        Wallet.objects.create(user=instance)
        
        # Create User Settings
        UserSetting.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save related models when user is saved
    """
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # If profile doesn't exist, create it
        Profile.objects.create(
            user=instance,
            phone_number=f"0700000000{instance.id}",
            gender='Other',
            sexual_orientation='Other',
            age=25,
            nationality='Kenyan',
            county='Nairobi',
            city_town='Nairobi',
            location='Nairobi CBD',
            services_offered='Dinner Date'
        )
# ================================
# 2. MEDIA MANAGEMENT
# ================================

class Photo(models.Model):
    """User uploaded photos"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='photos/%Y/%m/%d/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', '-uploaded_at']
    
    def __str__(self):
        return f"Photo: {self.profile.user.username}"

class Video(models.Model):
    """User uploaded videos with view tracking"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='videos')
    video_file = models.FileField(upload_to='videos/%Y/%m/%d/')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True)
    
    # Statistics
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)

    @property
    def likes_count(self):
        return self.video_likes.count()
    
    # Metadata
    duration = models.IntegerField(help_text="Duration in seconds", default=0)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.profile.user.username} ({self.views} views)"
    
    def get_duration_display(self):
        """Convert seconds to MM:SS format"""
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"
    
    

# ================================
# 3. SOCIAL & POSTS
# ================================

class Post(models.Model):
    """User posts (text, image, or video)"""
    POST_TYPES = [
        ('text', 'Text Post'),
        ('image', 'Image Post'),
        ('video', 'Video Post'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default='text')
    
    # Media fields (optional based on post_type)
    image = models.ImageField(upload_to='posts/images/', null=True, blank=True)
    video = models.FileField(upload_to='posts/videos/', null=True, blank=True)
    
    # Visibility & Status
    is_archived = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    # Statistics
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    
    # Location
    location = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'user']),
            models.Index(fields=['is_archived']),
        ]
    
    def __str__(self):
        return f"Post #{self.id} by {self.user.username}"
    
    def get_absolute_url(self):
        return f"/post/{self.id}/"
    

class VideoComment(models.Model):
    """Comments on videos"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.video.title}"

class PostInteraction(models.Model):
    """Track likes, saves, shares for posts"""
    INTERACTION_TYPES = [
        ('like', 'Like'),
        ('save', 'Save'),
        ('share', 'Share'),
        ('report', 'Report'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post', 'interaction_type']
        verbose_name = "Post Interaction"
        verbose_name_plural = "Post Interactions"
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type}d post #{self.post.id}"

class Comment(models.Model):
    """Comments on posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on post #{self.post.id}"

# ================================
# 4. MESSAGING & COMMUNICATION
# ================================

class Conversation(models.Model):
    """Chat conversation between users"""
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message = models.TextField(blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        participant_names = [p.username for p in self.participants.all()[:3]]
        return f"Conversation: {', '.join(participant_names)}"
    
    def update_last_message(self, message):
        self.last_message = message[:100]  # Store first 100 chars
        self.last_message_at = timezone.now()
        self.save()

class Message(models.Model):
    """Individual messages in conversations"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('call', 'Call Log'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    
    # Media fields
    media_file = models.FileField(upload_to='messages/media/', null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    is_saved = models.BooleanField(default=False, help_text="Saved message")
    
    # Timestamps
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['conversation', 'sent_at']),
            models.Index(fields=['sender', 'sent_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username}: {self.content[:50]}..."
    
    def save(self, *args, **kwargs):
        # Update conversation's last message
        super().save(*args, **kwargs)
        self.conversation.update_last_message(self.content)

class Contact(models.Model):
    """User's contact list"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    contact_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_of')
    nickname = models.CharField(max_length=100, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'contact_user']
        ordering = ['-is_favorite', 'contact_user__username']
    
    def __str__(self):
        return f"{self.user.username} → {self.contact_user.username}"

class CallLog(models.Model):
    """Audio/video call history"""
    CALL_TYPES = [
        ('audio', 'Audio Call'),
        ('video', 'Video Call'),
    ]
    
    CALL_STATUS = [
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
    ]
    
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_calls')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_calls')
    call_type = models.CharField(max_length=10, choices=CALL_TYPES)
    status = models.CharField(max_length=10, choices=CALL_STATUS)
    duration = models.IntegerField(default=0, help_text="Duration in seconds")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.caller.username} → {self.receiver.username} ({self.call_type}, {self.duration}s)"

# ================================
# 5. WALLET & PAYMENTS (M-PESA)
# ================================

class Wallet(models.Model):
    """User wallet for financial transactions"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    mpesa_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Wallet for {self.user.username} - KES {self.balance}"
    
    def deposit(self, amount):
        """Deposit to wallet"""
        self.balance += amount
        self.save()
    
    def withdraw(self, amount):
        """Withdraw from wallet"""
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False

class Transaction(models.Model):
    """Financial transactions"""
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('commission', 'Platform Commission'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Core transaction info
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # M-Pesa integration
    mpesa_receipt = models.CharField(max_length=50, blank=True, unique=True)
    mpesa_phone = models.CharField(max_length=20, blank=True)
    mpesa_checkout_id = models.CharField(max_length=100, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True, help_text="Internal reference ID")
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['mpesa_receipt']),
        ]
    
    def __str__(self):
        return f"TX-{self.id}: {self.transaction_type} - KES {self.amount}"

class ServiceBooking(models.Model):
    """Service appointments/booking system"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    LOCATION_TYPES = [
        ('incall', 'Incall'),
        ('outcall', 'Outcall'),
    ]
    
    # Booking parties
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_made')
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_received')
    
    # Service details
    service_type = models.CharField(max_length=100)
    duration_hours = models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Location
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)
    meeting_location = models.TextField(blank=True)
    
    # Timestamps
    booking_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Payment reference
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-booking_date']
    
    def __str__(self):
        return f"Booking #{self.id}: {self.client.username} → {self.service_provider.username}"
    
    def complete_booking(self):
        """Mark booking as completed"""
        self.status = 'completed'
        self.save()

# ================================
# 6. DISCOVERY & FEATURES
# ================================

class SavedSearch(models.Model):
    """Saved search queries for quick access"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    search_query = models.CharField(max_length=255)
    filters = models.JSONField(default=dict, blank=True)  # Store filter preferences
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Search: {self.search_query[:50]}..."

class Invitation(models.Model):
    """Friend/invitation system"""
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invitee_email = models.EmailField()
    invitee_phone = models.CharField(max_length=20, blank=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('expired', 'Expired')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Invitation from {self.inviter.username} to {self.invitee_email}"

class UserSetting(models.Model):
    """User preferences and settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[('public', 'Public'), ('contacts', 'Contacts Only'), ('private', 'Private')],
        default='public'
    )
    show_online_status = models.BooleanField(default=True)
    allow_calls = models.BooleanField(default=True)
    
    # App preferences
    theme = models.CharField(max_length=20, default='light', choices=[('light', 'Light'), ('dark', 'Dark')])
    language = models.CharField(max_length=10, default='en')
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Settings for {self.user.username}"
    
class VideoLike(models.Model):
    """Track which users liked which videos"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='video_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'video']
    
    def __str__(self):
        return f"{self.user.username} liked {self.video.title}"