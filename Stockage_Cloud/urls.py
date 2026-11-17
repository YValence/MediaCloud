"""
URL configuration for Stockage_Cloud project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views  

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('', views.galerie_publique, name='accueil'),
    path('dossiers/', views.dossiers_publics, name='dossiers'),

    path('connexion/', auth_views.LoginView.as_view(
        template_name='app/connexion.html',
        redirect_authenticated_user=True,
        next_page='accueil',
    ), name='connexion'),
    path('deconnexion/', auth_views.LogoutView.as_view(next_page='connexion'), name='deconnexion'),

    path('galerie/', views.galerie_publique, name='galerie_accueil'),
    path('galerie/1', views.galerie_publique, name='galerie_publique'),
    path('dossiers/', views.dossiers_publics, name='dossiers_publics'),
    path('dossier/<int:dossier_id>/', views.detail_dossier, name='detail_dossier'),
    path('media/<int:media_id>/', views.detail_media, name='detail_media'),

    path('upload/', views.upload_media, name='upload_media'),

    # Corbeille
    path('media/<int:media_id>/supprimer/', views.supprimer_media, name='supprimer_media'),
    path('corbeille/', views.corbeille_view, name='corbeille'),
    path('corbeille/<int:media_id>/restaurer/', views.restaurer_media, name='restaurer_media'),
    path('corbeille/<int:media_id>/supprimer-definitif/', views.supprimer_definitif, name='supprimer_definitif'),

    # Partage
    path('media/<int:media_id>/partager/', views.partager_media, name='partager_media'),
    path('partage/<int:partage_id>/retirer/', views.retirer_partage, name='retirer_partage'),
    path('partages/', views.partages_view, name='partages'),

    path('api/medias/', views.api_medias, name='api_medias'),
    path('api/stats/', views.statistiques_api, name='api_stats'),
    path('api/statistiques/', views.statistiques_api, name='api_statistiques'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)