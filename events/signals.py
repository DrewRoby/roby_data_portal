from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event, Space, EventInvitation
from shares.models import Share


@receiver(post_save, sender=Event)
def create_suggestion_box(sender, instance, created, **kwargs):
    """
    Automatically create a suggestion box space when an event is created.
    """
    if created:
        Space.objects.create(
            event=instance,
            name="Suggestion Box",
            description="Suggested agenda items from invitees",
            space_type='suggestion_box',
            order=999  # Put it last by default
        )


@receiver(post_save, sender=Share)
def create_event_invitation(sender, instance, created, **kwargs):
    """
    Create an EventInvitation when a Share is created for an Event.
    """
    if created and instance.content_type.model == 'event':
        try:
            from .models import Event
            event = Event.objects.get(pk=instance.object_id)
            
            # Only create invitation if sharing with a specific user (not public shares)
            if instance.shared_with:
                EventInvitation.objects.get_or_create(
                    event=event,
                    invitee=instance.shared_with,
                    defaults={'share': instance}
                )
        except Event.DoesNotExist:
            pass