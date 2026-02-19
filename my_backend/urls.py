from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('zedvye_one/users/', include('src.apis.users.urls')),
    path('zedvye_one/profile/', include('src.apis.profile.urls')),
    path('health/', include('src.apis.health.urls')),
    
]
if settings.DEBUG:
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]