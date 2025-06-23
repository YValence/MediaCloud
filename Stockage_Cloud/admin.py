from django.contrib import admin
import boto3, uuid
from django.utils.html import format_html
from django.contrib.auth.models import User
from .models import Role, Utilisateur, Media, Video, Image, Document, Dossier, Corbeille, Partage



s3 = boto3.client(
    service_name='s3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='qv6QjoEcNVwmwGwdGKLK',
    aws_secret_access_key='ZaWK9qOT1DRrfarpopHcYuE208NgzDgMPZ5Nn63N')

BUCKET_NAME = 'appstockage'


# Configuration pour le modèle Role
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name',)
    search_fields = ('role_name',)
    ordering = ('role_name',)

# Configuration de base pour les médias - Interface principale pour l'admin
class MediaAdmin(admin.ModelAdmin):
    list_display = ('nom', 'taille_formatee', 'date_creation', 'type_media')
    list_filter = ('date_creation',)
    search_fields = ('nom',)
    readonly_fields = ('date_creation', 'taille_formatee', 'type_media')
    ordering = ('-date_creation',)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # L'admin devient automatiquement le propriétaire
        if 'proprietaire' in form.base_fields:
            form.base_fields['proprietaire'].initial = request.user
            form.base_fields['proprietaire'].widget.attrs['readonly'] = True
        return form
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            obj.proprietaire = request.user
        super().save_model(request, obj, form, change)
    
    def taille_formatee(self, obj):
        """Formate la taille en unités lisibles"""
        if obj.taille < 1024:
            return f"{obj.taille} B"
        elif obj.taille < 1024 * 1024:
            return f"{obj.taille / 1024:.1f} KB"
        elif obj.taille < 1024 * 1024 * 1024:
            return f"{obj.taille / (1024 * 1024):.1f} MB"
        else:
            return f"{obj.taille / (1024 * 1024 * 1024):.1f} GB"
    taille_formatee.short_description = 'Taille'
    
    def type_media(self, obj):
        return obj.__class__.__name__
    type_media.short_description = 'Type'

# Configuration pour le modèle Video
@admin.register(Video)
class VideoAdmin(MediaAdmin):
    list_display = ('nom', 'duree_formatee', 'format', 'taille_formatee', 'date_creation', 'preview_video')
    list_filter = ('format', 'date_creation')
    fields = ('nom', 'fichier', 'duree', 'format', 'taille', 'proprietaire', 'date_creation', 'taille_formatee')
    readonly_fields = ('date_creation', 'taille_formatee', 'proprietaire')
    
    def duree_formatee(self, obj):
        if obj.duree:
            minutes = obj.duree // 60
            secondes = obj.duree % 60
            return f"{minutes}:{secondes:02d}"
        return "N/A"
    duree_formatee.short_description = 'Durée'
    
    def preview_video(self, obj):
        if obj.fichier:
            return format_html(
                '<video width="120" height="80" controls>'
                '<source src="{}" type="video/{}">'
                'Aperçu non disponible'
                '</video>',
                obj.fichier.url, obj.format.lower()
            )
        return "Pas de fichier"
    preview_video.short_description = 'Aperçu'

# Configuration pour le modèle Image
@admin.register(Image)
class ImageAdmin(MediaAdmin):
    list_display = ('nom', 'dimensions', 'taille_formatee', 'date_creation', 'preview_image')
    fields = ('nom', 'fichier', 'largeur', 'hauteur', 'taille', 'proprietaire', 'date_creation', 'taille_formatee')
    readonly_fields = ('date_creation', 'taille_formatee', 'proprietaire')
    
    def dimensions(self, obj):
        if obj.largeur and obj.hauteur:
            return f"{obj.largeur} x {obj.hauteur} px"
        return "N/A"
    dimensions.short_description = 'Dimensions'
    
    def preview_image(self, obj):
        if obj.fichier:
            return format_html(
                '<img src="{}" style="max-width: 120px; max-height: 80px; border: 1px solid #ddd;" />',
                obj.fichier.url
            )
        return "Pas de fichier"
    preview_image.short_description = 'Aperçu'

# Configuration pour le modèle Document
@admin.register(Document)
class DocumentAdmin(MediaAdmin):
    list_display = ('nom', 'type', 'nombre_pages', 'taille_formatee', 'date_creation', 'lien_telechargement')
    list_filter = ('type', 'date_creation')
    fields = ('nom', 'fichier', 'type', 'nombre_pages', 'taille', 'proprietaire', 'date_creation', 'taille_formatee')
    readonly_fields = ('date_creation', 'taille_formatee', 'proprietaire')
    
    def lien_telechargement(self, obj):
        if obj.fichier:
            return format_html(
                '<a href="{}" target="_blank" style="background: #417690; color: white; padding: 5px 10px; '
                'text-decoration: none; border-radius: 3px;">📥 Télécharger</a>',
                obj.fichier.url
            )
        return "Pas de fichier"
    lien_telechargement.short_description = 'Action'

# Configuration pour le modèle Dossier - Pour organiser les médias
@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_display = ('nom', 'nombre_medias', 'date_creation_format')
    search_fields = ('nom',)
    filter_horizontal = ('medias',)
    readonly_fields = ('proprietaire',)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Filtrer les médias pour ne montrer que ceux de l'admin
        if 'medias' in form.base_fields:
            form.base_fields['medias'].queryset = Media.objects.filter(proprietaire=request.user)
        return form
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.proprietaire = request.user
        super().save_model(request, obj, form, change)
    
    def nombre_medias(self, obj):
        count = obj.medias.count()
        return format_html(
            '<span style="background: #28a745; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 12px;">{}</span>',
            count
        )
    nombre_medias.short_description = 'Nb médias'
    
    def date_creation_format(self, obj):
        # Utiliser la date de création du propriétaire comme référence
        return obj.proprietaire.date_joined.strftime('%d/%m/%Y')
    date_creation_format.short_description = 'Créé le'

# Configuration pour la corbeille - Gestion des suppressions
@admin.register(Corbeille)
class CorbeilleAdmin(admin.ModelAdmin):
    list_display = ('media_nom', 'type_media', 'taille_media', 'date_suppression', 'actions_corbeille')
    list_filter = ('media_supprime__date_creation',)
    search_fields = ('media_supprime__nom',)
    readonly_fields = ('utilisateur', 'media_supprime')
    
    def media_nom(self, obj):
        return obj.media_supprime.nom
    media_nom.short_description = 'Nom du média'
    
    def type_media(self, obj):
        return obj.media_supprime.__class__.__name__
    type_media.short_description = 'Type'
    
    def taille_media(self, obj):
        taille = obj.media_supprime.taille
        if taille < 1024 * 1024:
            return f"{taille / 1024:.1f} KB"
        else:
            return f"{taille / (1024 * 1024):.1f} MB"
    taille_media.short_description = 'Taille'
    
    def date_suppression(self, obj):
        return obj.media_supprime.date_creation.strftime('%d/%m/%Y %H:%M')
    date_suppression.short_description = 'Supprimé le'
    
    def actions_corbeille(self, obj):
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<button onclick="if(confirm(\'Restaurer ce média ?\')) {{ alert(\'Fonctionnalité à implémenter\') }}" '
            'style="background: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Restaurer</button>'
            '<button onclick="if(confirm(\'Supprimer définitivement ce média ?\')) {{ alert(\'Fonctionnalité à implémenter\') }}" '
            'style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Supprimer</button>'
            '</div>'
        )
    actions_corbeille.short_description = 'Actions'

# Masquer les modèles non nécessaires pour l'instant
# admin.site.unregister(User)  # Masquer la gestion des users Django par défaut

# Ne pas enregistrer ces modèles pour l'instant
# @admin.register(Utilisateur)
# @admin.register(Partage) 

# Personnalisation de l'interface d'administration
admin.site.site_header = "🎬 Gestionnaire de Médias Cloud"
admin.site.site_title = "Admin Médias"
admin.site.index_title = "Panneau d'administration - Upload et gestion des médias"

# Ajouter du CSS personnalisé pour améliorer l'apparence
class MediaAdminConfig:
    """Configuration globale pour l'apparence de l'admin"""
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)