from django.urls import path
from . import views


app_name = 'api'

urlpatterns = [
    # User Apps API
    path('user/apps/', views.user_apps_api, name='user_apps_api'),
    
    # Existing endpoints
    path('images/', views.get_images, name='get_images'),
    path('images/random/', views.get_random_image, name='get_random_image'),
    
    # Storycraft API endpoints
    path('stories/', views.story_list_api, name='story_list_api'),
    path('stories/<int:story_id>/', views.story_detail_api, name='story_detail_api'),
    path('stories/<int:story_id>/data/', views.story_graph_data, name='story_graph_data'),
    
    # Character endpoints
    path('stories/<int:story_id>/characters/', views.character_list_api, name='character_list_api'),
    path('characters/<int:character_id>/', views.character_detail_api, name='character_detail_api'),
    path('characters/', views.character_create_api, name='character_create_api'),
    path('characters/<int:character_id>/update/', views.character_update_api, name='character_update_api'),
    path('characters/<int:character_id>/delete/', views.character_delete_api, name='character_delete_api'),
    
    # Setting endpoints
    path('stories/<int:story_id>/settings/', views.setting_list_api, name='setting_list_api'),
    path('settings/<int:setting_id>/', views.setting_detail_api, name='setting_detail_api'),
    path('settings/', views.setting_create_api, name='setting_create_api'),
    path('settings/<int:setting_id>/update/', views.setting_update_api, name='setting_update_api'),
    path('settings/<int:setting_id>/delete/', views.setting_delete_api, name='setting_delete_api'),
    
    # Plot endpoints
    path('stories/<int:story_id>/plots/', views.plot_list_api, name='plot_list_api'),
    path('plots/<int:plot_id>/', views.plot_detail_api, name='plot_detail_api'),
    path('plots/', views.plot_create_api, name='plot_create_api'),
    path('plots/<int:plot_id>/update/', views.plot_update_api, name='plot_update_api'),
    path('plots/<int:plot_id>/delete/', views.plot_delete_api, name='plot_delete_api'),
    
    # Scene endpoints
    path('stories/<int:story_id>/scenes/', views.scene_list_api, name='scene_list_api'),
    path('scenes/<int:scene_id>/', views.scene_detail_api, name='scene_detail_api'),
    path('scenes/', views.scene_create_api, name='scene_create_api'),
    path('scenes/<int:scene_id>/update/', views.scene_update_api, name='scene_update_api'),
    path('scenes/<int:scene_id>/delete/', views.scene_delete_api, name='scene_delete_api'),
    
    # Relationship endpoints
    path('relationships/', views.relationship_create_api, name='relationship_create_api'),
    path('relationships/<int:relationship_id>/', views.relationship_detail_api, name='relationship_detail_api'),
    path('relationships/<int:relationship_id>/update/', views.relationship_update_api, name='relationship_update_api'),
    path('relationships/<int:relationship_id>/delete/', views.relationship_delete_api, name='relationship_delete_api'),

    # AddressFinder
    path('find-places/', views.find_places, name='find-places'),
    ]