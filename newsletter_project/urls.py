from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.conf.urls import handler404
from django.shortcuts import render
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.urls import path
from .views import *
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

handler404 = 'newsletter_project.urls.custom_404'

def custom_404(request, exception):
    print("404 error triggered")  # Ceci devrait s'afficher dans la console
    try:
        return render(request, 'errors/404.html', status=404)
    except Exception as e:
        print(f"Erreur lors du rendu du template 404: {e}")
        raise  # Cela affichera les détails de l'erreur dans la console
 
urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin par défaut
    path('accounts/', include('apps.accounts.urls', namespace='accounts'   )  ),  # Inclure les URLs de l'application accounts
    path('custom-admin/', include('apps.custom_admin.urls', namespace='custom_admin')),  # Inclure les URLs de l'application admin
    path('accounts/', include('allauth.urls')),   
    path('subscriptions/', include('apps.subscriptions.urls')),
    path('newsletters/', include('apps.newsletters.urls')),
    path(''       , views.HomeView.as_view()   , name='home'),
    path('contact', views.contactView.as_view(), name='contact'),
    path('faq', views.faqView.as_view(), name='faq'),

]
if settings.DEBUG:
    # Serve static files
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Serve media files (uploaded by users)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)