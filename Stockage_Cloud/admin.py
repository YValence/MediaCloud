from django.contrib import admin
from django.utils.html import format_html

from .models import Corbeille, Document, Dossier, Image, Media, Role, Video

admin.site.site_header = "MediaCloud — administration"
admin.site.site_title = "MediaCloud"
admin.site.index_title = "Gestion des médias"


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name',)
    search_fields = ('role_name',)
    ordering = ('role_name',)


class MediaAdmin(admin.ModelAdmin):
    """Base commune aux admins Image, Video et Document."""
    list_filter = ('date_creation',)
    search_fields = ('nom',)
    readonly_fields = ('date_creation', 'taille_formatee', 'proprietaire')
    ordering = ('-date_creation',)

    def save_model(self, request, obj, form, change):
        if not change:  # à la création, l'utilisateur connecté devient le propriétaire
            obj.proprietaire = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='Taille')
    def taille_formatee(self, obj):
        return obj.get_taille_display()


@admin.register(Video)
class VideoAdmin(MediaAdmin):
    list_display = ('nom', 'duree_formatee', 'format', 'taille_formatee', 'date_creation', 'apercu')
    list_filter = ('format', 'date_creation')
    fields = ('nom', 'fichier', 'duree', 'format', 'taille', 'proprietaire', 'date_creation', 'taille_formatee')

    @admin.display(description='Durée')
    def duree_formatee(self, obj):
        return obj.get_duree_display() or '—'

    @admin.display(description='Aperçu')
    def apercu(self, obj):
        if not obj.fichier:
            return '—'
        return format_html('<video width="120" height="80" controls src="{}"></video>', obj.fichier.url)


@admin.register(Image)
class ImageAdmin(MediaAdmin):
    list_display = ('nom', 'dimensions', 'taille_formatee', 'date_creation', 'apercu')
    fields = ('nom', 'fichier', 'largeur', 'hauteur', 'taille', 'proprietaire', 'date_creation', 'taille_formatee')

    @admin.display(description='Dimensions')
    def dimensions(self, obj):
        return obj.get_dimensions_display()

    @admin.display(description='Aperçu')
    def apercu(self, obj):
        if not obj.fichier:
            return '—'
        return format_html('<img src="{}" style="max-width:120px; max-height:80px">', obj.fichier.url)


@admin.register(Document)
class DocumentAdmin(MediaAdmin):
    list_display = ('nom', 'type', 'nombre_pages', 'taille_formatee', 'date_creation', 'lien')
    list_filter = ('type', 'date_creation')
    fields = ('nom', 'fichier', 'type', 'nombre_pages', 'taille', 'proprietaire', 'date_creation', 'taille_formatee')

    @admin.display(description='Fichier')
    def lien(self, obj):
        if not obj.fichier:
            return '—'
        return format_html('<a href="{}" target="_blank" rel="noopener">Télécharger</a>', obj.fichier.url)


@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_display = ('nom', 'proprietaire', 'nombre_medias', 'date_creation')
    search_fields = ('nom',)
    filter_horizontal = ('medias',)
    readonly_fields = ('proprietaire',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'medias' in form.base_fields:  # ne proposer que les médias de l'utilisateur connecté
            form.base_fields['medias'].queryset = Media.objects.filter(proprietaire=request.user)
        return form

    def save_model(self, request, obj, form, change):
        if not change:
            obj.proprietaire = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='Nb médias')
    def nombre_medias(self, obj):
        return obj.get_media_count()


@admin.register(Corbeille)
class CorbeilleAdmin(admin.ModelAdmin):
    list_display = ('media_supprime', 'utilisateur', 'taille', 'date_suppression')
    search_fields = ('media_supprime__nom',)
    readonly_fields = ('utilisateur', 'media_supprime')
    actions = ('restaurer',)

    @admin.display(description='Taille')
    def taille(self, obj):
        return obj.media_supprime.get_taille_display()

    @admin.action(description='Restaurer les médias sélectionnés')
    def restaurer(self, request, queryset):
        nombre = queryset.count()
        queryset.delete()  # sortir de la corbeille = supprimer la ligne Corbeille
        self.message_user(request, f"{nombre} média(s) restauré(s).")
