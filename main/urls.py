# main/urls.py
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    # ==================== ALLAUTH URLs ===================
    
    # ==================== DASHBOARD URLs ====================
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # ==================== PROFILE URLs ====================
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/upload/photo/', views.profile_upload_photo, name='upload_photo'),
    path('profile/upload/video/', views.profile_upload_video, name='upload_video'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    
    # ==================== POST URLs ====================
    path('post/create/', views.post_create_view, name='post_create'),
    path('post/<int:post_id>/', views.post_detail_view, name='post_detail'),
    path('post/<int:post_id>/edit/', views.post_edit_view, name='post_edit'), 
    path('post/<int:post_id>/interact/<str:interaction_type>/', 
         views.post_interact_view, name='post_interact'),
    path('post/<int:post_id>/archive/', views.post_archive_view, name='post_archive'),
    path('post/<int:post_id>/delete/', views.post_delete_view, name='post_delete'),
    path('posts/archived/', views.archived_posts_view, name='archived_posts'),
    # main/urls.py - Add these to urlpatterns
          path('photos/upload/', views.photo_upload_view, name='upload_photo'),
     path('api/photos/upload/', views.api_photo_upload, name='api_photo_upload'),
     path('api/photos/edit/', views.api_photo_edit, name='api_photo_edit'),
     path('api/photos/delete/', views.api_photo_delete, name='api_photo_delete'),
     path('api/photos/set-primary/', views.api_photo_set_primary, name='api_photo_set_primary'),
    
    # ==================== VIDEO URLs ====================
    path('video/<int:video_id>/', views.video_detail_view, name='video_detail'),
    path('video/<int:video_id>/like/', views.video_like_view, name='video_like'),
    path('api/video/<int:video_id>/edit/', views.api_video_edit, name='api_video_edit'),
    path('api/video/<int:video_id>/delete/', views.api_video_delete, name='api_video_delete'),
    path('api/video/<int:video_id>/comment/', views.api_video_comment, name='api_video_comment'),
    path('api/comment/<int:comment_id>/delete/', views.api_comment_delete, name='api_comment_delete'),
    
    # ==================== MESSAGING URLs ====================
    path('inbox/', views.inbox_view, name='inbox'),
    path('conversation/', views.conversation_view, name='conversation_new'),
    path('conversation/<int:conversation_id>/', views.conversation_view, name='conversation'),
    path('conversation/user/<str:username>/', views.conversation_view, name='conversation_user'),
     path('conversation/clear/<int:conversation_id>/', 
         views.clear_conversation, 
         name='conversation_clear'),
    path('conversation/<int:conversation_id>/delete/', 
         views.conversation_delete_view, name='conversation_delete'),
    path('contacts/', views.contacts_view, name='contacts'),
    path('contact/<int:contact_id>/favorite/', 
         views.contact_toggle_favorite, name='contact_favorite'),
    path('contact/<int:contact_id>/block/', views.contact_block, name='contact_block'),
    path('contact/<int:contact_id>/delete/', views.contact_delete, name='contact_delete'),
    path('contact/add/', views.contact_add_view, name='contact_add'),
    path('contacts/toggle-favorite/<int:contact_id>/', views.contact_toggle_favorite, name='contact_toggle_favorite'),
    path('contacts/block/<int:contact_id>/', views.contact_block, name='contact_block'),
    path('contacts/delete/<int:contact_id>/', views.contact_delete, name='contact_delete'),
    
    # ==================== PAYMENT URLs ====================
    path('wallet/', views.wallet_view, name='wallet'),
    path('wallet/deposit/', views.deposit_view, name='deposit'),
    path('wallet/withdraw/', views.withdrawal_view, name='withdrawal'),
    path('booking/create/<str:username>/', 
         views.booking_create_view, name='booking_create'),
    path('booking/<int:booking_id>/', views.booking_detail_view, name='booking_detail'),
    path('bookings/', views.booking_list_view, name='booking_list'),
    
    # ==================== DISCOVERY URLs ====================
    path('search/', views.search_view, name='search'),
    path('saved-searches/', views.saved_searches_view, name='saved_searches'),
    path('saved-search/<int:search_id>/delete/', 
         views.saved_search_delete_view, name='saved_search_delete'),
    path('invitations/', views.invitations_view, name='invitations'),
    path('invitation/create/', views.invitation_create_view, name='invitation_create'),
    path('invitation/<int:invitation_id>/delete/', 
         views.invitation_delete_view, name='invitation_delete'),
    
    # ==================== CALL URLs ====================
    path('call/history/', views.call_history_view, name='call_history'),
    path('call/<int:call_id>/', views.call_detail_view, name='call_detail'),
    path('call/<str:username>/', views.call_initiate_view, name='call_initiate'),
    
    # ==================== SETTINGS URLs ====================
    path('settings/', views.settings_view, name='settings'),
    
    # ==================== API URLs ====================
    path('api/conversation/<int:conversation_id>/messages/', 
         views.api_get_conversation_messages, name='api_conversation_messages'),
    path('api/notifications/', views.api_get_notifications, name='api_get_notifications'),
    path('api/update-online-status/', 
         views.api_update_online_status, name='api_update_online_status'),
    path('api/save-search/', views.api_save_search, name='api_save_search'),
    path('api/search-users/', views.api_search_users, name='api_search_users'),
    path('api/mpesa-deposit/', views.api_mpesa_deposit, name='api_mpesa_deposit'),
    path('api/typing-indicator/', views.api_typing_indicator, name='api_typing_indicator'),
    path('api/conversation/<int:conversation_id>/typing/', views.api_get_typing_status, name='api_typing_status'),
    path('api/conversation/<int:conversation_id>/clear/', views.api_clear_chat, name='api_clear_chat'),
    
    # ==================== HELPER URLs ====================
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('help/', views.help_view, name='help'),
    
    # ==================== ALLAUTH HOOK URLs ====================
    path('accounts/login/success/', 
         views.update_online_status_on_login, name='login_success'),
    path('accounts/logout/confirm/', 
         views.update_online_status_on_logout, name='logout_confirm'),
]