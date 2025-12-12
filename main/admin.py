# main/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import *

# Extend User Admin to show profile inline
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_city', 'is_vip')
    list_select_related = ('profile',)
    
    def get_city(self, instance):
        return instance.profile.city_town
    get_city.short_description = 'City'
    
    def is_vip(self, instance):
        return instance.profile.is_vip
    is_vip.boolean = True
    is_vip.short_description = 'VIP'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register all models
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'gender', 'age', 'city_town', 'is_vip', 'is_verified', 'is_available')
    list_filter = ('is_vip', 'is_verified', 'gender', 'county', 'city_town')
    search_fields = ('user__username', 'phone_number', 'city_town', 'services_offered')
    list_per_page = 50
    readonly_fields = ('created_at', 'last_active', 'total_views', 'total_calls')

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'views', 'duration', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('title', 'profile__user__username')
    readonly_fields = ('views', 'uploaded_at')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post_type', 'is_archived', 'is_featured', 'views', 'likes', 'created_at')
    list_filter = ('post_type', 'is_archived', 'is_featured', 'created_at')
    search_fields = ('content', 'user__username')
    readonly_fields = ('views', 'likes', 'created_at', 'updated_at')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'transaction_type', 'amount', 'status', 'mpesa_receipt', 'initiated_at')
    list_filter = ('status', 'transaction_type', 'initiated_at')
    search_fields = ('user__username', 'mpesa_receipt', 'reference')
    readonly_fields = ('initiated_at', 'completed_at')

@admin.register(ServiceBooking)
class ServiceBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'service_provider', 'service_type', 'total_amount', 'status', 'booking_date')
    list_filter = ('status', 'location_type', 'booking_date')
    search_fields = ('client__username', 'service_provider__username', 'service_type')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'participants_list', 'last_message_at', 'created_at')
    filter_horizontal = ('participants',)
    
    def participants_list(self, obj):
        return ", ".join([p.username for p in obj.participants.all()])
    participants_list.short_description = 'Participants'

# Register remaining models with default admin
admin.site.register(Photo)
admin.site.register(PostInteraction)
admin.site.register(Comment)
admin.site.register(Message)
admin.site.register(Contact)
admin.site.register(CallLog)
admin.site.register(Wallet)
admin.site.register(SavedSearch)
admin.site.register(Invitation)
admin.site.register(UserSetting)