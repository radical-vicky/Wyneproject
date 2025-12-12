# main/urls.py
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ==================== ALLAUTH URLs ====================
    path('accounts/', include('allauth.urls')),
    
    # ==================== DASHBOARD URLs ====================
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.landing_view, name='landing'),
    
    # ==================== PROFILE URLs ====================
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),  # MOVE THIS BEFORE username pattern
    path('profile/upload/photo/', views.profile_upload_photo, name='upload_photo'),
    path('profile/upload/video/', views.profile_upload_video, name='upload_video'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),  # This should be LAST
    
    # ==================== POST URLs ====================
    path('post/create/', views.post_create_view, name='post_create'),
    path('post/<int:post_id>/', views.post_detail_view, name='post_detail'),
    path('post/<int:post_id>/interact/<str:interaction_type>/', 
         views.post_interact_view, name='post_interact'),
    path('post/<int:post_id>/archive/', views.post_archive_view, name='post_archive'),
    path('post/<int:post_id>/delete/', views.post_delete_view, name='post_delete'),
    path('posts/archived/', views.archived_posts_view, name='archived_posts'),
    
    # ==================== MESSAGING URLs ====================
    path('inbox/', views.inbox_view, name='inbox'),
    path('conversation/', views.conversation_view, name='conversation_new'),
    path('conversation/<int:conversation_id>/', views.conversation_view, name='conversation'),
    path('conversation/user/<str:username>/', views.conversation_view, name='conversation_user'),
    path('conversation/<int:conversation_id>/delete/', 
         views.conversation_delete_view, name='conversation_delete'),
    path('contacts/', views.contacts_view, name='contacts'),
    path('contact/<int:contact_id>/favorite/', 
         views.contact_toggle_favorite, name='contact_favorite'),
    path('contact/<int:contact_id>/block/', views.contact_block, name='contact_block'),
    path('contact/<int:contact_id>/delete/', views.contact_delete, name='contact_delete'),
    path('contact/add/', views.contact_add_view, name='contact_add'),
    
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
    path('call/<str:username>/', views.call_initiate_view, name='call_initiate'),
    path('call/detail/<int:call_id>/', views.call_detail_view, name='call_detail'),
    path('call/history/', views.call_history_view, name='call_history'),
    
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