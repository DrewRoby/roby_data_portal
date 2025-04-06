from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('portal.urls')),
    path('tracker/', include('tracker.urls')),
    # path('api/', include('api.urls')),
    # path('auth/', include('auth_detector.urls')),
    # path('todo/', include('todo.urls')),
    # path('dasher/', include('dasher.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)