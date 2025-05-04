from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views
from accounts.views import direct_login

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Home and role-based redirects
    path('', views.home, name='home'),
    
    # App URLs
    path('accounts/', include('accounts.urls')),
    path('patients/', include('patients.urls')),
    path('assessments/', include('assessments.urls')),
    path('consultations/', include('consultations.urls')),
    
    # Authentication URLs
    path('login/', direct_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)