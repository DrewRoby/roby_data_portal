import os
import random
import requests
import math
import time
import logging

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from typing import List, Dict, Tuple
from storycraft.models import Story, Character, Setting, Plot, Scene, CharacterRelationship
from .decorators import api_access_required
from .models import PlacesSearchCache, APIUsageLog

logger = logging.getLogger(__name__)


# Existing image API endpoints
@api_view(['GET'])
def get_images(request):
    """
    API endpoint that returns a list of all images in the rsps directory.
    """
    # Path to the rsps directory, relative to your MEDIA_ROOT
    rsps_dir = os.path.join(settings.MEDIA_ROOT, 'images', 'rsps')
    
    # Check if directory exists
    if not os.path.exists(rsps_dir):
        return Response(
            {"error": "Image directory not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get all files in the directory
    try:
        files = os.listdir(rsps_dir)
        
        # Filter out non-image files by extension
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        image_files = [
            file for file in files 
            if os.path.splitext(file)[1].lower() in image_extensions
        ]
        
        return Response({
            "status": "success",
            "count": len(image_files),
            "images": image_files
        })
    
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_random_image(request):
    """
    API endpoint that returns a random image from the rsps directory.
    """
    # Path to the rsps directory, relative to your MEDIA_ROOT
    rsps_dir = os.path.join(settings.MEDIA_ROOT, 'images', 'rsps')
    
    # Check if directory exists
    if not os.path.exists(rsps_dir):
        return Response(
            {"error": "Image directory not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get all files in the directory
    try:
        files = os.listdir(rsps_dir)
        
        # Filter out non-image files by extension
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        image_files = [
            file for file in files 
            if os.path.splitext(file)[1].lower() in image_extensions
        ]
        
        if not image_files:
            return Response(
                {"error": "No images found in directory"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Select a random image
        random_image = random.choice(image_files)
        
        # Construct the URL (adjust as needed for your MEDIA_URL configuration)
        image_url = f"{settings.MEDIA_URL}images/rsps/{random_image}"
        
        return Response({
            "status": "success",
            "image": random_image,
            "url": image_url
        })
    
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Storycraft API endpoints
@api_view(['GET'])
def story_list_api(request):
    """API endpoint that returns a list of user's stories."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        stories = Story.objects.filter(user=user).order_by('-updated_at')
        
        data = [{
            'id': story.id,
            'title': story.title,
            'description': story.description,
            'created_at': story.created_at,
            'updated_at': story.updated_at,
            'character_count': story.characters.count(),
            'scene_count': story.scenes.count(),
        } for story in stories]
        
        return Response({
            'status': 'success',
            'count': len(data),
            'stories': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def story_detail_api(request, story_id):
    """API endpoint that returns details for a specific story."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        story = get_object_or_404(Story, id=story_id, user=user)
        
        data = {
            'id': story.id,
            'title': story.title,
            'description': story.description,
            'created_at': story.created_at,
            'updated_at': story.updated_at,
            'character_count': story.characters.count(),
            'setting_count': story.settings.count(),
            'plot_count': story.plots.count(),
            'scene_count': story.scenes.count(),
        }
        
        return Response({
            'status': 'success',
            'story': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def story_graph_data(request, story_id):
    """API endpoint that returns all data needed for the story graph visualization."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        story = get_object_or_404(Story, id=story_id, user=user)
        
        # Get all story elements
        characters = Character.objects.filter(story=story)
        settings = Setting.objects.filter(story=story)
        plots = Plot.objects.filter(story=story)
        scenes = Scene.objects.filter(story=story)
        
        # Get character relationships
        character_ids = characters.values_list('id', flat=True)
        relationships = CharacterRelationship.objects.filter(
            source__in=character_ids,
            target__in=character_ids
        )
        
        # Build data structure for the graph visualization
        data = {
            'id': story.id,
            'title': story.title,
            'characters': list(characters.values('id', 'name', 'description', 'age', 'archetype', 'attributes')),
            'settings': list(settings.values('id', 'name', 'description', 'attributes')),
            'plots': list(plots.values('id', 'name', 'description', 'plot_type')),
            'scenes': [],
            'relationships': []
        }
        
        # Add type field to each entity
        for item in data['characters']:
            item['type'] = 'Character'
        for item in data['settings']:
            item['type'] = 'Setting'
        for item in data['plots']:
            item['type'] = 'Plot'
        
        # Build scene data with references
        for scene in scenes:
            scene_data = {
                'id': scene.id,
                'type': 'Scene',
                'name': scene.name,
                'description': scene.description,
                'content': scene.content,
                'setting_id': scene.setting_id,
                'plot_id': scene.plot_id,
                'sequence_number': scene.sequence_number,
                'status': scene.status,
                'metadata': scene.metadata,
                'characters': list(scene.characters.values_list('id', flat=True))
            }
            data['scenes'].append(scene_data)
        
        # Build relationship data
        for rel in relationships:
            rel_data = {
                'id': rel.id,
                'source_id': rel.source_id,
                'target_id': rel.target_id,
                'relationship': rel.relationship,
                'description': rel.description
            }
            data['relationships'].append(rel_data)
        
        return Response(data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Character endpoints
@api_view(['GET'])
def character_list_api(request, story_id):
    """API endpoint that returns all characters for a specific story."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        story = get_object_or_404(Story, id=story_id, user=user)
        characters = Character.objects.filter(story=story)
        
        data = list(characters.values(
            'id', 'name', 'description', 'age', 'archetype', 'attributes', 'created_at', 'updated_at'
        ))
        
        return Response({
            'status': 'success',
            'count': len(data),
            'characters': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def character_detail_api(request, character_id):
    """API endpoint that returns details for a specific character."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        character = get_object_or_404(Character, id=character_id, story__user=user)
        
        data = {
            'id': character.id,
            'name': character.name,
            'description': character.description,
            'age': character.age,
            'archetype': character.archetype,
            'attributes': character.attributes,
            'created_at': character.created_at,
            'updated_at': character.updated_at,
            'story_id': character.story_id
        }
        
        return Response({
            'status': 'success',
            'character': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def character_create_api(request):
    """API endpoint to create a new character."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Get the story
        story_id = request.data.get('story_id')
        if not story_id:
            return Response({"error": "Story ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        story = get_object_or_404(Story, id=story_id, user=user)
        
        # Create the character
        character = Character.objects.create(
            story=story,
            name=request.data.get('name'),
            description=request.data.get('description'),
            age=request.data.get('age'),
            archetype=request.data.get('archetype'),
            attributes=request.data.get('attributes', {})
        )
        
        return Response({
            'status': 'success',
            'message': 'Character created successfully',
            'character': {
                'id': character.id,
                'name': character.name,
                'story_id': character.story_id
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'PATCH'])
def character_update_api(request, character_id):
    """API endpoint to update a character."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        character = get_object_or_404(Character, id=character_id, story__user=user)
        
        # Update fields
        if 'name' in request.data:
            character.name = request.data['name']
        if 'description' in request.data:
            character.description = request.data['description']
        if 'age' in request.data:
            character.age = request.data['age']
        if 'archetype' in request.data:
            character.archetype = request.data['archetype']
        if 'attributes' in request.data:
            character.attributes = request.data['attributes']
            
        character.save()
        
        return Response({
            'status': 'success',
            'message': 'Character updated successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def character_delete_api(request, character_id):
    """API endpoint to delete a character."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        character = get_object_or_404(Character, id=character_id, story__user=user)
        character.delete()
        
        return Response({
            'status': 'success',
            'message': 'Character deleted successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Setting endpoints
@api_view(['GET'])
def setting_list_api(request, story_id):
    """API endpoint that returns all settings for a specific story."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        story = get_object_or_404(Story, id=story_id, user=user)
        settings = Setting.objects.filter(story=story)
        
        data = list(settings.values(
            'id', 'name', 'description', 'attributes', 'created_at', 'updated_at'
        ))
        
        return Response({
            'status': 'success',
            'count': len(data),
            'settings': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def setting_detail_api(request, setting_id):
    """API endpoint that returns details for a specific setting."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        setting = get_object_or_404(Setting, id=setting_id, story__user=user)
        
        data = {
            'id': setting.id,
            'name': setting.name,
            'description': setting.description,
            'attributes': setting.attributes,
            'created_at': setting.created_at,
            'updated_at': setting.updated_at,
            'story_id': setting.story_id
        }
        
        return Response({
            'status': 'success',
            'setting': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def setting_create_api(request):
    """API endpoint to create a new setting."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Get the story
        story_id = request.data.get('story_id')
        if not story_id:
            return Response({"error": "Story ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        story = get_object_or_404(Story, id=story_id, user=user)
        
        # Create the setting
        setting = Setting.objects.create(
            story=story,
            name=request.data.get('name'),
            description=request.data.get('description'),
            attributes=request.data.get('attributes', {})
        )
        
        return Response({
            'status': 'success',
            'message': 'Setting created successfully',
            'setting': {
                'id': setting.id,
                'name': setting.name,
                'story_id': setting.story_id
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'PATCH'])
def setting_update_api(request, setting_id):
    """API endpoint to update a setting."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        setting = get_object_or_404(Setting, id=setting_id, story__user=user)
        
        # Update fields
        if 'name' in request.data:
            setting.name = request.data['name']
        if 'description' in request.data:
            setting.description = request.data['description']
        if 'attributes' in request.data:
            setting.attributes = request.data['attributes']
            
        setting.save()
        
        return Response({
            'status': 'success',
            'message': 'Setting updated successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def setting_delete_api(request, setting_id):
    """API endpoint to delete a setting."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        setting = get_object_or_404(Setting, id=setting_id, story__user=user)
        setting.delete()
        
        return Response({
            'status': 'success',
            'message': 'Setting deleted successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def plot_list_api(request, story_id):
    """API endpoint that returns all plots for a specific story."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        story = get_object_or_404(Story, id=story_id, user=user)
        plots = Plot.objects.filter(story=story)
        
        data = list(plots.values(
            'id', 'name', 'description', 'plot_type', 'created_at', 'updated_at'
        ))
        
        return Response({
            'status': 'success',
            'count': len(data),
            'plots': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def plot_detail_api(request, plot_id):
    """API endpoint that returns details for a specific plot."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        plot = get_object_or_404(Plot, id=plot_id, story__user=user)
        
        data = {
            'id': plot.id,
            'name': plot.name,
            'description': plot.description,
            'plot_type': plot.plot_type,
            'created_at': plot.created_at,
            'updated_at': plot.updated_at,
            'story_id': plot.story_id
        }
        
        return Response({
            'status': 'success',
            'plot': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def plot_create_api(request):
    """API endpoint to create a new plot."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Get the story
        story_id = request.data.get('story_id')
        if not story_id:
            return Response({"error": "Story ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        story = get_object_or_404(Story, id=story_id, user=user)
        
        # Create the plot
        plot = Plot.objects.create(
            story=story,
            name=request.data.get('name'),
            description=request.data.get('description'),
            plot_type=request.data.get('plot_type', 'subplot')
        )
        
        return Response({
            'status': 'success',
            'message': 'Plot created successfully',
            'plot': {
                'id': plot.id,
                'name': plot.name,
                'story_id': plot.story_id
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'PATCH'])
def plot_update_api(request, plot_id):
    """API endpoint to update a plot."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        plot = get_object_or_404(Plot, id=plot_id, story__user=user)
        
        # Update fields
        if 'name' in request.data:
            plot.name = request.data['name']
        if 'description' in request.data:
            plot.description = request.data['description']
        if 'plot_type' in request.data:
            plot.plot_type = request.data['plot_type']
            
        plot.save()
        
        return Response({
            'status': 'success',
            'message': 'Plot updated successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def plot_delete_api(request, setting_id):
    """API endpoint to delete a plot."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        setting = get_object_or_404(Plot, id=plot_id, story__user=user)
        setting.delete()
        
        return Response({
            'status': 'success',
            'message': 'Setting deleted successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#Scene views
def scene_list_api(request, story_id):
    """API endpoint that returns all scenes for a specific story."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        story = get_object_or_404(Story, id=story_id, user=user)
        scenes = Scene.objects.filter(story=story)
        
        data = list(scenes.values(
            'id', 'name', 'description', 'content', 'story', 'plot', 'setting', 'created_at', 'updated_at'
        ))
        
        return Response({
            'status': 'success',
            'count': len(data),
            'scenes': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def scene_detail_api(request, scene_id):
    """API endpoint that returns details for a specific scene."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        scene = get_object_or_404(Scene, id=scene_id, story__user=user)
        
        data = {
            'id': scene.id,
            'name': scene.name,
            'description': scene.description,
            'content': scene.content,
            'story': scene.story,
            'plot': scene.plot,
            'setting': scene.setting,
            'created_at': scene.created_at,
            'updated_at': scene.updated_at,
        }
        
        return Response({
            'status': 'success',
            'scene': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def scene_create_api(request):
    """API endpoint to create a new scene."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Get the story
        story_id = request.data.get('story_id')
        if not story_id:
            return Response({"error": "Story ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        story = get_object_or_404(Story, id=story_id, user=user)
        
        # Create the scene
        scene = scene.objects.create(
            name=request.data.get('name'),
            description=request.data.get('description'),
            content=request.data.get('content'),
            story=request.data.get('story'),
            plot=request.data.get('plot'),
            setting=request.data.get('setting'),
        )
        
        return Response({
            'status': 'success',
            'message': 'scene created successfully',
            'scene': {
                'id': scene.id,
                'name': scene.name,
                'story_id': scene.story_id
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'PATCH'])
def scene_update_api(request, scene_id):
    """API endpoint to update a scene."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        scene = get_object_or_404(scene, id=scene_id, story__user=user)
        
        # Update fields
        if 'name' in request.data:
            scene.name = request.data['name']
        if 'description' in request.data:
            scene.description = request.data['description']
        if 'content' in request.data:
            scene.content = request.data['content']
        if 'story' in request.data:
            scene.story = request.data['story']
        if 'plot' in request.data:
            scene.plot = request.data['plot']
        if 'setting' in request.data:
            scene.setting = request.data['setting']
            
        scene.save()
        
        return Response({
            'status': 'success',
            'message': 'scene updated successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def scene_delete_api(request, scene_id):
    """API endpoint to delete a scene."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        scene = get_object_or_404(scene, id=scene_id, story__user=user)
        scene.delete()
        
        return Response({
            'status': 'success',
            'message': 'Setting deleted successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#Relationship views
@api_view(['GET'])
def relationship_list_api(request, story_id):
    """API endpoint that returns all relationships for a specific story."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        story = get_object_or_404(Story, id=story_id, user=user)
        relationships = Relationship.objects.filter(story=story)
        
        data = list(relationships.values(
            'id', 'source', 'target', 'relationship', 'description'
        ))
        
        return Response({
            'status': 'success',
            'count': len(data),
            'relationships': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def relationship_detail_api(request, relationship_id):
    """API endpoint that returns details for a specific relationship."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        relationship = get_object_or_404(Relationship, id=relationship_id, story__user=user)
        
        data = {
            'id': relationship.id,
            'source': relationship.source,
            'target': relationship.target,
            'relationship': relationship.relationship,
            'description': relationship.description,
        }
        
        return Response({
            'status': 'success',
            'relationship': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def relationship_create_api(request):
    """API endpoint to create a new relationship."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Get the story
        story_id = request.data.get('story_id')
        if not story_id:
            return Response({"error": "Story ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        story = get_object_or_404(Story, id=story_id, user=user)
        
        # Create the relationship
        relationship = relationship.objects.create(
            source=request.data.get('source'),
            target=request.data.get('target'),
            relationship=request.data.get('relationship'),
            description=request.data.get('description')
        )
        
        return Response({
            'status': 'success',
            'message': 'relationship created successfully',
            'relationship': {
                'id': relationship.id,
                'name': relationship.name,
                'story_id': relationship.story_id
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'PATCH'])
def relationship_update_api(request, relationship_id):
    """API endpoint to update a relationship."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        relationship = get_object_or_404(relationship, id=relationship_id, story__user=user)
        
        # Update fields
        if 'source' in request.data:
            relationship.source = request.data['source']
        if 'target' in request.data:
            relationship.target = request.data['target']
        if 'relationship' in request.data:
            relationship.relationship = request.data['relationship']
        if 'description' in request.data:
            relationship.description = request.data['description']
            
        relationship.save()
        
        return Response({
            'status': 'success',
            'message': 'relationship updated successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def relationship_delete_api(request, relationship_id):
    """API endpoint to delete a relationship."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        relationship = get_object_or_404(relationship, id=relationship_id, story__user=user)
        relationship.delete()
        
        return Response({
            'status': 'success',
            'message': 'Setting deleted successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def user_apps_api(request):
    """API endpoint that returns the list of apps a user has access to."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Get the user's app access
        from portal.models import UserAppAccess, App
        
        # Get apps that the user has access to
        user_apps = App.objects.filter(
            id__in=UserAppAccess.objects.filter(user=user).values_list('app_id', flat=True)
        ).order_by('order', 'name')
        
        # If no specific apps are assigned, fall back to default apps
        if not user_apps.exists():
            user_apps = App.objects.filter(is_default=True).order_by('order', 'name')
        
        data = []
        for app in user_apps:
            app_data = {
                'app_id': app.app_id,
                'name': app.name,
                'description': app.description,
                'icon': app.icon,
                'background_color': app.background_color,
                'link': app.link,
                'is_default': app.is_default,
                'order': app.order
            }
            data.append(app_data)
        
        return Response({
            'status': 'success',
            'count': len(data),
            'apps': data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_access_required('find_places')
@api_view(['POST'])
def find_places(request):
    """
    Find places using Google Places API (New) with caching
    """
    try:
        # Validate input
        lat = request.data.get('latitude')
        lon = request.data.get('longitude')
        radius = request.data.get('radius_meters', 1000)
        category = request.data.get('category', 'all')
        place_types = request.data.get('place_types', [])
        limit = request.data.get('limit', 20)
        
        # Validation (same as before)
        if lat is None or lon is None:
            return Response({'error': 'latitude and longitude are required'}, status=400)
            
        try:
            lat = float(lat)
            lon = float(lon)
            radius = int(radius)
            limit = int(limit)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid numeric values'}, status=400)
        
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return Response({'error': 'Invalid coordinates'}, status=400)
            
        if radius > 5000:
            return Response({'error': 'Radius cannot exceed 5000 meters'}, status=400)
            
        if limit > 50:
            return Response({'error': 'Limit cannot exceed 50 results'}, status=400)
            
        if category not in ['commercial', 'residential', 'all']:
            return Response({'error': 'Category must be commercial, residential, or all'}, status=400)
        
        # Try to get cached results first
        cache_data = PlacesSearchCache.get_cached_results(
            latitude=lat,
            longitude=lon,
            radius_meters=radius,
            category=category,
            place_types=place_types,
            max_age_hours=2  # Cache for 2 hours
        )
        
        # Use cache only if:
        # 1. Cache exists AND
        # 2. Cache has actual results (not an empty search)
        # OR cache is very recent (< 1 minute) even if empty (to avoid repeated API calls for truly empty areas)
        use_cache = False
        if cache_data is not None:
            cache_age_minutes = (timezone.now() - cache_data['created_at']).total_seconds() / 60
            use_cache = (cache_data['has_results'] or cache_age_minutes < 5)
        
        if use_cache:
            # Return cached results
            places = cache_data['results'][:limit]  # Apply limit to cached results
            
            # Get current usage counts
            today = timezone.now().date()
            daily_count = APIUsageLog.objects.filter(
                user=request.user,
                endpoint='find_places',
                timestamp__date=today,
                success=True
            ).count()
            
            cache_age_minutes = (timezone.now() - cache_data['created_at']).total_seconds() / 60
            
            return Response({
                'total_found': len(places),
                'places': places,
                'from_cache': True,
                'cache_age_minutes': round(cache_age_minutes, 1),
                'user_daily_usage': daily_count + 1,
                'user_daily_limit': request.user.profile.api_daily_limit
            })
        
        # No cached results, call Google API
        places_finder = GooglePlacesFinder()
        places = places_finder.find_places_nearby(
            latitude=lat,
            longitude=lon,
            radius_meters=radius,
            category=category,
            place_types=place_types,
            limit=limit
        )
        
        # Cache the results for future use
        PlacesSearchCache.cache_results(
            latitude=lat,
            longitude=lon,
            radius_meters=radius,
            category=category,
            place_types=place_types,
            results=places
        )
        
        # Get current usage counts
        today = timezone.now().date()
        daily_count = APIUsageLog.objects.filter(
            user=request.user,
            endpoint='find_places',
            timestamp__date=today,
            success=True
        ).count()
        
        return Response({
            'total_found': len(places),
            'places': places,
            'from_cache': False,
            'user_daily_usage': daily_count + 1,
            'user_daily_limit': request.user.profile.api_daily_limit
        })
        
    except Exception as e:
        logger.error(f"Error in find_places: {str(e)}")
        return Response({'error': 'Internal server error'}, status=500)


class GooglePlacesFinder:
    """
    Google Places API (New) integration for finding nearby places
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY not found in settings")
        
        self.base_url = "https://places.googleapis.com/v1/places:searchNearby"
        self.session = requests.Session()
    
    def find_places_nearby(self, latitude, longitude, radius_meters, category, place_types, limit):
        """
        Find places near a location using Google Places API (New)
        """
        all_places = []
        next_page_token = None
        
        # Define place types based on category
        search_types = self._get_place_types_for_category(category, place_types)
        
        # Handle pagination
        while len(all_places) < limit:
            batch_limit = min(20, limit - len(all_places))  # Google max is 20 per request
            
            places_batch, next_token = self._search_places_batch(
                latitude=latitude,
                longitude=longitude,
                radius_meters=radius_meters,
                place_types=search_types,
                limit=batch_limit,
                page_token=next_page_token
            )
            
            all_places.extend(places_batch)
            
            # Check if we have more pages and haven't hit our limit
            if not next_token or len(all_places) >= limit:
                break
                
            next_page_token = next_token
        
        return all_places[:limit]
    
    def _get_place_types_for_category(self, category, custom_types):
        """
        Get Google Places types based on category
        """
        if custom_types:
            return custom_types
        
        if category == 'commercial':
            return [
                'store', 'restaurant', 'gas_station', 'bank', 'hospital',
                'pharmacy', 'grocery_store', 'clothing_store', 'electronics_store',
                'shopping_mall', 'cafe', 'bar', 'gym', 'beauty_salon'
            ]
        elif category == 'residential':
            # return ['premise', 'subpremise', 'neighborhood']
            return ['apartment_building','apartment_complex','condominium_complex','housing_complex']
        else:  # 'all'
            return []  # Empty list means search all types
    
    def _search_places_batch(self, latitude, longitude, radius_meters, place_types, limit, page_token=None):
        """
        Search a single batch of places
        """
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.location,places.types'
        }
        
        payload = {
            'locationRestriction': {
                'circle': {
                    'center': {
                        'latitude': latitude,
                        'longitude': longitude
                    },
                    'radius': radius_meters
                }
            },
            'maxResultCount': limit
        }
        
        # Add place types if specified
        if place_types:
            payload['includedTypes'] = place_types
        
        # Add page token if continuing pagination
        if page_token:
            payload['pageToken'] = page_token
        
        try:
            response = self.session.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            places = []
            next_token = data.get('nextPageToken')
            
            for place in data.get('places', []):
                processed_place = self._process_place_result(place)
                if processed_place:
                    places.append(processed_place)
            
            return places, next_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Places API error: {str(e)}")
            return [], None
    
    def _process_place_result(self, place):
        """
        Process a single place result from Google Places API
        """
        try:
            name = place.get('displayName', {}).get('text', 'Unnamed Place')
            address = place.get('formattedAddress', 'Address not available')
            location = place.get('location', {})
            place_types = place.get('types', [])
            
            return {
                'name': name,
                'address': address,
                'latitude': location.get('latitude'),
                'longitude': location.get('longitude'),
                'types': place_types
            }
        except (KeyError, TypeError):
            return None