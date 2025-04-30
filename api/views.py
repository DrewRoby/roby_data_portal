import os
import random
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Import the Storycraft models
from storycraft.models import Story, Character, Setting, Plot, Scene, CharacterRelationship

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
