from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from .models import Story, Character, Setting, Plot, Scene, CharacterRelationship, Note, CharacterSceneMotivation
from .forms import StoryForm, CharacterForm, SettingForm, PlotForm, SceneForm, CharacterRelationshipForm, NoteForm
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.contenttypes.models import ContentType


def story_list(request):
    stories = Story.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'storycraft/story_list.html', {'stories': stories})

#@login_required
def create_story(request):
    if request.method == 'POST':
        form = StoryForm(request.POST)
        if form.is_valid():
            story = form.save(commit=False)
            story.user = request.user
            story.save()
            
            # Create default plot
            story.create_default_plot()
            
            return redirect('storycraft:story_detail', story_id=story.id)
    else:
        form = StoryForm()
    
    return render(request, 'storycraft/create_story.html', {'form': form})

def story_detail(request, story_id):
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

def edit_story(request, story_id):
    story = get_object_or_404(Story, id=story_id, user=request.user)
    
    if request.method == 'POST':
        form = StoryForm(request.POST, instance=story)
        if form.is_valid():
            form.save()
            return redirect('storycraft:story_detail', story_id=story.id)
    else:
        form = StoryForm(instance=story)
    
    return render(request, 'storycraft/edit_story.html', {'form': form, 'story': story})

def delete_story(request, story_id):
    story = get_object_or_404(Story, id=story_id, user=request.user)
    
    if request.method == 'POST':
        story.delete()
        return redirect('storycraft:story_list')
    
    return render(request, 'storycraft/delete_story.html', {'story': story})

def story_network(request, story_id):
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

def story_timeline(request, story_id):
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
def character_list(request, story_id):
    story = get_object_or_404(Story, id=story_id, user=request.user)
    characters = Character.objects.filter(story=story)
    
    return render(request, 'storycraft/character_list.html', {
        'story': story, 
        'characters': characters
    })

def create_character(request, story_id):
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

def character_detail(request, character_id):
    # character = get_object_or_404(Character, id=character_id, story__user=request.user)
    # story = character.story
    
    # Create character JSON
    # character_json = json.dumps({
    #     'id': character.id,
    #     'name': character.name,
    #     'description': character.description,
    #     'age': character.age,
    #     'archetype': character.archetype,
    #     'attributes': character.attributes or {}
    # }, cls=DjangoJSONEncoder)
    
    # context = {
    #     'character': character,
    #     'story': story,
    #     'character_json': character_json,
    # }
    
    # return render(request, 'storycraft/character_detail.html', context)

    # """View for character details page."""
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
        'attributes': character.attributes or {},
        'type': 'Character'
    }, cls=DjangoJSONEncoder)
    
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

    context = {
        'character': character,
        'story': story,
        'character_json': character_json,
        'story_data_json': story_data_json,
    }
    
    return render(request, 'storycraft/character_detail.html', context)

def edit_character(request, character_id):
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

def delete_character(request, character_id):
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
def setting_list(request, story_id):
    story = get_object_or_404(Story, id=story_id, user=request.user)
    settings = Setting.objects.filter(story=story)
    
    return render(request, 'storycraft/setting_list.html', {
        'story': story, 
        'settings': settings
    })

def create_setting(request, story_id):
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

def edit_setting(request, setting_id):
    setting = get_object_or_404(Setting, id=setting_id, story__user=request.user)
    story = setting.story
    
    if request.method == 'POST':
        form = SettingForm(request.POST, instance=setting, story=story)
        if form.is_valid():
            form.save()
            return redirect('storycraft:setting_detail', setting_id=setting.id)
    else:
        form = SettingForm(instance=setting, story=story)
    
    return render(request, 'storycraft/edit_setting.html', {
        'form': form, 
        'setting': setting,
        'story': setting.story
    })

def setting_detail(request, setting_id):
    setting = get_object_or_404(Setting, id=setting_id, story__user=request.user)
    story = setting.story
    children = setting.get_all_children()
    
    return render(request, 'storycraft/setting_detail.html', {
        'setting': setting,
        'story': story,
        'children': children
    })

def delete_setting(request, setting_id):
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
def plot_list(request, story_id):
    story = get_object_or_404(Story, id=story_id, user=request.user)
    plots = Plot.objects.filter(story=story)
    
    return render(request, 'storycraft/plot_list.html', {
        'story': story, 
        'plots': plots
    })

def create_plot(request, story_id):
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

def plot_detail(request, plot_id):
    plot = get_object_or_404(Plot, id=plot_id, story__user=request.user)
    story = plot.story
    
    return render(request, 'storycraft/plot_detail.html', {
        'plot': plot,
        'story': story
    })

def edit_plot(request, plot_id):
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

def delete_plot(request, plot_id):
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
def scene_list(request, story_id):
    story = get_object_or_404(Story, id=story_id, user=request.user)
    scenes = Scene.objects.filter(story=story).order_by('sequence_number')
    
    return render(request, 'storycraft/scene_list.html', {
        'story': story, 
        'scenes': scenes
    })

def create_scene(request, story_id):
    story = get_object_or_404(Story, id=story_id, user=request.user)
    
    if request.method == 'POST':
        form = SceneForm(request.POST, story=story)
        if form.is_valid():
            scene = form.save(commit=False)
            scene.story = story
            scene.save()
            
            # Handle the many-to-many relationship with characters
            selected_characters = []
            if 'characters' in form.cleaned_data:
                selected_characters = form.cleaned_data['characters']
                scene.characters.set(selected_characters)
            
            # Process character motivations from the form
            for character in selected_characters:
                desire_key = f'desire_{character.id}'
                obstacle_key = f'obstacle_{character.id}'
                action_key = f'action_{character.id}'
                
                if desire_key in request.POST or obstacle_key in request.POST or action_key in request.POST:
                    motivation = CharacterSceneMotivation(
                        character=character,
                        scene=scene,
                        desire=request.POST.get(desire_key, ''),
                        obstacle=request.POST.get(obstacle_key, ''),
                        action=request.POST.get(action_key, '')
                    )
                    motivation.save()
            
            return redirect('storycraft:scene_detail', scene_id=scene.id)
    else:
        form = SceneForm(story=story)
    
    return render(request, 'storycraft/create_scene.html', {
        'form': form, 
        'story': story
    })
    
def scene_detail(request, scene_id):
    scene = get_object_or_404(Scene, id=scene_id, story__user=request.user)
    story = scene.story
    
    character_motivations = CharacterSceneMotivation.objects.filter(scene=scene)
    motivation_dict = {m.character_id: m for m in character_motivations}
    
    return render(request, 'storycraft/scene_detail.html', {
        'scene': scene,
        'story': story,
        'character_motivations': motivation_dict
    })

def edit_scene(request, scene_id):
    scene = get_object_or_404(Scene, id=scene_id, story__user=request.user)
    story = scene.story
    
    # Get existing character motivations for this scene
    existing_motivations = CharacterSceneMotivation.objects.filter(scene=scene)
    motivation_dict = {m.character_id: m for m in existing_motivations}
    
    if request.method == 'POST':
        form = SceneForm(request.POST, instance=scene, story=story)
        if form.is_valid():
            form.save()
            
            # Handle the many-to-many relationship with characters
            selected_characters = []
            if 'characters' in form.cleaned_data:
                selected_characters = form.cleaned_data['characters']
                scene.characters.set(selected_characters)
            
            # Process character motivations from the form
            for character in selected_characters:
                desire_key = f'desire_{character.id}'
                obstacle_key = f'obstacle_{character.id}'
                action_key = f'action_{character.id}'
                
                # Check if motivation already exists for this character
                if character.id in motivation_dict:
                    # Update existing motivation
                    motivation = motivation_dict[character.id]
                    motivation.desire = request.POST.get(desire_key, '')
                    motivation.obstacle = request.POST.get(obstacle_key, '')
                    motivation.action = request.POST.get(action_key, '')
                    motivation.save()
                else:
                    # Create new motivation
                    if desire_key in request.POST or obstacle_key in request.POST or action_key in request.POST:
                        motivation = CharacterSceneMotivation(
                            character=character,
                            scene=scene,
                            desire=request.POST.get(desire_key, ''),
                            obstacle=request.POST.get(obstacle_key, ''),
                            action=request.POST.get(action_key, '')
                        )
                        motivation.save()
            
            # Remove motivations for characters no longer in the scene
            CharacterSceneMotivation.objects.filter(
                scene=scene
            ).exclude(
                character__in=selected_characters
            ).delete()
            
            return redirect('storycraft:scene_detail', scene_id=scene.id)
    else:
        form = SceneForm(instance=scene, story=story)
        # Set initial value for the characters field
        form.initial['characters'] = scene.characters.all()
    
    # Pass existing motivations to the template
    character_motivations = {m.character_id: m for m in existing_motivations}
    
    return render(request, 'storycraft/edit_scene.html', {
        'form': form, 
        'scene': scene,
        'story': story,
        'character_motivations': character_motivations
    })

def delete_scene(request, scene_id):
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
def relationship_list(request, story_id):
    story = get_object_or_404(Story, id=story_id, user=request.user)
    relationships = CharacterRelationship.objects.filter(
        source__story=story, target__story=story
    )
    
    return render(request, 'storycraft/relationship_list.html', {
        'story': story, 
        'relationships': relationships
    })

def create_relationship(request, story_id):
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

def edit_relationship(request, relationship_id):
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

def delete_relationship(request, relationship_id):
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

def delete_story(request, story_id):
    story_to_delete = get_object_or_404(Story, id=story_id, user=request.user)
    
    if request.method == 'POST':
        story_to_delete.delete()
        return redirect('storycraft:story_list')
    
    stories = Story.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'storycraft/story_list.html', {'stories':stories})

def create_note(request, model_name, object_id):
    # Get the content type based on model name
    model_mapping = {
        'story': Story,
        'character': Character,
        'setting': Setting,
        'plot': Plot,
        'scene': Scene,
        'relationship': CharacterRelationship,
    }
    
    if model_name not in model_mapping:
        return HttpResponseBadRequest("Invalid model name")
        
    model_class = model_mapping[model_name]
    content_type = ContentType.objects.get_for_model(model_class)
    obj = get_object_or_404(model_class, id=object_id)
    
    # Check if user has access to this object
    if hasattr(obj, 'user') and obj.user != request.user:
        return HttpResponseForbidden("You don't have permission to add notes to this object")
    
    if hasattr(obj, 'story') and obj.story.user != request.user:
        return HttpResponseForbidden("You don't have permission to add notes to this object")
    
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.content_type = content_type
            note.object_id = object_id
            note.user = request.user
            note.save()
            
            # Determine the redirect URL based on model
            if model_name == 'story':
                return redirect('storycraft:story_detail', story_id=obj.id)
            elif model_name == 'character':
                return redirect('storycraft:character_detail', character_id=obj.id)
            elif model_name == 'setting':
                return redirect('storycraft:setting_detail', setting_id=obj.id)
            elif model_name == 'plot':
                return redirect('storycraft:plot_detail', plot_id=obj.id)
            elif model_name == 'scene':
                return redirect('storycraft:scene_detail', scene_id=obj.id)
            elif model_name == 'relationship':
                return redirect('storycraft:story_detail', story_id=obj.source.story.id)
    else:
        form = NoteForm()
    
    context = {
        'form': form,
        'object': obj,
        'model_name': model_name,
    }
    
    return render(request, 'storycraft/create_note.html', context)

def edit_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    obj = note.content_object
    
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            
            # Determine where to redirect based on the object type
            model_name = note.content_type.model
            if model_name == 'story':
                return redirect('storycraft:story_detail', story_id=obj.id)
            elif model_name == 'character':
                return redirect('storycraft:character_detail', character_id=obj.id)
            elif model_name == 'setting':
                return redirect('storycraft:setting_detail', setting_id=obj.id)
            elif model_name == 'plot':
                return redirect('storycraft:plot_detail', plot_id=obj.id)
            elif model_name == 'scene':
                return redirect('storycraft:scene_detail', scene_id=obj.id)
            elif model_name == 'characterrelationship':
                return redirect('storycraft:story_detail', story_id=obj.source.story.id)
    else:
        form = NoteForm(instance=note)
    
    return render(request, 'storycraft/edit_note.html', {
        'form': form,
        'note': note,
        'object': obj,
    })

def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    obj = note.content_object
    
    if request.method == 'POST':
        # Determine where to redirect based on the object type
        model_name = note.content_type.model
        
        note.delete()
        
        if model_name == 'story':
            return redirect('storycraft:story_detail', story_id=obj.id)
        elif model_name == 'character':
            return redirect('storycraft:character_detail', character_id=obj.id)
        elif model_name == 'setting':
            return redirect('storycraft:setting_detail', setting_id=obj.id)
        elif model_name == 'plot':
            return redirect('storycraft:plot_detail', plot_id=obj.id)
        elif model_name == 'scene':
            return redirect('storycraft:scene_detail', scene_id=obj.id)
        elif model_name == 'characterrelationship':
            return redirect('storycraft:story_detail', story_id=obj.source.story.id)
    
    return render(request, 'storycraft/delete_note.html', {
        'note': note,
        'object': obj,
    })

def note_list(request, model_name, object_id):
    # Get the content type based on model name
    model_mapping = {
        'story': Story,
        'character': Character,
        'setting': Setting,
        'plot': Plot,
        'scene': Scene,
        'relationship': CharacterRelationship,
    }
    
    if model_name not in model_mapping:
        return HttpResponseBadRequest("Invalid model name")
        
    model_class = model_mapping[model_name]
    content_type = ContentType.objects.get_for_model(model_class)
    obj = get_object_or_404(model_class, id=object_id)
    
    # Check if user has access to this object
    if hasattr(obj, 'user') and obj.user != request.user:
        return HttpResponseForbidden("You don't have permission to view notes for this object")
    
    if hasattr(obj, 'story') and obj.story.user != request.user:
        return HttpResponseForbidden("You don't have permission to view notes for this object")
    
    notes = Note.objects.filter(
        content_type=content_type,
        object_id=object_id,
        user=request.user
    ).order_by('-created_at')
    
    context = {
        'notes': notes,
        'object': obj,
        'model_name': model_name,
    }
    
    return render(request, 'storycraft/note_list.html', context)