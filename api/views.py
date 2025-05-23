import os
import random
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from typing import List, Dict, Tuple
import requests
import math
import time
import logging

# Import the Storycraft models
from storycraft.models import Story, Character, Setting, Plot, Scene, CharacterRelationship

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

@api_view(['POST'])
def find_addresses(request):
    """Find 10 closest residential addresses to a point"""
    try:
        lat = float(request.data.get('latitude'))
        lon = float(request.data.get('longitude'))
    except (ValueError, TypeError):
        return Response({'error': 'Invalid lat/lon'}, status=400)
    
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return Response({'error': 'Invalid coordinates'}, status=400)
    
    # Simple bounding box search
    radius_km = 2.0  # Fixed 2km radius
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
    
    bbox = f"{lon-lon_delta},{lat-lat_delta},{lon+lon_delta},{lat+lat_delta}"
    
    # Search Nominatim
    headers = {
        'User-Agent': 'AddressFinder/1.0 (contact@example.com)',  # CHANGE THIS
    }
    
    params = {
        'q': 'building',
        'format': 'json',
        'addressdetails': 1,
        'limit': 50,
        'viewbox': bbox,
        'bounded': 1,
    }
    
    try:
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params=params,
            headers=headers,
            timeout=10
        )
        results = response.json()
    except:
        return Response({'error': 'Search failed'}, status=500)
    
    # Process and filter results
    addresses = []
    for result in results:
        try:
            result_lat = float(result['lat'])
            result_lon = float(result['lon'])
            
            # Calculate distance
            R = 6371  # Earth radius in km
            dlat = math.radians(result_lat - lat)
            dlon = math.radians(result_lon - lon)
            a = (math.sin(dlat/2)**2 + 
                 math.cos(math.radians(lat)) * math.cos(math.radians(result_lat)) * 
                 math.sin(dlon/2)**2)
            distance = R * 2 * math.asin(math.sqrt(a))
            
            if distance <= radius_km:
                address = result.get('address', {})
                formatted = result.get('display_name', 'Unknown')
                
                addresses.append({
                    'address': formatted,
                    'latitude': result_lat,
                    'longitude': result_lon,
                    'distance_km': round(distance, 3)
                })
        except:
            continue
    
    # Sort by distance and return top 10
    addresses.sort(key=lambda x: x['distance_km'])
    
    return Response({
        'total_found': len(addresses),
        'addresses': addresses[:10]
    })


class AddressFinder:
    """
    Class to handle address finding using Nominatim API
    """
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'YourAppName/1.0 (your-email@example.com)',  # REQUIRED: Replace with your app details
            'Referer': 'https://your-domain.com'  # REQUIRED: Replace with your domain
        })
        self.debug_requests = []  # For debugging
    
    def find_addresses_in_radius(self, center_lat: float, center_lon: float, 
                               radius_km: float, address_types: List[str], 
                               limit: int = 100) -> List[Dict]:
        """
        Find addresses within a radius of the center point
        """
        addresses = []
        
        # Calculate bounding box for initial search
        bbox = self._calculate_bounding_box(center_lat, center_lon, radius_km)
        
        # Try multiple search strategies
        search_strategies = [
            # Strategy 1: Search by administrative area
            {'area_search': True},
            # Strategy 2: Search for specific address types
            {'address_types': address_types},
            # Strategy 3: Broad search for any addresses
            {'broad_search': True}
        ]
        
        for strategy in search_strategies:
            if len(addresses) >= limit:
                break
                
            if strategy.get('area_search'):
                # Search for administrative areas first, then get addresses within them
                batch_addresses = self._search_by_area(center_lat, center_lon, radius_km, limit - len(addresses))
            elif strategy.get('address_types'):
                # Search for specific types
                batch_addresses = self._search_by_types(bbox, address_types, limit - len(addresses))
            else:
                # Broad search
                batch_addresses = self._broad_address_search(bbox, limit - len(addresses))
            
            # Filter by actual distance and avoid duplicates
            for addr in batch_addresses:
                if len(addresses) >= limit:
                    break
                    
                try:
                    distance = self._calculate_distance(
                        center_lat, center_lon, 
                        float(addr['lat']), float(addr['lon'])
                    )
                    
                    if distance <= radius_km:
                        addr['distance_km'] = round(distance, 3)
                        
                        # Avoid duplicates (simple check by coordinates)
                        if not self._is_duplicate(addr, addresses):
                            addresses.append(addr)
                except (ValueError, KeyError):
                    # Skip addresses with invalid coordinates
                    continue
            
            # Be respectful to the API
            time.sleep(1.5)  # Increased delay
        
        # Sort by distance
        addresses.sort(key=lambda x: x['distance_km'])
        
        return addresses[:limit]
    
    def _calculate_bounding_box(self, lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
        """
        Calculate bounding box for a given center point and radius
        Returns (min_lat, min_lon, max_lat, max_lon)
        """
        # Approximate conversion: 1 degree ≈ 111 km
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
        
        return (
            lat - lat_delta,  # min_lat
            lon - lon_delta,  # min_lon
            lat + lat_delta,  # max_lat
            lon + lon_delta   # max_lon
        )
    
    def _generate_search_queries(self, address_types: List[str]) -> List[str]:
        """
        Generate search queries based on address types
        """
        type_mapping = {
            'house': ['house', 'detached', 'building'],
            'apartment': ['apartment', 'flat', 'residential'],
            'residential': ['residential', 'address'],
            'commercial': ['shop', 'office', 'commercial'],
        }
        
        queries = []
        for addr_type in address_types:
            if addr_type in type_mapping:
                queries.extend(type_mapping[addr_type])
            else:
                queries.append(addr_type)
        
        return list(set(queries))  # Remove duplicates
    
    def _search_by_area(self, center_lat: float, center_lon: float, radius_km: float, limit: int) -> List[Dict]:
        """
        Search by finding the area first, then getting addresses within it
        """
        addresses = []
        
        # First, do a reverse geocode to find the area
        params = {
            'lat': center_lat,
            'lon': center_lon,
            'format': 'json',
            'addressdetails': 1,
            'zoom': 14  # City/town level
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/reverse",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            self._log_request(f"{self.base_url}/reverse", params, 1 if result else 0)
            
            if 'address' in result:
                address = result['address']
                
                # Try multiple location identifiers in order of preference
                location_keys = ['city', 'town', 'village', 'suburb', 'neighbourhood', 'county', 'state']
                location_name = None
                
                for key in location_keys:
                    if address.get(key):
                        location_name = address[key]
                        break
                
                if location_name:
                    # Try multiple search approaches for this location
                    search_queries = [
                        location_name,  # Just the city name
                        f"{location_name} address",
                        f"{location_name} street",
                        f"{location_name} building"
                    ]
                    
                    for query in search_queries:
                        if len(addresses) >= limit:
                            break
                        batch = self._search_nominatim_simple(query, limit - len(addresses))
                        addresses.extend(batch)
                        
                        if batch:  # If we got results, don't need to try other queries
                            break
                        
                        time.sleep(0.5)
                else:
                    # If we can't get a location name, try searching by coordinates with a broad query
                    bbox = self._calculate_bounding_box(center_lat, center_lon, radius_km)
                    addresses = self._search_nominatim_with_bbox("building", bbox, limit)
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Reverse geocoding error: {str(e)}")
            self._log_request(f"{self.base_url}/reverse", params, 0)
        
        return addresses
    
    def _search_by_types(self, bbox: Tuple[float, float, float, float], address_types: List[str], limit: int) -> List[Dict]:
        """
        Search for specific address types
        """
        addresses = []
        
        # Simplified search terms that work better with Nominatim
        type_queries = []
        
        for addr_type in address_types:
            if addr_type in ['residential', 'house', 'apartment']:
                type_queries.extend(['building', 'house', 'residential'])
            elif addr_type == 'business':
                type_queries.extend(['shop', 'office', 'commercial'])
            else:
                type_queries.append(addr_type)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in type_queries:
            if query not in seen:
                seen.add(query)
                unique_queries.append(query)
        
        for query in unique_queries[:3]:  # Limit to 3 queries to avoid too many requests
            if len(addresses) >= limit:
                break
                
            batch = self._search_nominatim_with_bbox(query, bbox, limit - len(addresses))
            addresses.extend(batch)
            
            time.sleep(1)
        
        return addresses
    
    def _broad_address_search(self, bbox: Tuple[float, float, float, float], limit: int) -> List[Dict]:
        """
        Broad search for any addresses - simplified approach
        """
        # Use simpler, more reliable search terms
        searches = [
            'building',    # Most general building search
            'address',     # Direct address search
            'house'        # House search
        ]
        
        addresses = []
        for search_term in searches:
            if len(addresses) >= limit:
                break
            batch = self._search_nominatim_with_bbox(search_term, bbox, limit - len(addresses))
            addresses.extend(batch)
            
            if batch:  # If we got results, we can stop here
                break
                
            time.sleep(1)
        
        return addresses
    
    def _search_nominatim_simple(self, query: str, limit: int) -> List[Dict]:
        """
        Simple Nominatim search without bounding box constraints
        """
        params = {
            'q': query,
            'format': 'json',
            'addressdetails': 1,
            'limit': min(limit, 50),
            'dedupe': 1
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            results = response.json()
            self._log_request(f"{self.base_url}/search", params, len(results))
            
            processed_results = []
            for result in results:
                processed_result = self._process_nominatim_result(result)
                if processed_result:
                    processed_results.append(processed_result)
            
            return processed_results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Nominatim API error: {str(e)}")
            self._log_request(f"{self.base_url}/search", params, 0)
            return []
    
    def _search_nominatim_with_bbox(self, query: str, bbox: Tuple[float, float, float, float], limit: int) -> List[Dict]:
        """
        Search Nominatim API with bounding box
        """
        params = {
            'q': query,
            'format': 'json',
            'addressdetails': 1,
            'limit': min(limit, 50),
            'viewbox': f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}",  # lon,lat,lon,lat
            'bounded': 1,
            'dedupe': 1
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            results = response.json()
            self._log_request(f"{self.base_url}/search", params, len(results))
            
            processed_results = []
            for result in results:
                processed_result = self._process_nominatim_result(result)
                if processed_result:
                    processed_results.append(processed_result)
            
            return processed_results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Nominatim API error: {str(e)}")
            self._log_request(f"{self.base_url}/search", params, 0)
            return []
    
    def _process_nominatim_result(self, result: Dict) -> Dict:
        """
        Process a single Nominatim result to extract address information
        """
        address = result.get('address', {})
        
        # Extract components
        house_number = address.get('house_number', '')
        street = address.get('road', address.get('street', ''))
        city = address.get('city', address.get('town', address.get('village', '')))
        state = address.get('state', address.get('province', ''))
        postcode = address.get('postcode', '')
        country = address.get('country', '')
        
        # Build formatted address
        address_parts = []
        if house_number and street:
            address_parts.append(f"{house_number} {street}")
        elif street:
            address_parts.append(street)
        
        if city:
            address_parts.append(city)
        if state:
            address_parts.append(state)
        if postcode:
            address_parts.append(postcode)
        
        formatted_address = ', '.join(address_parts)
        
        if not formatted_address:
            formatted_address = result.get('display_name', 'Unknown Address')
        
        return {
            'formatted_address': formatted_address,
            'lat': result['lat'],
            'lon': result['lon'],
            'house_number': house_number,
            'street': street,
            'city': city,
            'state': state,
            'postcode': postcode,
            'country': country,
            'place_type': result.get('type', 'unknown'),
            'osm_id': result.get('osm_id'),
            'osm_type': result.get('osm_type')
        }
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _is_duplicate(self, new_address: Dict, existing_addresses: List[Dict]) -> bool:
        """
        Simple duplicate check based on coordinates
        """
        new_lat = float(new_address['lat'])
        new_lon = float(new_address['lon'])
        
        for existing in existing_addresses:
            existing_lat = float(existing['lat'])
            existing_lon = float(existing['lon'])
            
            # If coordinates are very close (within ~10 meters), consider duplicate
            if (abs(new_lat - existing_lat) < 0.0001 and 
                abs(new_lon - existing_lon) < 0.0001):
                return True
                
        return False