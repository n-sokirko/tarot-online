from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def healthz(_request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/healthz/', healthz),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/', include('apps.tarot.urls')),
    path('api/v1/', include('apps.readings.urls')),
    path('api/v1/', include('apps.billing.urls')),
    path('api/v1/', include('apps.runes.urls')),
]
