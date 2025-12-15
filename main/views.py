from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Sum, Avg, F  # Add F to imports
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json
# Add these imports at the top
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
# Add these imports at the top if not already there
from django.views.decorators.http import require_POST, require_http_methods
import json
from .models import VideoLike  # Add VideoLike to imports




# Allauth imports
from allauth.account.decorators import verified_email_required

from .models import *
from .forms import *


def get_user_profile(user):
    """Safe method to get or create user profile"""
    try:
        return user.profile
    except Profile.DoesNotExist:
        # Create profile with default values
        profile = Profile.objects.create(
            user=user,
            phone_number=f"2547{user.id:08d}",  # Kenyan format
            gender='Other',
            sexual_orientation='Other',
            age=25,
            nationality='Kenyan',
            county='Nairobi',
            city_town='Nairobi',
            location='Nairobi CBD',
            services_offered='Dinner Date'
        )
        
        # Also create wallet and settings if they don't exist
        Wallet.objects.get_or_create(user=user)
        UserSetting.objects.get_or_create(user=user)
        
        return profile

# ==================== DASHBOARD VIEWS ====================
@login_required
def dashboard_view(request):
    user = request.user
    
    # Get user profile
    profile = get_user_profile(user)
    
    # Get unread messages count
    unread_messages_count = Message.objects.filter(
        conversation__participants=user,
        is_read=False
    ).exclude(sender=user).count()
    
    # Get recent activity
    recent_posts = Post.objects.filter(user=user).order_by('-created_at')[:5]
    recent_messages = Message.objects.filter(
        Q(conversation__participants=user) & ~Q(sender=user)
    ).order_by('-sent_at')[:5]
    
    # Get pending bookings
    pending_bookings = ServiceBooking.objects.filter(
        Q(client=user) | Q(service_provider=user),
        status='pending'
    ).order_by('-created_at')[:5]
    
    # Get wallet balance
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    # Statistics
    stats = {
        'total_posts': Post.objects.filter(user=user).count(),
        'total_contacts': Contact.objects.filter(user=user).count(),
        'total_bookings': ServiceBooking.objects.filter(
            Q(client=user) | Q(service_provider=user)
        ).count(),
        'wallet_balance': wallet.balance,
    }
    
    # Get notifications count
    notifications = {
        'unread_messages': unread_messages_count,
        'pending_bookings': pending_bookings.count(),
        'pending_transactions': Transaction.objects.filter(
            user=user,
            status='pending'
        ).count(),
    }
    
    context = {
        'user': user,
        'profile': profile,
        'recent_posts': recent_posts,
        'recent_messages': recent_messages,
        'pending_bookings': pending_bookings,
        'stats': stats,
        'wallet': wallet,
        'notifications': notifications,
        'unread_messages_count': unread_messages_count,  # Add this
    }
    
    return render(request, 'dashboard/dashboard.html', context)


def get_user_profile(user):
    """Safe method to get or create user profile"""
    try:
        return user.profile
    except Profile.DoesNotExist:
        # Create profile with default values
        profile = Profile.objects.create(
            user=user,
            phone_number=f"0700000000{user.id}",
            gender='Other',
            sexual_orientation='Other',
            age=25,
            nationality='Kenyan',
            county='Nairobi',
            city_town='Nairobi',
            location='Nairobi CBD',
            services_offered='Dinner Date'
        )
        
        # Also create wallet and settings if they don't exist
        Wallet.objects.get_or_create(user=user)
        UserSetting.objects.get_or_create(user=user)
        
        return profile


@login_required
def profile_view(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    # Use safe method to get profile
    profile = get_user_profile(user)
    
    # Increment profile views (for non-owners)
    if request.user != user:
        profile.total_views += 1
        profile.save()
    
    # Get primary photo with optimized query
    try:
        primary_photo = Photo.objects.filter(
            profile=profile,
            is_primary=True
        ).select_related('profile').first()
        
        # If no primary photo, get the most recent photo
        if not primary_photo:
            primary_photo = Photo.objects.filter(
                profile=profile
            ).select_related('profile').order_by('-uploaded_at').first()
            
            # If we found a photo but it's not marked as primary, mark it
            if primary_photo:
                primary_photo.is_primary = True
                primary_photo.save()
    except Exception as e:
        primary_photo = None
    
    # Get user's photos with optimization
    photos = Photo.objects.filter(profile=profile).select_related('profile').order_by('-is_primary', '-uploaded_at')
    
    # Get user's videos
    videos = Video.objects.filter(profile=profile).order_by('-uploaded_at')
    
    # Get user's posts with optimization - FIXED: Removed 'likes' from prefetch_related
    posts = Post.objects.filter(user=user).select_related('user').annotate(
    likes_count=Count('interactions', filter=Q(interactions__interaction_type='like'))
).prefetch_related(
    'comments__user__profile'
).order_by('-created_at')[:10]
    # Get services as list
    services_list = profile.get_services_list()
    
    # Check if user can contact this profile
    can_contact = True
    is_contact = False
    
    if request.user != user:
        # Check if contact exists (blocked or not)
        contact = Contact.objects.filter(
            user=request.user,
            contact_user=user
        ).first()
        
        if contact:
            can_contact = not contact.is_blocked
            is_contact = not contact.is_blocked
    
    # Initialize stats with default values
    rating_stats = {'avg_rating': profile.rating, 'total_reviews': 0}
    booking_stats = {'total_bookings': profile.total_bookings, 'total_earnings': 0}
    call_stats = {'total_calls': profile.total_calls, 'total_duration': 0}
    
    # Try to get booking stats if bookings app exists
    try:
        booking_stats = ServiceBooking.objects.filter(
            service_provider=user,
            status__in=['completed', 'confirmed']
        ).aggregate(
            total_bookings=Count('id'),
            total_earnings=Sum('total_amount')
        )
        
        # Update profile booking count if different
        if profile.total_bookings != (booking_stats['total_bookings'] or 0):
            profile.total_bookings = booking_stats['total_bookings'] or 0
            profile.save()
    except Exception as e:
        # Use profile data
        booking_stats = {
            'total_bookings': profile.total_bookings or 0,
            'total_earnings': 0
        }
    
    # Try to get call stats if calls app exists
    try:
        call_stats = CallLog.objects.filter(
            receiver=user,
            status='completed'
        ).aggregate(
            total_calls=Count('id'),
            total_duration=Sum('duration')
        )
        
        # Update profile call count if different
        if profile.total_calls != (call_stats['total_calls'] or 0):
            profile.total_calls = call_stats['total_calls'] or 0
            profile.save()
    except Exception as e:
        # Use profile data
        call_stats = {
            'total_calls': profile.total_calls or 0,
            'total_duration': 0
        }
    
    # Check online status - FIXED: Use last_active instead of last_seen
    profile.is_online = profile.last_active >= timezone.now() - timedelta(minutes=5)
    profile.save()  # Save the online status update
    
    # Get verification status
    verification_status = {
        'is_verified': profile.is_verified,
        'verification_badge': 'Verified' if profile.is_verified else 'Unverified',
    }
    
    context = {
        'profile_user': user,
        'profile': profile,
        'primary_photo': primary_photo,
        'photos': photos,
        'videos': videos,
        'posts': posts,
        'services_list': services_list,
        'is_owner': request.user == user,
        'can_contact': can_contact,
        'is_contact': is_contact,
        'rating_stats': rating_stats,
        'booking_stats': booking_stats,
        'call_stats': call_stats,
        'verification_status': verification_status,
        'now': timezone.now(),
        'debug': False,  # Set to False for production
    }
    
    # Add messages if any
    messages_list = messages.get_messages(request)
    if messages_list:
        context['messages'] = list(messages_list)
    
    return render(request, 'dashboard/profile.html', context)



def get_user_profile(user):
    """Safely get or create user profile"""
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = Profile.objects.create(
            user=user,
            username=user.username,
            email=user.email,
            # Set default values
            gender='',
            age=18,
            phone_number='',
            county='',
            city_town='',
            location='',
            services_offered='',
        )
    return profile

@login_required
def profile_edit_view(request):
    profile = request.user.profile
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    context = {
        'profile': profile,
        'form': form,  # Add the form to context
        'profile_form': ProfileUpdateForm(instance=profile),  # Add this too
    }
    
    return render(request, 'dashboard/profile_edit.html', context)


@login_required
def profile_upload_photo(request):
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.profile = request.user.profile
            
            # If this is set as primary, unset others
            if photo.is_primary:
                Photo.objects.filter(profile=request.user.profile).update(is_primary=False)
            
            photo.save()
            messages.success(request, 'Photo uploaded successfully!')
            return redirect('profile')
    else:
        form = PhotoUploadForm()
    
    return render(request, 'dashboard/upload_photo.html', {'form': form})

@login_required
def profile_upload_video(request):
    if request.method == 'POST':
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.profile = request.user.profile
            video.save()
            messages.success(request, 'Video uploaded successfully!')
            return redirect('profile')
    else:
        form = VideoUploadForm()
    
    return render(request, 'dashboard/upload_video.html', {'form': form})

# ==================== POST VIEWS ====================

@login_required
def post_create_view(request):
    if request.method == 'POST':
        form = PostCreateForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            
            # Determine post type if not specified
            if not post.post_type:
                if post.image:
                    post.post_type = 'image'
                elif post.video:
                    post.post_type = 'video'
                else:
                    post.post_type = 'text'
            
            post.save()
            messages.success(request, 'Post created successfully!')
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostCreateForm()
    
    return render(request, 'dashboard/post_create.html', {'form': form})

def post_detail_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Increment views
    if request.user != post.user:
        post.views += 1
        post.save()
    
    comments = Comment.objects.filter(post=post).order_by('created_at')
    comment_form = CommentForm()
    
    # Check if user has interacted with this post
    user_interactions = {}
    if request.user.is_authenticated:
        interactions = PostInteraction.objects.filter(user=request.user, post=post)
        user_interactions = {interaction.interaction_type: True for interaction in interactions}
    
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            
            post.comments_count += 1
            post.save()
            
            messages.success(request, 'Comment added!')
            return redirect('post_detail', post_id=post.id)
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'user_interactions': user_interactions,
    }
    
    return render(request, 'dashboard/post_detail.html', context)

@login_required
def post_interact_view(request, post_id, interaction_type):
    post = get_object_or_404(Post, id=post_id)
    
    if interaction_type not in ['like', 'save', 'share', 'report']:
        return JsonResponse({'error': 'Invalid interaction type'}, status=400)
    
    # Check if interaction already exists
    interaction, created = PostInteraction.objects.get_or_create(
        user=request.user,
        post=post,
        interaction_type=interaction_type
    )
    
    if not created:
        interaction.delete()
        is_active = False
    else:
        is_active = True
    
    # Update post stats
    if interaction_type == 'like':
        post.likes = post.likes + 1 if created else max(0, post.likes - 1)
        post.save()
    
    return JsonResponse({
        'success': True,
        'is_active': is_active,
        'likes_count': post.likes,
    })

@login_required
def post_archive_view(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.is_archived = not post.is_archived
    post.save()
    
    action = 'archived' if post.is_archived else 'unarchived'
    messages.success(request, f'Post {action} successfully!')
    return redirect('post_detail', post_id=post.id)

@login_required
def post_delete_view(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('profile')
    
    return render(request, 'dashboard/post_confirm_delete.html', {'post': post})

# ==================== MESSAGING VIEWS ====================

@login_required
def inbox_view(request):
    conversations = Conversation.objects.filter(participants=request.user).order_by('-last_message_at')
    
    # Get unread counts and last message
    for conversation in conversations:
        conversation.unread_count = Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=request.user).count()
        
        # Get other participant
        other_participant = conversation.participants.exclude(id=request.user.id).first()
        conversation.other_participant = other_participant
        conversation.other_profile = other_participant.profile if other_participant else None
    
    return render(request, 'dashboard/inbox.html', {'conversations': conversations})


@login_required
def conversation_view(request, conversation_id=None, username=None):
    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    elif username:
        other_user = get_object_or_404(User, username=username)
        # Check if contact is blocked
        blocked = Contact.objects.filter(
            user=request.user,
            contact_user=other_user,
            is_blocked=True
        ).exists()
        
        if blocked:
            messages.error(request, 'You have blocked this user.')
            return redirect('inbox')
        
        # Find or create conversation
        conversations = Conversation.objects.filter(participants=request.user).filter(participants=other_user)
        if conversations.exists():
            conversation = conversations.first()
        else:
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, other_user)
            conversation.save()
    else:
        return redirect('inbox')
    
    # Mark messages as read
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True, read_at=timezone.now())
    
    messages_list = Message.objects.filter(conversation=conversation).order_by('sent_at')
    
    # Get other user info
    other_user = conversation.participants.exclude(id=request.user.id).first()
    other_profile = other_user.profile if other_user else None
    
    # Handle form submission
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            
            # Determine message type based on file
            if 'media_file' in request.FILES:
                media_file = request.FILES['media_file']
                if media_file.content_type.startswith('image/'):
                    message.message_type = 'image'
                elif media_file.content_type.startswith('video/'):
                    message.message_type = 'video'
                elif media_file.content_type.startswith('audio/'):
                    message.message_type = 'audio'
                message.media_file = media_file
            
            message.save()
            
            # Return JSON response for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'message_type': message.message_type,
                        'media_url': message.media_file.url if message.media_file else None,
                        'sent_at': message.sent_at.isoformat(),
                        'sender': message.sender.username,
                        'is_read': message.is_read,
                    }
                })
            
            messages.success(request, 'Message sent!')
            return redirect('conversation', conversation_id=conversation.id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.as_json()
                }, status=400)
    else:
        form = MessageForm()
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'form': form,
        'other_user': other_user,
        'other_profile': other_profile,
        'now': timezone.now(),
    }
    
    # If AJAX request for initial load
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        messages_data = []
        for msg in messages_list:
            messages_data.append({
                'id': msg.id,
                'content': msg.content,
                'message_type': msg.message_type,
                'media_url': msg.media_file.url if msg.media_file else None,
                'sent_at': msg.sent_at.isoformat(),
                'sender': msg.sender.username,
                'is_read': msg.is_read,
            })
        
        return JsonResponse({
            'conversation_id': conversation.id,
            'messages': messages_data,
            'other_user': {
                'username': other_user.username,
                'is_online': other_profile.is_online if other_profile else False,
                'last_active': other_profile.last_active.isoformat() if other_profile else None,
            }
        })
    
    return render(request, 'dashboard/conversation.html', context)


@login_required
def conversation_delete_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    if request.method == 'POST':
        # Remove user from conversation participants
        conversation.participants.remove(request.user)
        
        # If no participants left, delete the conversation
        if conversation.participants.count() == 0:
            conversation.delete()
        
        messages.success(request, 'Conversation deleted successfully!')
        return redirect('inbox')
    
    other_user = conversation.participants.exclude(id=request.user.id).first()
    
    return render(request, 'dashboard/conversation_confirm_delete.html', {
        'conversation': conversation,
        'other_user': other_user,
    })

@login_required
def contacts_view(request):
    contacts = Contact.objects.filter(user=request.user).order_by('-is_favorite', 'contact_user__username')
    form = ContactAddForm()
    
    if request.method == 'POST':
        form = ContactAddForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            contact_user = User.objects.get(username=username)
            
            # Check if trying to add self
            if contact_user == request.user:
                messages.error(request, 'You cannot add yourself as a contact.')
                return redirect('contacts')
            
            # Check if already in contacts
            if Contact.objects.filter(user=request.user, contact_user=contact_user).exists():
                messages.warning(request, f'{username} is already in your contacts.')
            else:
                contact = form.save(commit=False)
                contact.user = request.user
                contact.contact_user = contact_user
                contact.save()
                messages.success(request, f'{username} added to contacts!')
            
            return redirect('contacts')
    
    return render(request, 'dashboard/contacts.html', {'contacts': contacts, 'form': form})

@login_required
def contact_toggle_favorite(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    contact.is_favorite = not contact.is_favorite
    contact.save()
    
    action = 'added to' if contact.is_favorite else 'removed from'
    messages.success(request, f'Contact {action} favorites!')
    return redirect('contacts')

@login_required
def contact_block(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    contact.is_blocked = not contact.is_blocked
    contact.save()
    
    action = 'blocked' if contact.is_blocked else 'unblocked'
    messages.success(request, f'Contact {action}!')
    return redirect('contacts')

@login_required
def contact_delete(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    
    if request.method == 'POST':
        contact.delete()
        messages.success(request, 'Contact deleted successfully!')
        return redirect('contacts')
    
    return render(request, 'dashboard/contact_confirm_delete.html', {'contact': contact})

# ==================== PAYMENT VIEWS ====================

@login_required
@verified_email_required
def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = Transaction.objects.filter(user=request.user).order_by('-initiated_at')[:20]
    
    context = {
        'wallet': wallet,
        'transactions': transactions,
    }
    
    return render(request, 'dashboard/wallet.html', context)

@login_required
@verified_email_required
def deposit_view(request):
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            phone_number = form.cleaned_data['phone_number']
            
            # Create pending transaction
            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='deposit',
                amount=amount,
                status='pending',
                mpesa_phone=phone_number,
                description=f"M-Pesa deposit to wallet"
            )
            
            # TODO: Integrate with M-Pesa API
            # This is where you'd call the M-Pesa STK Push API
            # For now, we'll simulate a successful deposit
            
            messages.info(request, f'Deposit request for KES {amount} initiated. Please check your phone to complete the payment.')
            return redirect('wallet')
    else:
        form = DepositForm()
    
    return render(request, 'dashboard/deposit.html', {'form': form})

@login_required
@verified_email_required
def withdrawal_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            if wallet.balance >= amount:
                # Create pending transaction
                transaction = Transaction.objects.create(
                    user=request.user,
                    transaction_type='withdrawal',
                    amount=amount,
                    status='pending',
                    description=f"Withdrawal from wallet"
                )
                
                # TODO: Integrate with M-Pesa API
                messages.info(request, f'Withdrawal request for KES {amount} initiated. Processing may take 24 hours.')
                return redirect('wallet')
            else:
                messages.error(request, 'Insufficient balance for withdrawal.')
    else:
        form = WithdrawalForm()
    
    context = {
        'form': form,
        'wallet': wallet,
    }
    
    return render(request, 'dashboard/withdrawal.html', context)

@login_required
def booking_create_view(request, username):
    service_provider = get_object_or_404(User, username=username)
    
    # Check if user is trying to book themselves
    if service_provider == request.user:
        messages.error(request, 'You cannot book your own services.')
        return redirect('profile_view', username=username)
    
    # Check if service provider is available
    if not service_provider.profile.is_available:
        messages.error(request, 'This service provider is currently unavailable.')
        return redirect('profile_view', username=username)
    
    if request.method == 'POST':
        form = ServiceBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.client = request.user
            booking.service_provider = service_provider
            
            # Calculate total amount
            hourly_rate = service_provider.profile.hourly_rate_outcall if booking.location_type == 'outcall' else service_provider.profile.hourly_rate_incall
            if hourly_rate:
                booking.total_amount = hourly_rate * booking.duration_hours
            else:
                messages.error(request, 'Service provider has not set their hourly rate.')
                return redirect('booking_create', username=username)
            
            booking.save()
            
            messages.success(request, f'Booking request sent to {service_provider.username}!')
            return redirect('booking_detail', booking_id=booking.id)
    else:
        form = ServiceBookingForm(initial={
            'service_provider_username': username
        })
    
    context = {
        'form': form,
        'service_provider': service_provider,
        'profile': service_provider.profile,
    }
    
    return render(request, 'dashboard/booking_create.html', context)

@login_required
def booking_detail_view(request, booking_id):
    booking = get_object_or_404(ServiceBooking, id=booking_id)
    
    # Check if user is part of the booking
    if request.user not in [booking.client, booking.service_provider]:
        return HttpResponseForbidden("You don't have permission to view this booking.")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm' and request.user == booking.service_provider:
            booking.status = 'confirmed'
            booking.save()
            messages.success(request, 'Booking confirmed!')
        
        elif action == 'complete' and request.user == booking.service_provider:
            booking.status = 'completed'
            booking.save()
            messages.success(request, 'Booking marked as completed!')
        
        elif action == 'cancel':
            # Both client and service provider can cancel
            booking.status = 'cancelled'
            booking.save()
            messages.warning(request, 'Booking cancelled!')
        
        elif action == 'pay' and request.user == booking.client:
            # Process payment
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            
            if wallet.balance >= booking.total_amount:
                # Create transaction
                transaction = Transaction.objects.create(
                    user=request.user,
                    transaction_type='payment',
                    amount=booking.total_amount,
                    status='completed',
                    description=f"Payment for booking #{booking.id}"
                )
                
                # Deduct from wallet
                wallet.balance -= booking.total_amount
                wallet.save()
                
                # Link transaction to booking
                booking.transaction = transaction
                booking.status = 'confirmed'
                booking.save()
                
                messages.success(request, 'Payment successful! Booking confirmed.')
            else:
                messages.error(request, 'Insufficient balance. Please deposit funds.')
                return redirect('deposit')
    
    return render(request, 'dashboard/booking_detail.html', {'booking': booking})

@login_required
def booking_list_view(request):
    # Get all bookings for the user
    bookings = ServiceBooking.objects.filter(
        Q(client=request.user) | Q(service_provider=request.user)
    ).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/booking_list.html', {'page_obj': page_obj, 'status_filter': status_filter})

# ==================== DISCOVERY VIEWS ====================

def search_view(request):
    profiles = Profile.objects.all().select_related('user')
    form = SearchForm(request.GET)
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        gender = form.cleaned_data.get('gender')
        county = form.cleaned_data.get('county')
        min_age = form.cleaned_data.get('min_age')
        max_age = form.cleaned_data.get('max_age')
        services = form.cleaned_data.get('services')
        is_vip = form.cleaned_data.get('is_vip')
        
        # Apply filters
        if query:
            profiles = profiles.filter(
                Q(user__username__icontains=query) |
                Q(city_town__icontains=query) |
                Q(services_offered__icontains=query)
            )
        
        if gender:
            profiles = profiles.filter(gender=gender)
        
        if county:
            profiles = profiles.filter(county__icontains=county)
        
        if min_age:
            profiles = profiles.filter(age__gte=min_age)
        
        if max_age:
            profiles = profiles.filter(age__lte=max_age)
        
        if services:
            profiles = profiles.filter(services_offered__icontains=services)
        
        if is_vip:
            profiles = profiles.filter(is_vip=True)
    
    # Only show available profiles to non-authenticated users
    if not request.user.is_authenticated:
        profiles = profiles.filter(is_available=True)
    
    # Order by VIP status and last activity
    profiles = profiles.order_by('-is_vip', '-last_active')
    
    # Pagination
    paginator = Paginator(profiles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'profiles': page_obj,
    }
    
    return render(request, 'dashboard/search.html', context)

@login_required
def saved_searches_view(request):
    saved_searches = SavedSearch.objects.filter(user=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        query = request.POST.get('query')
        if query:
            saved_search = SavedSearch.objects.create(
                user=request.user,
                search_query=query,
                filters={}  # You can save filters here
            )
            messages.success(request, 'Search saved!')
            return redirect('saved_searches')
    
    return render(request, 'dashboard/saved_searches.html', {'saved_searches': saved_searches})

@login_required
def saved_search_delete_view(request, search_id):
    saved_search = get_object_or_404(SavedSearch, id=search_id, user=request.user)
    
    if request.method == 'POST':
        saved_search.delete()
        messages.success(request, 'Saved search deleted!')
        return redirect('saved_searches')
    
    return render(request, 'dashboard/saved_search_confirm_delete.html', {'saved_search': saved_search})

@login_required
def invitation_create_view(request):
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.inviter = request.user
            invitation.save()
            
            # TODO: Send invitation email/SMS
            messages.success(request, f'Invitation sent to {invitation.invitee_email}!')
            return redirect('invitations')
    else:
        form = InvitationForm()
    
    return render(request, 'dashboard/invitation_create.html', {'form': form})

@login_required
def invitations_view(request):
    sent_invitations = Invitation.objects.filter(inviter=request.user).order_by('-created_at')
    
    return render(request, 'dashboard/invitations.html', {'invitations': sent_invitations})

@login_required
def invitation_delete_view(request, invitation_id):
    invitation = get_object_or_404(Invitation, id=invitation_id, inviter=request.user)
    
    if request.method == 'POST':
        invitation.delete()
        messages.success(request, 'Invitation deleted!')
        return redirect('invitations')
    
    return render(request, 'dashboard/invitation_confirm_delete.html', {'invitation': invitation})

# ==================== SETTINGS VIEWS ====================

@login_required
def settings_view(request):
    user_settings, created = UserSetting.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=user_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('settings')
    else:
        form = UserSettingsForm(instance=user_settings)
    
    return render(request, 'dashboard/settings.html', {'form': form})

@login_required
def archived_posts_view(request):
    posts = Post.objects.filter(user=request.user, is_archived=True).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/archived_posts.html', {'page_obj': page_obj})

# ==================== CALL VIEWS ====================

@login_required
def call_initiate_view(request, username):
    receiver = get_object_or_404(User, username=username)
    
    # Check if receiver allows calls
    try:
        receiver_settings = receiver.settings
        if not receiver_settings.allow_calls:
            messages.error(request, 'This user does not allow calls.')
            return redirect('profile_view', username=username)
    except UserSetting.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = CallInitiateForm(request.POST)
        if form.is_valid():
            call_type = form.cleaned_data['call_type']
            
            # Create call log
            call_log = CallLog.objects.create(
                caller=request.user,
                receiver=receiver,
                call_type=call_type,
                status='pending',
                started_at=timezone.now()
            )
            
            # TODO: Integrate with WebRTC or third-party calling service
            messages.info(request, f'Initiating {call_type} call with {receiver.username}...')
            return redirect('call_detail', call_id=call_log.id)
    else:
        form = CallInitiateForm(initial={'receiver_username': username})
    
    context = {
        'form': form,
        'receiver': receiver,
    }
    
    return render(request, 'dashboard/call_initiate.html', context)

@login_required
def call_detail_view(request, call_id):
    call = get_object_or_404(CallLog, id=call_id)
    
    # Check if user is part of the call
    if request.user not in [call.caller, call.receiver]:
        return HttpResponseForbidden("You don't have permission to view this call.")
    
    # Update call status if needed
    if call.status == 'pending' and request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accept':
            call.status = 'completed'
            call.ended_at = timezone.now()
            if 'duration' in request.POST:
                call.duration = int(request.POST['duration'])
            call.save()
            messages.success(request, 'Call accepted!')
        
        elif action == 'decline':
            call.status = 'declined'
            call.ended_at = timezone.now()
            call.save()
            messages.warning(request, 'Call declined.')
        
        elif action == 'end':
            call.status = 'completed'
            call.ended_at = timezone.now()
            if 'duration' in request.POST:
                call.duration = int(request.POST['duration'])
            call.save()
            messages.info(request, 'Call ended.')
    
    return render(request, 'dashboard/call_detail.html', {'call': call})

@login_required
def call_history_view(request):
    calls = CallLog.objects.filter(
        Q(caller=request.user) | Q(receiver=request.user)
    ).order_by('-started_at')
    
    # Filter by call type if provided
    call_type = request.GET.get('type')
    if call_type in ['audio', 'video']:
        calls = calls.filter(call_type=call_type)
    
    # Pagination
    paginator = Paginator(calls, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/call_history.html', {
        'page_obj': page_obj,
        'call_type': call_type,
    })

# ==================== API VIEWS ====================

@login_required
def api_get_conversation_messages(request, conversation_id):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    # Get messages after a certain timestamp (for real-time updates)
    last_message_id = request.GET.get('last_message_id', 0)
    
    messages = Message.objects.filter(
        conversation=conversation,
        id__gt=last_message_id
    ).order_by('sent_at')
    
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'content': msg.content,
            'message_type': msg.message_type,
            'sent_at': msg.sent_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': msg.is_read,
        })
    
    return JsonResponse({'messages': messages_data})

@login_required
def api_get_notifications(request):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    # Get unread messages count
    unread_messages = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False
    ).exclude(sender=request.user).count()
    
    # Get pending bookings
    pending_bookings = ServiceBooking.objects.filter(
        Q(client=request.user) | Q(service_provider=request.user),
        status='pending'
    ).count()
    
    # Get pending transactions
    pending_transactions = Transaction.objects.filter(
        user=request.user,
        status='pending'
    ).count()
    
    return JsonResponse({
        'unread_messages': unread_messages,
        'pending_bookings': pending_bookings,
        'pending_transactions': pending_transactions,
        'total': unread_messages + pending_bookings + pending_transactions,
    })

@login_required
def api_update_online_status(request):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    status = request.GET.get('status', 'online')
    
    if status in ['online', 'offline']:
        request.user.profile.is_online = (status == 'online')
        request.user.profile.save()
        
        return JsonResponse({'success': True, 'status': status})
    
    return JsonResponse({'error': 'Invalid status'}, status=400)

# ==================== HELPER VIEWS ====================

def landing_view(request):
    """Landing page for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Get featured profiles
    featured_profiles = Profile.objects.filter(
        is_verified=True,
        is_vip=True,
        is_available=True
    ).order_by('-total_views')[:6]
    
    # Get recent posts
    recent_posts = Post.objects.filter(
        is_featured=True
    ).select_related('user').order_by('-created_at')[:4]
    
    context = {
        'featured_profiles': featured_profiles,
        'recent_posts': recent_posts,
    }
    
    return render(request, 'dashboard/landing.html', context)

def terms_view(request):
    """Terms and conditions page"""
    return render(request, 'dashboard/terms.html')

def privacy_view(request):
    """Privacy policy page"""
    return render(request, 'dashboard/privacy.html')

def help_view(request):
    """Help and FAQ page"""
    return render(request, 'dashboard/help.html')

# ==================== ALLAUTH INTEGRATION HOOKS ====================

@login_required
def update_online_status_on_login(request):
    """Update user's online status when they log in"""
    request.user.profile.is_online = True
    request.user.profile.save()
    return redirect('dashboard')

@login_required
def update_online_status_on_logout(request):
    """Update user's online status when they log out"""
    request.user.profile.is_online = False
    request.user.profile.save()
    
    # Logout will be handled by allauth
    from allauth.account.views import LogoutView
    return LogoutView.as_view()(request)


# Add this to your views.py after saved_search_delete_view function

@login_required
def api_save_search(request):
    """API endpoint to save current search"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        data = json.loads(request.body)
        search_query = data.get('query', '')
        filters = data.get('filters', {})
        
        if not search_query and not filters:
            return JsonResponse({'error': 'No search criteria provided'}, status=400)
        
        # Create saved search
        saved_search = SavedSearch.objects.create(
            user=request.user,
            search_query=search_query,
            filters=filters
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Search saved successfully',
            'search_id': saved_search.id,
            'search_query': saved_search.search_query
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

from django.db import DatabaseError
import traceback

@login_required
def api_get_notifications(request):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        # Get unread messages count
        unread_messages = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
        
        # Get pending bookings
        pending_bookings = ServiceBooking.objects.filter(
            Q(client=request.user) | Q(service_provider=request.user),
            status='pending'
        ).count()
        
        # Get pending transactions
        pending_transactions = Transaction.objects.filter(
            user=request.user,
            status='pending'
        ).count()
        
        return JsonResponse({
            'unread_messages': unread_messages,
            'pending_bookings': pending_bookings,
            'pending_transactions': pending_transactions,
            'total': unread_messages + pending_bookings + pending_transactions,
        })
        
    except DatabaseError as e:
        # Log the error but return default values
        print(f"Database error in api_get_notifications: {e}")
        return JsonResponse({
            'unread_messages': 0,
            'pending_bookings': 0,
            'pending_transactions': 0,
            'total': 0,
            'error': 'Database error occurred'
        })
    except Exception as e:
        # Catch any other exceptions
        print(f"Unexpected error in api_get_notifications: {e}")
        traceback.print_exc()
        return JsonResponse({
            'unread_messages': 0,
            'pending_bookings': 0,
            'pending_transactions': 0,
            'total': 0,
            'error': 'Unexpected error occurred'
        })

@login_required
def api_update_online_status(request):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        status = request.GET.get('status', 'online')
        
        if status in ['online', 'offline']:
            # Use safe profile access
            profile = get_user_profile(request.user)
            profile.is_online = (status == 'online')
            profile.save()
            
            return JsonResponse({'success': True, 'status': status})
        
        return JsonResponse({'error': 'Invalid status'}, status=400)
        
    except Exception as e:
        print(f"Error updating online status: {e}")
        traceback.print_exc()
        return JsonResponse({'error': 'Failed to update status'}, status=500)
    
@login_required
def contact_add_view(request):
    """API endpoint to add a contact"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        nickname = request.POST.get('nickname', '')
        
        if not username:
            return JsonResponse({'error': 'Username is required'}, status=400)
        
        try:
            contact_user = User.objects.get(username=username)
            
            # Check if trying to add self
            if contact_user == request.user:
                return JsonResponse({'error': 'You cannot add yourself as a contact'}, status=400)
            
            # Check if already in contacts
            if Contact.objects.filter(user=request.user, contact_user=contact_user).exists():
                return JsonResponse({'error': f'{username} is already in your contacts'}, status=400)
            
            # Create contact
            contact = Contact.objects.create(
                user=request.user,
                contact_user=contact_user,
                nickname=nickname if nickname else username
            )
            
            return JsonResponse({
                'success': True,
                'message': f'{username} added to contacts!',
                'contact_id': contact.id
            })
            
        except User.DoesNotExist:
            return JsonResponse({'error': 'User does not exist'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# Add these imports at the top if not already there
import json
from django.http import JsonResponse
from django.db import DatabaseError
import traceback
from django.db.models import Q

# ==================== API VIEWS ====================

@login_required
def api_get_notifications(request):
    """API endpoint to get notification counts"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        # Get unread messages count
        unread_messages = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
        
        # Get pending bookings
        pending_bookings = ServiceBooking.objects.filter(
            Q(client=request.user) | Q(service_provider=request.user),
            status='pending'
        ).count()
        
        # Get pending transactions
        pending_transactions = Transaction.objects.filter(
            user=request.user,
            status='pending'
        ).count()
        
        return JsonResponse({
            'unread_messages': unread_messages,
            'pending_bookings': pending_bookings,
            'pending_transactions': pending_transactions,
            'total': unread_messages + pending_bookings + pending_transactions,
        })
        
    except DatabaseError as e:
        print(f"Database error in api_get_notifications: {e}")
        return JsonResponse({
            'unread_messages': 0,
            'pending_bookings': 0,
            'pending_transactions': 0,
            'total': 0,
            'error': 'Database error occurred'
        })
    except Exception as e:
        print(f"Unexpected error in api_get_notifications: {e}")
        traceback.print_exc()
        return JsonResponse({
            'unread_messages': 0,
            'pending_bookings': 0,
            'pending_transactions': 0,
            'total': 0,
            'error': 'Unexpected error occurred'
        })

@login_required
def api_update_online_status(request):
    """API endpoint to update user's online status"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        status = request.GET.get('status', 'online')
        
        if status in ['online', 'offline']:
            profile = get_user_profile(request.user)
            profile.is_online = (status == 'online')
            profile.save()
            
            return JsonResponse({'success': True, 'status': status})
        
        return JsonResponse({'error': 'Invalid status'}, status=400)
        
    except Exception as e:
        print(f"Error updating online status: {e}")
        traceback.print_exc()
        return JsonResponse({'error': 'Failed to update status'}, status=500)

@login_required
def api_save_search(request):
    """API endpoint to save current search"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        data = json.loads(request.body)
        search_query = data.get('query', '')
        filters = data.get('filters', {})
        
        if not search_query and not filters:
            return JsonResponse({'error': 'No search criteria provided'}, status=400)
        
        # Create saved search
        saved_search = SavedSearch.objects.create(
            user=request.user,
            search_query=search_query,
            filters=filters
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Search saved successfully',
            'search_id': saved_search.id,
            'search_query': saved_search.search_query
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_search_users(request):
    """API endpoint to search users for messaging"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        query = request.GET.get('q', '')
        if len(query) < 2:
            return JsonResponse({'users': []})
        
        # Search for users
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(email__icontains=query) |
            Q(profile__phone_number__icontains=query)
        ).exclude(id=request.user.id)[:10]
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'city_town': user.profile.city_town,
                'is_online': user.profile.is_online,
                'avatar_url': user.profile.photos.first().image.url if user.profile.photos.exists() else None
            })
        
        return JsonResponse({'users': users_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_mpesa_deposit(request):
    """API endpoint for M-Pesa deposit"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        data = json.loads(request.body)
        phone = data.get('phone')
        amount = data.get('amount')
        
        if not phone or not amount:
            return JsonResponse({'error': 'Phone and amount are required'}, status=400)
        
        # Create pending transaction
        transaction = Transaction.objects.create(
            user=request.user,
            transaction_type='deposit',
            amount=amount,
            status='pending',
            mpesa_phone=phone,
            description=f"M-Pesa deposit to wallet"
        )
        
        # TODO: Integrate with actual Co-op Bank API
        # For now, simulate a successful deposit
        # In production, you would call Co-op Bank API here
        
        return JsonResponse({
            'success': True,
            'message': 'M-Pesa request initiated. Please check your phone.',
            'transaction_id': transaction.id,
            'checkout_id': 'SIMULATED_CHECKOUT_ID'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    


@login_required
def post_edit_view(request, post_id):
    """Edit an existing post"""
    post = get_object_or_404(Post, id=post_id, user=request.user)
    
    if request.method == 'POST':
        form = PostUpdateForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostUpdateForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
        'title': 'Edit Post',
    }
    
    return render(request, 'dashboard/post_edit.html', context)


@login_required
def api_typing_indicator(request):
    """Handle typing indicators"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        is_typing = data.get('is_typing', False)
        
        # Store typing status in cache or database
        # You can use Django's cache framework here
        from django.core.cache import cache
        cache_key = f'typing:{conversation_id}:{request.user.id}'
        cache.set(cache_key, is_typing, timeout=5)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_get_typing_status(request, conversation_id):
    """Get typing status for a conversation"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    from django.core.cache import cache
    
    # Get other participant
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    other_user = conversation.participants.exclude(id=request.user.id).first()
    
    cache_key = f'typing:{conversation_id}:{other_user.id}'
    is_typing = cache.get(cache_key, False)
    
    return JsonResponse({
        'typing': {
            str(other_user.id): is_typing
        }
    })

@login_required
def api_clear_chat(request, conversation_id):
    """Clear all messages in a chat"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    # Soft delete messages
    Message.objects.filter(conversation=conversation).delete()
    
    return JsonResponse({'success': True})


@login_required
def video_detail_view(request, video_id):
    """View individual video details"""
    video = get_object_or_404(Video, id=video_id)
    profile = video.profile
    
    # Check if user can view this video
    if request.user != profile.user:
        # Check if user is blocked
        if Contact.objects.filter(
            user=profile.user,
            contact_user=request.user,
            is_blocked=True
        ).exists():
            messages.error(request, 'You cannot view this video.')
            return redirect('dashboard')
        
        # Increment views
        video.views += 1
        video.save()
    
    # Check if user has liked the video
    try:
        user_has_liked = VideoLike.objects.filter(video=video, user=request.user).exists()
    except:
        user_has_liked = False
    
    # Get similar videos
    similar_videos = Video.objects.filter(
        profile=profile
    ).exclude(id=video_id).order_by('-uploaded_at')[:4]
    
    # Get video comments
    video_comments = VideoComment.objects.filter(video=video).order_by('-created_at')[:50]
    
    context = {
        'video': video,
        'profile': profile,
        'profile_user': profile.user,
        'similar_videos': similar_videos,
        'is_owner': request.user == profile.user,
        'user_has_liked': user_has_liked,
        'likes_count': video.likes,
        'comments': video_comments,
    }
    
    return render(request, 'dashboard/video_detail.html', context)

@login_required
@require_POST
def video_like_view(request, video_id):
    """Like or unlike a video"""
    video = get_object_or_404(Video, id=video_id)
    
    try:
        # Check if user has already liked the video
        like, created = VideoLike.objects.get_or_create(
            user=request.user,
            video=video
        )
        
        if not created:
            # User already liked the video, so unlike it
            like.delete()
            liked = False
            # Decrement likes count
            if video.likes > 0:
                video.likes -= 1
        else:
            liked = True
            # Increment likes count
            video.likes += 1
        
        video.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'liked': liked,
                'likes_count': video.likes,
            })
        
        messages.success(request, f'Video {"liked" if liked else "unliked"}!')
        return redirect('video_detail', video_id=video_id)
        
    except Exception as e:
        print(f"Error in video_like_view: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Failed to process like'}, status=500)
        messages.error(request, 'Failed to process like')
        return redirect('video_detail', video_id=video_id)

# Update these imports at the top
from django.views.decorators.http import require_POST, require_http_methods
from django.http import HttpResponseForbidden

# Fix the api_video_edit function
@login_required
@csrf_exempt
def api_video_edit(request, video_id):
    """API endpoint to edit video"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        video = Video.objects.get(id=video_id, profile__user=request.user)
    except Video.DoesNotExist:
        return JsonResponse({'error': 'Video not found or permission denied'}, status=404)
    
    try:
        if request.method == 'POST':
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            
            if not title:
                return JsonResponse({'error': 'Title is required'}, status=400)
            
            video.title = title
            video.description = description
            
            if 'thumbnail' in request.FILES:
                thumbnail = request.FILES['thumbnail']
                # Validate file type
                if not thumbnail.content_type.startswith('image/'):
                    return JsonResponse({'error': 'Only image files are allowed for thumbnails'}, status=400)
                # Validate file size (10MB limit)
                if thumbnail.size > 10 * 1024 * 1024:
                    return JsonResponse({'error': 'Thumbnail image is too large. Max size is 10MB'}, status=400)
                video.thumbnail = thumbnail
            
            video.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Video updated successfully',
                'video': {
                    'id': video.id,
                    'title': video.title,
                    'description': video.description,
                    'thumbnail_url': video.thumbnail.url if video.thumbnail else ''
                }
            })
        else:
            return JsonResponse({'error': 'Invalid method. Use POST'}, status=405)
            
    except Exception as e:
        print(f"Error in api_video_edit: {e}")
        return JsonResponse({'error': 'Server error occurred'}, status=500)

# Fix the api_video_delete function
@login_required
@csrf_exempt
@require_POST
def api_video_delete(request, video_id):
    """API endpoint to delete video"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        video = Video.objects.get(id=video_id, profile__user=request.user)
    except Video.DoesNotExist:
        return JsonResponse({'error': 'Video not found or permission denied'}, status=404)
    
    try:
        video_title = video.title
        video.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Video "{video_title}" deleted successfully'
        })
            
    except Exception as e:
        print(f"Error in api_video_delete: {e}")
        return JsonResponse({'error': 'Failed to delete video'}, status=500)

# Fix the api_video_comment function
@login_required
@csrf_exempt
@require_POST
def api_video_comment(request, video_id):
    """API endpoint to add comment to video"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        video = Video.objects.get(id=video_id)
    except Video.DoesNotExist:
        return JsonResponse({'error': 'Video not found'}, status=404)
    
    try:
        text = request.POST.get('text', '').strip()
        
        if not text:
            return JsonResponse({'error': 'Comment text is required'}, status=400)
        
        # Create comment
        comment = VideoComment.objects.create(
            video=video,
            user=request.user,
            text=text
        )
        
        # Get avatar URL
        avatar_url = ''
        try:
            if request.user.profile.photos.exists():
                primary_photo = request.user.profile.photos.filter(is_primary=True).first()
                if not primary_photo:
                    primary_photo = request.user.profile.photos.first()
                if primary_photo:
                    avatar_url = primary_photo.image.url
        except:
            pass
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'username': request.user.username,
                'avatar_url': avatar_url,
                'text': text,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
            
    except Exception as e:
        print(f"Error in api_video_comment: {e}")
        return JsonResponse({'error': 'Failed to add comment'}, status=500)

# Add this new function for comment deletion
@login_required
@csrf_exempt
@require_POST
def api_comment_delete(request, comment_id):
    """API endpoint to delete comment"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        comment = VideoComment.objects.get(id=comment_id)
    except VideoComment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found'}, status=404)
    
    # Check if user owns the comment or is video owner
    if not (comment.user == request.user or comment.video.profile.user == request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        comment.delete()
        return JsonResponse({
            'success': True,
            'message': 'Comment deleted successfully'
        })
            
    except Exception as e:
        print(f"Error in api_comment_delete: {e}")
        return JsonResponse({'error': 'Failed to delete comment'}, status=500)



# views.py - Add these functions

@login_required
def photo_upload_view(request):
    """View for uploading and managing photos"""
    photos = Photo.objects.filter(profile=request.user.profile).order_by('-is_primary', '-uploaded_at')
    
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.profile = request.user.profile
            
            # If this is set as primary, unset others
            if photo.is_primary:
                Photo.objects.filter(profile=request.user.profile).update(is_primary=False)
            
            photo.save()
            messages.success(request, 'Photo uploaded successfully!')
            return redirect('upload_photo')
    else:
        form = PhotoUploadForm()
    
    context = {
        'photos': photos,
        'form': form,
    }
    
    return render(request, 'dashboard/upload_photo.html', context)


@login_required
@csrf_exempt
@require_POST
def api_photo_upload(request):
    """API endpoint to upload multiple photos"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        images = request.FILES.getlist('images')
        caption = request.POST.get('caption', '').strip()
        is_primary = request.POST.get('is_primary') == 'on'
        
        if not images:
            return JsonResponse({'error': 'No images provided'}, status=400)
        
        # If setting as primary, unset current primary
        if is_primary:
            Photo.objects.filter(profile=request.user.profile).update(is_primary=False)
        
        photo_ids = []
        for image in images:
            # Validate file type
            if not image.content_type.startswith('image/'):
                continue
            
            # Validate file size (5MB)
            if image.size > 5 * 1024 * 1024:
                continue
            
            photo = Photo.objects.create(
                profile=request.user.profile,
                image=image,
                caption=caption,
                is_primary=is_primary
            )
            photo_ids.append(photo.id)
            
            # Only first photo can be primary if multiple uploaded
            if is_primary:
                is_primary = False
        
        return JsonResponse({
            'success': True,
            'message': f'{len(photo_ids)} photo(s) uploaded successfully',
            'photo_ids': photo_ids
        })
        
    except Exception as e:
        print(f"Error in api_photo_upload: {e}")
        return JsonResponse({'error': 'Failed to upload photos'}, status=500)


@login_required
@csrf_exempt
@require_POST
def api_photo_edit(request):
    """API endpoint to edit photo"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        photo_id = request.POST.get('photo_id')
        caption = request.POST.get('caption', '').strip()
        is_primary = request.POST.get('is_primary') == 'on'
        
        if not photo_id:
            return JsonResponse({'error': 'Photo ID is required'}, status=400)
        
        photo = Photo.objects.get(id=photo_id, profile=request.user.profile)
        
        # Update photo
        photo.caption = caption
        
        # Handle primary photo change
        if is_primary and not photo.is_primary:
            # Unset current primary
            Photo.objects.filter(profile=request.user.profile).update(is_primary=False)
            photo.is_primary = True
        
        photo.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Photo updated successfully',
            'photo_id': photo.id,
            'caption': photo.caption,
            'is_primary': photo.is_primary
        })
        
    except Photo.DoesNotExist:
        return JsonResponse({'error': 'Photo not found or permission denied'}, status=404)
    except Exception as e:
        print(f"Error in api_photo_edit: {e}")
        return JsonResponse({'error': 'Failed to update photo'}, status=500)


@login_required
@csrf_exempt
@require_POST
def api_photo_delete(request):
    """API endpoint to delete photo"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        photo_id = request.POST.get('photo_id')
        
        if not photo_id:
            return JsonResponse({'error': 'Photo ID is required'}, status=400)
        
        photo = Photo.objects.get(id=photo_id, profile=request.user.profile)
        
        # Store info before deletion
        was_primary = photo.is_primary
        
        # Delete the photo
        photo.delete()
        
        # If it was primary, set a new primary (most recent photo)
        if was_primary:
            latest_photo = Photo.objects.filter(profile=request.user.profile).first()
            if latest_photo:
                latest_photo.is_primary = True
                latest_photo.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Photo deleted successfully',
            'was_primary': was_primary
        })
        
    except Photo.DoesNotExist:
        return JsonResponse({'error': 'Photo not found or permission denied'}, status=404)
    except Exception as e:
        print(f"Error in api_photo_delete: {e}")
        return JsonResponse({'error': 'Failed to delete photo'}, status=500)


@login_required
@csrf_exempt
@require_POST
def api_photo_set_primary(request):
    """API endpoint to set photo as primary"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        photo_id = request.POST.get('photo_id')
        
        if not photo_id:
            return JsonResponse({'error': 'Photo ID is required'}, status=400)
        
        # Unset current primary
        Photo.objects.filter(profile=request.user.profile).update(is_primary=False)
        
        # Set new primary
        photo = Photo.objects.get(id=photo_id, profile=request.user.profile)
        photo.is_primary = True
        photo.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Primary photo updated successfully',
            'photo_id': photo.id
        })
        
    except Photo.DoesNotExist:
        return JsonResponse({'error': 'Photo not found or permission denied'}, status=404)
    except Exception as e:
        print(f"Error in api_photo_set_primary: {e}")
        return JsonResponse({'error': 'Failed to set primary photo'}, status=500)
    

@login_required
def clear_conversation(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id, users=request.user)
        # Clear all messages in the conversation
        conversation.messages.all().delete()
        return JsonResponse({'success': True})
    except Conversation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Conversation not found'}, status=404)