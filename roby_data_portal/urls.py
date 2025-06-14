from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('portal.urls')),
    path('schemascope/', include('schemascope.urls')),
    path('api/', include('api.urls')),
    # path('auth/', include('auth_detector.urls')),
    path('todo/', include('todo.urls')),
    # path('dasher/', include('dasher.urls')),
    path('storycraft/',include('storycraft.urls')),
    path('inventory/',include('inventory.urls')),
    path('shares/',include('shares.urls')),
    path('events/',include('events.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)