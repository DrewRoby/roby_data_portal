from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db import models

from shares.decorators import owner_or_permission_required
from .models import Event, EventInvitation, Space, AgendaItem, AgendaComment
from .forms import (
    EventForm, RSVPForm, AgendaItemForm, AgendaCommentForm, 
    SpaceForm, MoveAgendaItemForm, BulkRSVPForm
)


def event_list(request):
    """
    Display list of events - both created by user and shared with user.
    Public for now, but login required for full functionality.
    """
    if request.user.is_authenticated:
        # Get events created by user
        created_events = Event.objects.filter(created_by=request.user)
        
        # Get events shared with user
        shared_event_ids = EventInvitation.objects.filter(
            invitee=request.user
        ).values_list('event_id', flat=True)
        shared_events = Event.objects.filter(id__in=shared_event_ids)
        
        # Combine and organize
        all_events = []
        
        for event in created_events:
            all_events.append({
                'event': event,
                'is_created_by_user': True,
                'invitation': None
            })
        
        for event in shared_events:
            if event not in created_events:  # Avoid duplicates
                try:
                    invitation = EventInvitation.objects.get(event=event, invitee=request.user)
                except EventInvitation.DoesNotExist:
                    pass
    
    
    return render(request, 'events/event_list.html', {'all_events':all_events})



@login_required
def event_create(request):
    """Create a new event."""
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            
            messages.success(request, f'Event "{event.title}" created successfully!')
            return redirect('events:event_detail', pk=event.pk)
    else:
        form = EventForm()
    
    return render(request, 'events/event_create.html', {'form': form})


@owner_or_permission_required('EDIT')
def event_edit(request, pk):
    """Edit an existing event."""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f'Event "{event.title}" updated successfully!')
            return redirect('events:event_detail', pk=event.pk)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/event_edit.html', {
        'form': form,
        'event': event
    })


@login_required
@require_POST
def rsvp_update(request, pk):
    """Update RSVP status for an event invitation."""
    event = get_object_or_404(Event, pk=pk)
    
    try:
        invitation = EventInvitation.objects.get(event=event, invitee=request.user)
    except EventInvitation.DoesNotExist:
        messages.error(request, "You don't have an invitation to this event.")
        return redirect('events:event_detail', pk=pk)
    
    form = RSVPForm(request.POST, instance=invitation)
    if form.is_valid():
        form.save()
        status_display = dict(EventInvitation.RSVP_CHOICES)[invitation.rsvp_status]
        messages.success(request, f'RSVP updated to: {status_display}')
    else:
        messages.error(request, 'Error updating RSVP. Please try again.')
    
    return redirect('events:event_detail', pk=pk)


@owner_or_permission_required('VIEW')
def rsvp_summary(request, pk):
    """Display RSVP summary for event organizers."""
    event = get_object_or_404(Event, pk=pk)
    
    # Only event creator or users with ADMIN permission can see full RSVP summary
    user_permission = event.get_user_permission(request.user)
    if user_permission not in ['ADMIN']:
        raise Http404("You don't have permission to view RSVP details.")
    
    invitations = event.invitations.select_related('invitee', 'share').all()
    
    # Group by RSVP status
    rsvp_groups = {
        'yes': [],
        'tentative': [],
        'no': [],
        'pending': []
    }
    
    for invitation in invitations:
        rsvp_groups[invitation.rsvp_status].append(invitation)
    
    context = {
        'event': event,
        'rsvp_groups': rsvp_groups,
        'total_invitations': invitations.count(),
    }
    
    return render(request, 'events/rsvp_summary.html', context)


@owner_or_permission_required('EDIT')
def space_create(request, event_pk):
    """Create a new space for an event."""
    event = get_object_or_404(Event, pk=event_pk)
    
    if request.method == 'POST':
        form = SpaceForm(request.POST)
        if form.is_valid():
            space = form.save(commit=False)
            space.event = event
            space.space_type = 'normal'  # Only normal spaces can be created manually
            
            # Set order to be after existing spaces
            max_order = event.spaces.filter(space_type='normal').aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            space.order = max_order + 1
            
            space.save()
            messages.success(request, f'Space "{space.name}" created successfully!')
            return redirect('events:event_detail', pk=event.pk)
    else:
        form = SpaceForm()
    
    return render(request, 'events/space_create.html', {
        'form': form,
        'event': event
    })


@owner_or_permission_required('EDIT')
def space_edit(request, pk):
    """Edit an existing space."""
    space = get_object_or_404(Space, pk=pk)
    event = space.event
    
    # Don't allow editing suggestion boxes
    if space.space_type == 'suggestion_box':
        messages.error(request, "Suggestion boxes cannot be edited.")
        return redirect('events:event_detail', pk=event.pk)
    
    if request.method == 'POST':
        form = SpaceForm(request.POST, instance=space)
        if form.is_valid():
            form.save()
            messages.success(request, f'Space "{space.name}" updated successfully!')
            return redirect('events:event_detail', pk=event.pk)
    else:
        form = SpaceForm(instance=space)
    
    return render(request, 'events/space_edit.html', {
        'form': form,
        'space': space,
        'event': event
    })


@login_required
def agenda_item_create(request, space_pk):
    """Create a new agenda item."""
    space = get_object_or_404(Space, pk=space_pk)
    event = space.event
    
    # Check permissions based on space type
    if space.space_type == 'suggestion_box':
        # For suggestion box, check if user can suggest
        if not event.can_user_suggest_agenda_items(request.user):
            messages.error(request, "You need to RSVP 'Yes' and have edit permission to suggest agenda items.")
            return redirect('events:event_detail', pk=event.pk)
    else:
        # For normal spaces, check edit permission
        user_permission = event.get_user_permission(request.user)
        if user_permission not in ['EDIT', 'ADMIN']:
            raise Http404("You don't have permission to add agenda items.")
    
    if request.method == 'POST':
        form = AgendaItemForm(request.POST)
        if form.is_valid():
            agenda_item = form.save(commit=False)
            agenda_item.space = space
            
            # Set suggested_by for suggestion box items
            if space.space_type == 'suggestion_box':
                agenda_item.suggested_by = request.user
            
            # Set order to be last in the space
            max_order = space.agenda_items.aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            agenda_item.order = max_order + 1
            
            agenda_item.save()
            
            if space.space_type == 'suggestion_box':
                messages.success(request, 'Your suggestion has been added!')
            else:
                messages.success(request, f'Agenda item "{agenda_item.title}" added successfully!')
            
            return redirect('events:event_detail', pk=event.pk)
    else:
        form = AgendaItemForm()
    
    return render(request, 'events/agenda_item_create.html', {
        'form': form,
        'space': space,
        'event': event
    })


def agenda_item_detail(request, pk):
    """Display agenda item details with comments."""
    agenda_item = get_object_or_404(AgendaItem, pk=pk)
    event = agenda_item.space.event
    
    # Check if user can view this event
    user_permission = event.get_user_permission(request.user)
    if not user_permission:
        raise Http404("Event not found or you don't have permission to view it.")
    
    # Check if user can comment
    can_comment = agenda_item.can_user_comment(request.user, event)
    
    comments = agenda_item.comments.select_related('author').all()
    
    # Handle comment form submission
    if request.method == 'POST' and can_comment:
        comment_form = AgendaCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.agenda_item = agenda_item
            comment.author = request.user
            comment.save()
            
            messages.success(request, 'Comment added successfully!')
            return redirect('events:agenda_item_detail', pk=pk)
    else:
        comment_form = AgendaCommentForm() if can_comment else None
    
    context = {
        'agenda_item': agenda_item,
        'event': event,
        'comments': comments,
        'can_comment': can_comment,
        'comment_form': comment_form,
        'user_permission': user_permission,
    }
    
    return render(request, 'events/agenda_item_detail.html', context)


@owner_or_permission_required('EDIT')
def agenda_item_edit(request, pk):
    """Edit an existing agenda item."""
    agenda_item = get_object_or_404(AgendaItem, pk=pk)
    event = agenda_item.space.event
    
    if request.method == 'POST':
        form = AgendaItemForm(request.POST, instance=agenda_item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Agenda item "{agenda_item.title}" updated successfully!')
            return redirect('events:agenda_item_detail', pk=pk)
    else:
        form = AgendaItemForm(instance=agenda_item)
    
    return render(request, 'events/agenda_item_edit.html', {
        'form': form,
        'agenda_item': agenda_item,
        'event': event
    })


@login_required
def agenda_item_move(request, pk):
    """Move an agenda item from suggestion box to a space."""
    agenda_item = get_object_or_404(AgendaItem, pk=pk)
    event = agenda_item.space.event
    
    # Only users with ADMIN permission can move suggestions
    if not event.can_user_move_suggestions(request.user):
        raise Http404("You don't have permission to move suggestions.")
    
    # Only items in suggestion box can be moved
    if agenda_item.space.space_type != 'suggestion_box':
        messages.error(request, "Only suggested items can be moved.")
        return redirect('events:event_detail', pk=event.pk)
    
    if request.method == 'POST':
        form = MoveAgendaItemForm(event, agenda_item.space, request.POST)
        if form.is_valid():
            target_space = form.cleaned_data['target_space']
            
            # Move the item
            agenda_item.space = target_space
            
            # Set new order to be last in target space
            max_order = target_space.agenda_items.aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            agenda_item.order = max_order + 1
            
            agenda_item.save()
            
            messages.success(request, f'Moved "{agenda_item.title}" to {target_space.name}!')
            return redirect('events:event_detail', pk=event.pk)
    else:
        form = MoveAgendaItemForm(event, agenda_item.space)
    
    return render(request, 'events/agenda_item_move.html', {
        'form': form,
        'agenda_item': agenda_item,
        'event': event
    })


@login_required
@require_POST
def add_comment(request, item_pk):
    """Add a comment to an agenda item via AJAX."""
    agenda_item = get_object_or_404(AgendaItem, pk=item_pk)
    event = agenda_item.space.event
    
    # Check if user can comment
    if not agenda_item.can_user_comment(request.user, event):
        return JsonResponse({'error': 'You do not have permission to comment.'}, status=403)
    
    form = AgendaCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.agenda_item = agenda_item
        comment.author = request.user
        comment.save()
        
        return JsonResponse({
            'success': True,
            'comment': {
                'author': comment.author.get_full_name() or comment.author.username,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p')
            }
        })
    
    return JsonResponse({'error': 'Invalid comment data.'}, status=400)
        


def event_detail(request, pk):
    """
    Display event details. Public events can be viewed by anyone,
    shared events require appropriate permissions.
    """
    event = get_object_or_404(Event, pk=pk)
    
    # Check permissions
    user_permission = event.get_user_permission(request.user)
    
    if not user_permission:
        raise Http404("Event not found or you don't have permission to view it.")
    
    # Get user's invitation if they have one
    invitation = None
    if request.user.is_authenticated:
        try:
            invitation = EventInvitation.objects.get(event=event, invitee=request.user)
        except EventInvitation.DoesNotExist:
            pass  # No invitation is fine - user might be viewing a public event
    
    # Get spaces with their agenda items
    spaces = event.spaces.prefetch_related('agenda_items__comments').all()
    
    # Check if user can suggest agenda items
    can_suggest = event.can_user_suggest_agenda_items(request.user)
    can_move_suggestions = event.can_user_move_suggestions(request.user)
    
    context = {
        'event': event,
        'invitation': invitation,
        'spaces': spaces,
        'user_permission': user_permission,
        'can_suggest': can_suggest,
        'can_move_suggestions': can_move_suggestions,
        'rsvp_form': RSVPForm(instance=invitation) if invitation else None,
    }
    
    return render(request, 'events/event_detail.html', context)