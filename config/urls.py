"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from config.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/', include('fleet.urls_v1')),
    path('api/v1/', include('users.urls_v1')),

    # Schema & docs per version
    path('api/schema/v1/', SpectacularAPIView.as_view(
        api_version='v1',
        permission_classes=[permissions.AllowAny]
    ), name='schema-v1'),
    path('api/docs/v1/', SpectacularSwaggerView.as_view(
        url_name='schema-v1', permission_classes=[permissions.AllowAny]
    ), name='swagger-v1'),

    # Health check (unversioned - for infra monitoring)
    path('health/', HealthCheckView.as_view(), name='health-check'),
]