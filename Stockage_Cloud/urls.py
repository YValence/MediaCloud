from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentification
    path('connexion/', auth_views.LoginView.as_view(
        template_name='app/connexion.html',
        redirect_authenticated_user=True,
        next_page='accueil',
    ), name='connexion'),
    path('deconnexion/', auth_views.LogoutView.as_view(next_page='connexion'), name='deconnexion'),

    # Galerie et médias
    path('', views.galerie, name='accueil'),
    path('upload/', views.upload_media, name='upload_media'),
    path('media/<int:media_id>/', views.detail_media, name='detail_media'),
    path('media/<int:media_id>/supprimer/', views.supprimer_media, name='supprimer_media'),
    path('media/<int:media_id>/partager/', views.partager_media, name='partager_media'),
    path('media/<int:media_id>/ajouter-dossier/', views.ajouter_au_dossier, name='ajouter_au_dossier'),

    # Dossiers
    path('dossiers/', views.dossiers, name='dossiers'),
    path('dossiers/creer/', views.creer_dossier, name='creer_dossier'),
    path('dossier/<int:dossier_id>/', views.detail_dossier, name='detail_dossier'),
    path('dossier/<int:dossier_id>/renommer/', views.renommer_dossier, name='renommer_dossier'),
    path('dossier/<int:dossier_id>/supprimer/', views.supprimer_dossier, name='supprimer_dossier'),
    path('dossier/<int:dossier_id>/retirer/<int:media_id>/', views.retirer_du_dossier, name='retirer_du_dossier'),

    # Corbeille
    path('corbeille/', views.corbeille, name='corbeille'),
    path('corbeille/<int:media_id>/restaurer/', views.restaurer_media, name='restaurer_media'),
    path('corbeille/<int:media_id>/supprimer-definitif/', views.supprimer_definitif, name='supprimer_definitif'),

    # Partage
    path('partages/', views.partages, name='partages'),
    path('partage/<int:partage_id>/retirer/', views.retirer_partage, name='retirer_partage'),
]
