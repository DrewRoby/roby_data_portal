from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # Event management
    path('', views.event_list, name='event_list'),
    path('create/', views.event_create, name='event_create'),
    path('<int:pk>/', views.event_detail, name='event_detail'),
    path('<int:pk>/edit/', views.event_edit, name='event_edit'),
    
    # RSVP management
    path('<int:pk>/rsvp/', views.rsvp_update, name='rsvp_update'),
    path('<int:pk>/rsvp-summary/', views.rsvp_summary, name='rsvp_summary'),
    
    # Space management
    path('<int:event_pk>/spaces/create/', views.space_create, name='space_create'),
    path('spaces/<int:pk>/edit/', views.space_edit, name='space_edit'),
    
    # Agenda item management
    path('spaces/<int:space_pk>/items/create/', views.agenda_item_create, name='agenda_item_create'),
    path('items/<int:pk>/', views.agenda_item_detail, name='agenda_item_detail'),
    path('items/<int:pk>/edit/', views.agenda_item_edit, name='agenda_item_edit'),
    path('items/<int:pk>/move/', views.agenda_item_move, name='agenda_item_move'),
    
    # Comments
    path('items/<int:item_pk>/comment/', views.add_comment, name='add_comment'),
]
