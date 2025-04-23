from django.urls import path
from . import views

app_name = 'storycraft'
urlpatterns = [
    # Story views
    path('', views.story_list, name='story_list'),
    path('story/create/', views.create_story, name='create_story'),
    path('story/<int:story_id>/', views.story_detail, name='story_detail'),
    path('story/<int:story_id>/edit/', views.edit_story, name='edit_story'),
    path('story/<int:story_id>/delete/', views.delete_story, name='delete_story'),
    path('story/<int:story_id>/network/', views.story_network, name='story_network'),
    path('story/<int:story_id>/timeline/', views.story_timeline, name='story_timeline'),
    
    # Character views
    path('story/<int:story_id>/characters/', views.character_list, name='character_list'),
    path('story/<int:story_id>/character/create/', views.create_character, name='create_character'),
    path('character/<int:character_id>/', views.character_detail, name='character_detail'),
    path('character/<int:character_id>/edit/', views.edit_character, name='edit_character'),
    path('character/<int:character_id>/delete/', views.delete_character, name='delete_character'),
    
    # Setting views
    path('story/<int:story_id>/settings/', views.setting_list, name='setting_list'),
    path('story/<int:story_id>/setting/create/', views.create_setting, name='create_setting'),
    path('setting/<int:setting_id>/', views.setting_detail, name='setting_detail'),
    path('setting/<int:setting_id>/edit/', views.edit_setting, name='edit_setting'),
    path('setting/<int:setting_id>/delete/', views.delete_setting, name='delete_setting'),
    
    # Plot views
    path('story/<int:story_id>/plots/', views.plot_list, name='plot_list'),
    path('story/<int:story_id>/plot/create/', views.create_plot, name='create_plot'),
    path('plot/<int:plot_id>/', views.plot_detail, name='plot_detail'),
    path('plot/<int:plot_id>/edit/', views.edit_plot, name='edit_plot'),
    path('plot/<int:plot_id>/delete/', views.delete_plot, name='delete_plot'),
    
    # Scene views
    path('story/<int:story_id>/scenes/', views.scene_list, name='scene_list'),
    path('story/<int:story_id>/scene/create/', views.create_scene, name='create_scene'),
    path('scene/<int:scene_id>/', views.scene_detail, name='scene_detail'),
    path('scene/<int:scene_id>/edit/', views.edit_scene, name='edit_scene'),
    path('scene/<int:scene_id>/delete/', views.delete_scene, name='delete_scene'),
    
    # Relationship views
    path('story/<int:story_id>/relationships/', views.relationship_list, name='relationship_list'),
    path('story/<int:story_id>/relationship/create/', views.create_relationship, name='create_relationship'),
    path('relationship/<int:relationship_id>/edit/', views.edit_relationship, name='edit_relationship'),
    path('relationship/<int:relationship_id>/delete/', views.delete_relationship, name='delete_relationship'),

    # Note views
    path('note/create/<str:model_name>/<int:object_id>/', views.create_note, name='create_note'),
    path('note/<int:note_id>/edit/', views.edit_note, name='edit_note'),
    path('note/<int:note_id>/delete/', views.delete_note, name='delete_note'),
    path('<str:model_name>/<int:object_id>/notes/', views.note_list, name='note_list'),
]