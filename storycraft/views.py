from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Story, Character, Setting, Plot, Scene, CharacterRelationship
from .forms import StoryForm, CharacterForm, SettingForm, PlotForm, SceneForm, CharacterRelationshipForm
import json

#@login_required
def story_list(request):
    """View for listing all stories."""
    stories = Story.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'storycraft/story_list.html', {'stories': stories})

#@login_required
def create_story(request):
    """View for creating a new story."""
    if request.method == 'POST':
        form = StoryForm(request.POST)
        if form.is_valid():
            story = form.save(commit=False)
            story.user = request.user
            story.save()
            return redirect('storycraft:story_detail', story_id=story.id)
    else:
        form = StoryForm()
    
    return render(request, 'storycraft/create_story.html', {'form': form})

#@login_required
def story_detail(request, story_id):
    """View for story details page."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    characters = Character.objects.filter(story=story)
    settings = Setting.objects.filter(story=story)
    plots = Plot.objects.filter(story=story)
    scenes = Scene.objects.filter(story=story).order_by('sequence_number')
    relationships = CharacterRelationship.objects.filter(
        source__story=story, target__story=story
    )
    
    context = {
        'story': story,
        'characters': characters,
        'settings': settings,
        'plots': plots,
        'scenes': scenes,
        'relationships': relationships,
    }
    
    return render(request, 'storycraft/story_detail.html', context)

#@login_required
def edit_story(request, story_id):
    """View for editing a story."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    
    if request.method == 'POST':
        form = StoryForm(request.POST, instance=story)
        if form.is_valid():
            form.save()
            return redirect('storycraft:story_detail', story_id=story.id)
    else:
        form = StoryForm(instance=story)
    
    return render(request, 'storycraft/edit_story.html', {'form': form, 'story': story})

#@login_required
def delete_story(request, story_id):
    """View for deleting a story."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    
    if request.method == 'POST':
        story.delete()
        return redirect('storycraft:story_list')
    
    return render(request, 'storycraft/delete_story.html', {'story': story})

#@login_required
def story_network(request, story_id):
    """View for the story network visualization."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    
    context = {
        'story': story,
        'title': f"{story.title} - Network View",
        'nav_tabs': [
            {'name': 'Stories', 'url': 'storycraft:story_list', 'icon': 'fa-book'},
            {'name': 'Network', 'url': 'storycraft:story_network', 'icon': 'fa-project-diagram'},
            {'name': 'Timeline', 'url': 'storycraft:story_timeline', 'icon': 'fa-stream'},
        ],
        'active_tab': 'Network',
    }
    
    return render(request, 'storycraft/story_network.html', context)

#@login_required
def story_timeline(request, story_id):
    """View for the story timeline visualization."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    
    context = {
        'story': story,
        'nav_tabs': [
            {'name': 'Stories', 'url': 'storycraft:story_list', 'icon': 'fa-book'},
            {'name': 'Network', 'url': 'storycraft:story_network', 'icon': 'fa-project-diagram'},
            {'name': 'Timeline', 'url': 'storycraft:story_timeline', 'icon': 'fa-stream'},
        ],
        'active_tab': 'Timeline',
    }
    
    return render(request, 'storycraft/story_timeline.html', context)

# Character-related views
#@login_required
def character_list(request, story_id):
    """View for listing all characters in a story."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    characters = Character.objects.filter(story=story)
    
    return render(request, 'storycraft/character_list.html', {
        'story': story, 
        'characters': characters
    })

#@login_required
def create_character(request, story_id):
    """View for creating a new character."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    
    if request.method == 'POST':
        form = CharacterForm(request.POST)
        if form.is_valid():
            character = form.save(commit=False)
            character.story = story
            character.save()
            return redirect('storycraft:story_detail', story_id=story.id)
    else:
        form = CharacterForm()
    
    return render(request, 'storycraft/create_character.html', {
        'form': form, 
        'story': story
    })

#@login_required
def character_detail(request, character_id):
    """View for character details page."""
    character = get_object_or_404(Character, id=character_id, story__user=request.user)
    story = character.story
    
    # Prepare data for Vue component
    characters = Character.objects.filter(story=story)
    settings = Setting.objects.filter(story=story)
    plots = Plot.objects.filter(story=story)
    scenes = Scene.objects.filter(story=story).order_by('sequence_number')
    relationships = CharacterRelationship.objects.filter(
        source__story=story, target__story=story
    )
    
    # Convert to JSON for Vue
    character_json = json.dumps({
        'id': character.id,
        'name': character.name,
        'description': character.description,
        'age': character.age,
        'archetype': character.archetype,
        'attributes': character.attributes,
        'type': 'Character'
    })
    
    # Build full story data for relationships and references
    story_data = {
        'id': story.id,
        'title': story.title,
        'characters': [],
        'settings': [],
        'plots': [],
        'scenes': [],
        'relationships': []
    }
    
    # Add characters data
    for char in characters:
        story_data['characters'].append({
            'id': char.id,
            'name': char.name,
            'description': char.description,
            'age': char.age,
            'archetype': char.archetype,
            'attributes': char.attributes,
            'type': 'Character'
        })
    
    # Add settings data
    for setting in settings:
        story_data['settings'].append({
            'id': setting.id,
            'name': setting.name,
            'description': setting.description,
            'attributes': setting.attributes,
            'type': 'Setting'
        })
    
    # Add plots data
    for plot in plots:
        story_data['plots'].append({
            'id': plot.id,
            'name': plot.name,
            'description': plot.description,
            'plot_type': plot.plot_type,
            'type': 'Plot'
        })
    
    # Add scenes data
    for scene in scenes:
        scene_data = {
            'id': scene.id,
            'name': scene.name,
            'description': scene.description,
            'setting_id': scene.setting_id,
            'plot_id': scene.plot_id,
            'sequence_number': scene.sequence_number,
            'status': scene.status,
            'metadata': scene.metadata,
            'characters': list(scene.characters.values_list('id', flat=True)),
            'type': 'Scene'
        }
        story_data['scenes'].append(scene_data)
    
    # Add relationship data
    for rel in relationships:
        rel_data = {
            'id': rel.id,
            'source_id': rel.source_id,
            'target_id': rel.target_id,
            'relationship': rel.relationship,
            'description': rel.description
        }
        story_data['relationships'].append(rel_data)
    
    story_data_json = json.dumps(story_data)
    
    return render(request, 'storycraft/character_detail.html', {
        'character': character,
        'character_json': character_json,
        'story_data_json': story_data_json,
        'story': story
    })

#@login_required
def edit_character(request, character_id):
    """View for editing a character."""
    character = get_object_or_404(Character, id=character_id, story__user=request.user)
    
    if request.method == 'POST':
        form = CharacterForm(request.POST, instance=character)
        if form.is_valid():
            form.save()
            return redirect('storycraft:character_detail', character_id=character.id)
    else:
        form = CharacterForm(instance=character)
    
    return render(request, 'storycraft/edit_character.html', {
        'form': form, 
        'character': character,
        'story': character.story
    })

#@login_required
def delete_character(request, character_id):
    """View for deleting a character."""
    character = get_object_or_404(Character, id=character_id, story__user=request.user)
    story_id = character.story.id
    
    if request.method == 'POST':
        character.delete()
        return redirect('storycraft:story_detail', story_id=story_id)
    
    return render(request, 'storycraft/delete_character.html', {
        'character': character,
        'story': character.story
    })

# Setting-related views
#@login_required
def setting_list(request, story_id):
    """View for listing all settings in a story."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    settings = Setting.objects.filter(story=story)
    
    return render(request, 'storycraft/setting_list.html', {
        'story': story, 
        'settings': settings
    })

#@login_required
def create_setting(request, story_id):
    """View for creating a new setting."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    
    if request.method == 'POST':
        form = SettingForm(request.POST)
        if form.is_valid():
            setting = form.save(commit=False)
            setting.story = story
            setting.save()
            return redirect('storycraft:story_detail', story_id=story.id)
    else:
        form = SettingForm()
    
    return render(request, 'storycraft/create_setting.html', {
        'form': form, 
        'story': story
    })

#@login_required
def setting_detail(request, setting_id):
    """View for setting details page."""
    setting = get_object_or_404(Setting, id=setting_id, story__user=request.user)
    story = setting.story
    
    return render(request, 'storycraft/setting_detail.html', {
        'setting': setting,
        'story': story
    })

#@login_required
def edit_setting(request, setting_id):
    """View for editing a setting."""
    setting = get_object_or_404(Setting, id=setting_id, story__user=request.user)
    
    if request.method == 'POST':
        form = SettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            return redirect('storycraft:setting_detail', setting_id=setting.id)
    else:
        form = SettingForm(instance=setting)
    
    return render(request, 'storycraft/edit_setting.html', {
        'form': form, 
        'setting': setting,
        'story': setting.story
    })

#@login_required
def delete_setting(request, setting_id):
    """View for deleting a setting."""
    setting = get_object_or_404(Setting, id=setting_id, story__user=request.user)
    story_id = setting.story.id
    
    if request.method == 'POST':
        setting.delete()
        return redirect('storycraft:story_detail', story_id=story_id)
    
    return render(request, 'storycraft/delete_setting.html', {
        'setting': setting,
        'story': setting.story
    })

# Plot-related views
#@login_required
def plot_list(request, story_id):
    """View for listing all plots in a story."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    plots = Plot.objects.filter(story=story)
    
    return render(request, 'storycraft/plot_list.html', {
        'story': story, 
        'plots': plots
    })

#@login_required
def create_plot(request, story_id):
    """View for creating a new plot."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    
    if request.method == 'POST':
        form = PlotForm(request.POST)
        if form.is_valid():
            plot = form.save(commit=False)
            plot.story = story
            plot.save()
            return redirect('storycraft:story_detail', story_id=story.id)
    else:
        form = PlotForm()
    
    return render(request, 'storycraft/create_plot.html', {
        'form': form, 
        'story': story
    })

#@login_required
def plot_detail(request, plot_id):
    """View for plot details page."""
    plot = get_object_or_404(Plot, id=plot_id, story__user=request.user)
    story = plot.story
    
    return render(request, 'storycraft/plot_detail.html', {
        'plot': plot,
        'story': story
    })

#@login_required
def edit_plot(request, plot_id):
    """View for editing a plot."""
    plot = get_object_or_404(Plot, id=plot_id, story__user=request.user)
    
    if request.method == 'POST':
        form = PlotForm(request.POST, instance=plot)
        if form.is_valid():
            form.save()
            return redirect('storycraft:plot_detail', plot_id=plot.id)
    else:
        form = PlotForm(instance=plot)
    
    return render(request, 'storycraft/edit_plot.html', {
        'form': form, 
        'plot': plot,
        'story': plot.story
    })

#@login_required
def delete_plot(request, plot_id):
    """View for deleting a plot."""
    plot = get_object_or_404(Plot, id=plot_id, story__user=request.user)
    story_id = plot.story.id
    
    if request.method == 'POST':
        plot.delete()
        return redirect('storycraft:story_detail', story_id=story_id)
    
    return render(request, 'storycraft/delete_plot.html', {
        'plot': plot,
        'story': plot.story
    })

# Scene-related views
#@login_required
def scene_list(request, story_id):
    """View for listing all scenes in a story."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    scenes = Scene.objects.filter(story=story).order_by('sequence_number')
    
    return render(request, 'storycraft/scene_list.html', {
        'story': story, 
        'scenes': scenes
    })

#@login_required
def create_scene(request, story_id):
    """View for creating a new scene."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    
    if request.method == 'POST':
        form = SceneForm(request.POST, story=story)
        if form.is_valid():
            scene = form.save(commit=False)
            scene.story = story
            scene.save()
            
            # Handle the many-to-many relationship with characters
            if 'characters' in form.cleaned_data:
                scene.characters.set(form.cleaned_data['characters'])
            
            return redirect('storycraft:story_detail', story_id=story.id)
    else:
        form = SceneForm(story=story)
    
    return render(request, 'storycraft/create_scene.html', {
        'form': form, 
        'story': story
    })

#@login_required
def scene_detail(request, scene_id):
    """View for scene details page."""
    scene = get_object_or_404(Scene, id=scene_id, story__user=request.user)
    story = scene.story
    
    return render(request, 'storycraft/scene_detail.html', {
        'scene': scene,
        'story': story
    })

#@login_required
def edit_scene(request, scene_id):
    """View for editing a scene."""
    scene = get_object_or_404(Scene, id=scene_id, story__user=request.user)
    story = scene.story
    
    if request.method == 'POST':
        form = SceneForm(request.POST, instance=scene, story=story)
        if form.is_valid():
            form.save()
            
            # Handle the many-to-many relationship with characters
            if 'characters' in form.cleaned_data:
                scene.characters.set(form.cleaned_data['characters'])
            
            return redirect('storycraft:scene_detail', scene_id=scene.id)
    else:
        form = SceneForm(instance=scene, story=story)
        # Set initial value for the characters field
        form.initial['characters'] = scene.characters.all()
    
    return render(request, 'storycraft/edit_scene.html', {
        'form': form, 
        'scene': scene,
        'story': story
    })

#@login_required
def delete_scene(request, scene_id):
    """View for deleting a scene."""
    scene = get_object_or_404(Scene, id=scene_id, story__user=request.user)
    story_id = scene.story.id
    
    if request.method == 'POST':
        scene.delete()
        return redirect('storycraft:story_detail', story_id=story_id)
    
    return render(request, 'storycraft/delete_scene.html', {
        'scene': scene,
        'story': scene.story
    })

# Relationship-related views
#@login_required
def relationship_list(request, story_id):
    """View for listing all relationships in a story."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    relationships = CharacterRelationship.objects.filter(
        source__story=story, target__story=story
    )
    
    return render(request, 'storycraft/relationship_list.html', {
        'story': story, 
        'relationships': relationships
    })

#@login_required
def create_relationship(request, story_id):
    """View for creating a new relationship."""
    story = get_object_or_404(Story, id=story_id, user=request.user)
    
    if request.method == 'POST':
        form = CharacterRelationshipForm(request.POST, story=story)
        if form.is_valid():
            relationship = form.save()
            return redirect('storycraft:story_detail', story_id=story.id)
    else:
        form = CharacterRelationshipForm(story=story)
    
    return render(request, 'storycraft/create_relationship.html', {
        'form': form, 
        'story': story
    })

#@login_required
def edit_relationship(request, relationship_id):
    """View for editing a relationship."""
    relationship = get_object_or_404(
        CharacterRelationship, 
        id=relationship_id, 
        source__story__user=request.user
    )
    story = relationship.source.story
    
    if request.method == 'POST':
        form = CharacterRelationshipForm(request.POST, instance=relationship, story=story)
        if form.is_valid():
            form.save()
            return redirect('storycraft:story_detail', story_id=story.id)
    else:
        form = CharacterRelationshipForm(instance=relationship, story=story)
    
    return render(request, 'storycraft/edit_relationship.html', {
        'form': form, 
        'relationship': relationship,
        'story': story
    })

#@login_required
def delete_relationship(request, relationship_id):
    """View for deleting a relationship."""
    relationship = get_object_or_404(
        CharacterRelationship, 
        id=relationship_id, 
        source__story__user=request.user
    )
    story_id = relationship.source.story.id
    
    if request.method == 'POST':
        relationship.delete()
        return redirect('storycraft:story_detail', story_id=story_id)
    
    return render(request, 'storycraft/delete_relationship.html', {
        'relationship': relationship,
        'story': relationship.source.story
    })