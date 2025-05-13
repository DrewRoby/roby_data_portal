from django.urls import path
from . import views

app_name = 'shares'

urlpatterns = [
    # Access a shared object
    path('access/<uuid:share_id>/', views.access_share, name='access_share'),
    
    # Manage shares
    path('my-shares/', views.my_shares, name='my_shares'),
    path('shared-with-me/', views.shared_with_me, name='shared_with_me'),
    path('create/<int:content_type_id>/<int:object_id>/', views.create_share, name='create_share'),
    path('edit/<uuid:share_id>/', views.edit_share, name='edit_share'),
    path('delete/<uuid:share_id>/', views.delete_share, name='delete_share'),
]