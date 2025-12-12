from .models import Message
from django.db.models import Q

def unread_messages(request):
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
        return {'unread_messages_count': unread_count}
    return {'unread_messages_count': 0}