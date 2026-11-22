from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts.views import pwa_manifest, service_worker

urlpatterns = [
    path('manifest.webmanifest', pwa_manifest, name='pwa_manifest'),
    path('service-worker.js', service_worker, name='pwa_service_worker'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', include('accounts.urls')),
]
