"""
Example views integration with Storycraft app.
This shows how to use the decorators and sharing functionality in views.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from shares.decorators import share_permission_required, owner_or_permission_required
from shares.models import Share

from storycraft.models import Story, Character, Plot, Scene

from django import template


register = template.Library()

# Example of a view that uses the owner_or_permission_required decorator
@owner_or_permission_required('VIEW')  # Will check if user is owner or has at least VIEW permission
def story_detail(request, story_id):
    """View for displaying a story's details."""
    story = get_object_or_404(Story, id=story_id)
    
    # If we get here, the user has permission to view the story
    characters = story.characters.all()
    plots = story.plots.all()
    settings = story.settings.all()
    scenes = story.scenes.all().order_by('sequence_number')
    
    # Get all shares for this story (if user is the owner)
    shares = []
    if request.user == story.user:
        content_type = ContentType.objects.get_for_model(Story)
        shares = Share.objects.filter(
            content_type=content_type,
            object_id=story.id
        )
    
    return render(request, 'storycraft/story_detail.html', {
        'story': story,
        'characters': characters,
        'plots': plots,
        'settings': settings,
        'scenes': scenes,
        'shares': shares
    })

# Example of a view with higher permission requirement
@owner_or_permission_required('EDIT')  # Requires EDIT permission
def edit_story(request, story_id):
    """View for editing a story."""
    story = get_object_or_404(Story, id=story_id)
    
    if request.method == 'POST':
        # Process form data and update story
        story.title = request.POST.get('title')
        story.description = request.POST.get('description')
        story.save()
        
        messages.success(request, 'Story updated successfully.')
        return redirect('storycraft:story_detail', story_id=story.id)
    
    return render(request, 'storycraft/edit_story.html', {
        'story': story
    })

# Example of a view specifically for shared content
def shared_story(request, story_id):
    """
    View for displaying a shared story.
    This would be called from the share URL.
    """
    story = get_object_or_404(Story, id=story_id)
    
    # Get the share (would typically be handled by the shares app, but shown here for clarity)
    share_id = request.GET.get('share')
    if not share_id:
        # No share ID provided, redirect to normal story detail if user has access
        if request.user == story.user:
            return redirect('storycraft:story_detail', story_id=story.id)
        else:
            share_permission = story.get_share_permissions(request.user)
            if share_permission:
                return redirect('storycraft:story_detail', story_id=story.id)
            else:
                messages.error(request, "You don't have permission to view this story.")
                return redirect('storycraft:story_list')
    
    # A dedicated shared view would be handled by the shares app, 
    # but we show this for demonstration purposes
    share = get_object_or_404(Share, id=share_id)
    
    # Use the story's custom method to get context for the shared view
    context = story.get_shareable_context(request, share)
    
    return render(request, 'storycraft/shared_story.html', context)