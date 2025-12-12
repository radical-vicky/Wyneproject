import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

import django
django.setup()

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import Profile, Wallet, UserSetting

class Command(BaseCommand):
    help = 'Create missing profiles for existing users'
    
    def handle(self, *args, **kwargs):
        users = User.objects.all()
        created_count = 0
        
        for user in users:
            # Create profile if it doesn't exist
            if not hasattr(user, 'profile'):
                Profile.objects.create(
                    user=user,
                    phone_number=f"0700000000{user.id}",  # Default phone
                    gender='Other',
                    sexual_orientation='Other',
                    age=25,
                    nationality='Kenyan',
                    county='Nairobi',
                    city_town='Nairobi',
                    location='Nairobi CBD',
                    services_offered='Dinner Date'
                )
                self.stdout.write(self.style.SUCCESS(f'Created profile for {user.username}'))
                created_count += 1
            
            # Create wallet if it doesn't exist
            if not hasattr(user, 'wallet'):
                Wallet.objects.create(user=user)
                self.stdout.write(self.style.SUCCESS(f'Created wallet for {user.username}'))
            
            # Create settings if it doesn't exist
            if not hasattr(user, 'settings'):
                UserSetting.objects.create(user=user)
                self.stdout.write(self.style.SUCCESS(f'Created settings for {user.username}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created profiles for {created_count} users'))