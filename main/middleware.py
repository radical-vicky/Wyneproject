from django.shortcuts import redirect
from django.contrib import messages
from .models import Profile, Wallet, UserSetting

class ProfileCreationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            try:
                # Just try to access profile to trigger creation if needed
                profile = request.user.profile
            except Profile.DoesNotExist:
                # Create missing profile
                Profile.objects.create(
                    user=request.user,
                    phone_number=f"0700000000{request.user.id}",
                    gender='Other',
                    sexual_orientation='Other',
                    age=25,
                    nationality='Kenyan',
                    county='Nairobi',
                    city_town='Nairobi',
                    location='Nairobi CBD',
                    services_offered='Dinner Date'
                )
                
                # Create wallet if missing
                Wallet.objects.get_or_create(user=request.user)
                
                # Create settings if missing
                UserSetting.objects.get_or_create(user=request.user)
                
                messages.info(request, "Your profile has been created with default settings. Please update your information.")