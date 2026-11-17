import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Corbeille, Document, Dossier, Image, Media, Partage, Video

# Sous-classe de Media pour chaque type (sert aux filtres ?type=…)
MODELES = {'image': Image, 'video': Video, 'document': Document}
TYPE_LABELS = {'image': 'Image', 'video': 'Vidéo', 'document': 'Document', 'media': 'Fichier'}
MEDIAS_PAR_PAGE = 12
DOSSIERS_PAR_PAGE = 8


# ===== Fonctions utilitaires =====

def _ids_corbeille():
    """IDs des médias actuellement dans la corbeille."""
    return list(Corbeille.objects.values_list('media_supprime_id', flat=True))


def _hors_corbeille(qs):
    """Exclut d'un queryset (Media ou sous-classe) les médias en corbeille."""
    return qs.exclude(id__in=_ids_corbeille())


def _stats():
    """Compteurs de la bibliothèque, hors corbeille."""
    en_corbeille = _ids_corbeille()
    return {
        'total_medias': Media.objects.exclude(id__in=en_corbeille).count(),
        'total_images': Image.objects.exclude(id__in=en_corbeille).count(),
        'total_videos': Video.objects.exclude(id__in=en_corbeille).count(),
        'total_documents': Document.objects.exclude(id__in=en_corbeille).count(),
        'total_dossiers': Dossier.objects.count(),
    }


def _type_et_specifique(media):
    """Retourne (type, objet Image/Video/Document) pour un Media ou une de ses sous-classes."""
    for type_media, modele in MODELES.items():
        if isinstance(media, modele):
            return type_media, media
    for type_media, modele in MODELES.items():
        try:
            return type_media, getattr(media, type_media)
        except modele.DoesNotExist:
            continue
    return 'media', None


def _enrichir(media):
    """Ajoute type_media, specifique et type_label au média, pour les templates."""
    media.type_media, media.specifique = _type_et_specifique(media)
    media.type_label = TYPE_LABELS[media.type_media]
    return media


def _paginer(request, queryset, par_page):
    return Paginator(queryset, par_page).get_page(request.GET.get('page'))


def _contexte(section, **extra):
    """Contexte commun à toutes les pages (menu actif + espace utilisé)."""
    return {
        'section': section,
        'stockage_total': _hors_corbeille(Media.objects).aggregate(Sum('taille'))['taille__sum'] or 0,
        **extra,
    }


def _detecter_type(nom_fichier):
    """Déduit ('image'|'video'|'document', extension) d'un nom de fichier, via settings.MEDIA_EXTENSIONS."""
    ext = os.path.splitext(nom_fichier)[1].lower()
    for type_media, extensions in settings.MEDIA_EXTENSIONS.items():
        if ext in extensions:
            return type_media, ext
    return None, ext


def _nom_saisi(request):
    return (request.POST.get('nom') or '').strip()[:255]


# ===== Pages =====

def galerie(request):
    type_filtre = request.GET.get('type')
    search = request.GET.get('search', '')

    medias = _hors_corbeille(MODELES.get(type_filtre, Media).objects.order_by('-date_creation'))
    if search:
        medias = medias.filter(nom__icontains=search)

    page_obj = _paginer(request, medias, MEDIAS_PAR_PAGE)
    for media in page_obj:
        _enrichir(media)

    return render(request, 'app/galerie.html', _contexte(
        'galerie',
        page_obj=page_obj,
        stats=_stats(),
        type_actuel=type_filtre,
        search_query=search,
    ))


def dossiers(request):
    search = request.GET.get('search', '')
    liste = Dossier.objects.order_by('-date_creation')
    if search:
        liste = liste.filter(nom__icontains=search)

    return render(request, 'app/dossiers.html', _contexte(
        'dossiers',
        page_obj=_paginer(request, liste, DOSSIERS_PAR_PAGE),
        search_query=search,
    ))


def detail_dossier(request, dossier_id):
    dossier = get_object_or_404(Dossier, id=dossier_id)
    type_filtre = request.GET.get('type')

    medias = _hors_corbeille(dossier.medias.order_by('-date_creation'))
    if type_filtre in MODELES:
        medias = medias.filter(**{f'{type_filtre}__isnull': False})

    page_obj = _paginer(request, medias, MEDIAS_PAR_PAGE)
    for media in page_obj:
        _enrichir(media)

    return render(request, 'app/detail_dossier.html', _contexte(
        'dossiers',
        dossier=dossier,
        page_obj=page_obj,
        type_actuel=type_filtre,
    ))


def detail_media(request, media_id):
    media = _enrichir(get_object_or_404(Media, id=media_id))

    similaires = Media.objects.filter(proprietaire=media.proprietaire).exclude(id=media.id)[:6]
    deja_partage_avec = media.partages.values_list('destinataire_id', flat=True)

    return render(request, 'app/detail_media.html', _contexte(
        'galerie',
        media=media,
        media_specifique=media.specifique,
        type_media=media.type_media,
        medias_similaires=[_enrichir(m) for m in similaires],
        destinataires=User.objects.exclude(id=media.proprietaire_id)
                                  .exclude(id__in=deja_partage_avec).order_by('username'),
        dossiers_disponibles=Dossier.objects.exclude(medias=media).order_by('nom'),
        en_corbeille=media.id in _ids_corbeille(),
    ))


@login_required
def corbeille(request):
    elements = Corbeille.objects.select_related('utilisateur', 'media_supprime').order_by('-date_suppression')
    medias = []
    for element in elements:
        media = _enrichir(element.media_supprime)
        media.supprime_par = element.utilisateur
        media.date_suppression = element.date_suppression
        medias.append(media)
    return render(request, 'app/corbeille.html', _contexte('corbeille', medias=medias))


@login_required
def partages(request):
    """Médias partagés avec l'utilisateur connecté."""
    liste = (Partage.objects
             .filter(destinataire=request.user, actif=True)
             .exclude(media_partage_id__in=_ids_corbeille())
             .select_related('media_partage__proprietaire')
             .order_by('-date_partage'))
    medias = []
    for partage in liste:
        media = _enrichir(partage.media_partage)
        media.partage_par = media.proprietaire
        media.date_partage = partage.date_partage
        medias.append(media)
    return render(request, 'app/partages.html', _contexte('partages', medias=medias))


# ===== Téléversement =====

@login_required
@require_POST
def upload_media(request):
    """Téléverse un fichier : détecte son type, remplit les métadonnées et l'envoie sur MinIO."""
    fichier = request.FILES.get('fichier')
    if not fichier:
        messages.error(request, "Aucun fichier sélectionné.")
        return redirect('accueil')

    type_media, ext = _detecter_type(fichier.name)
    if not type_media:
        messages.error(request, f"Type de fichier non pris en charge ({ext or 'inconnu'}).")
        return redirect('accueil')

    nom = _nom_saisi(request) or os.path.splitext(fichier.name)[0][:255] or 'Sans titre'
    commun = {'nom': nom, 'taille': fichier.size, 'proprietaire': request.user, 'fichier': fichier}

    if type_media == 'image':
        media = Image(**commun)
        media.largeur, media.hauteur = _dimensions_image(fichier)
    elif type_media == 'video':
        media = Video(**commun, format=ext.lstrip('.'))
    else:
        media = Document(**commun, type=ext.lstrip('.'))

    try:
        media.save()
    except Exception as e:  # erreur réseau/MinIO : on prévient l'utilisateur
        messages.error(request, f"Échec du téléversement : {e}")
    else:
        messages.success(request, f"« {nom} » a été téléversé.")
    return redirect('accueil')


def _dimensions_image(fichier):
    """(largeur, hauteur) lues avec Pillow, ou (0, 0) si l'image est illisible."""
    from PIL import Image as PILImage, UnidentifiedImageError
    try:
        with PILImage.open(fichier) as im:
            return im.width, im.height
    except (UnidentifiedImageError, OSError):
        return 0, 0
    finally:
        fichier.seek(0)


# ===== Corbeille =====

@login_required
@require_POST
def supprimer_media(request, media_id):
    """Déplace un média dans la corbeille (suppression douce)."""
    media = get_object_or_404(Media, id=media_id)
    Corbeille.objects.get_or_create(media_supprime=media, defaults={'utilisateur': request.user})
    messages.success(request, f"« {media.nom} » a été déplacé dans la corbeille.")
    return redirect('accueil')


@login_required
@require_POST
def restaurer_media(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    Corbeille.objects.filter(media_supprime=media).delete()
    messages.success(request, f"« {media.nom} » a été restauré.")
    return redirect('corbeille')


@login_required
@require_POST
def supprimer_definitif(request, media_id):
    """Supprime définitivement un média (fichier sur MinIO + ligne en base)."""
    media = get_object_or_404(Media, id=media_id)
    _, specifique = _type_et_specifique(media)
    if specifique is not None and specifique.fichier:
        try:
            specifique.fichier.delete(save=False)
        except Exception:  # fichier déjà absent de MinIO : on supprime quand même en base
            pass
    media.delete()
    messages.success(request, f"« {media.nom} » a été supprimé définitivement.")
    return redirect('corbeille')


# ===== Partage =====

@login_required
@require_POST
def partager_media(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    destinataire = User.objects.filter(id=request.POST.get('destinataire')).first()
    if not destinataire:
        messages.error(request, "Destinataire invalide.")
    elif destinataire == media.proprietaire:
        messages.error(request, "Le propriétaire a déjà accès à ce média.")
    else:
        Partage.objects.update_or_create(media_partage=media, destinataire=destinataire,
                                         defaults={'actif': True})
        nom = destinataire.get_full_name() or destinataire.username
        messages.success(request, f"« {media.nom} » est partagé avec {nom}.")
    return redirect('detail_media', media_id=media_id)


@login_required
@require_POST
def retirer_partage(request, partage_id):
    partage = get_object_or_404(Partage, id=partage_id)
    partage.delete()
    messages.success(request, "Le partage a été retiré.")
    return redirect('detail_media', media_id=partage.media_partage_id)


# ===== Dossiers =====

@login_required
@require_POST
def creer_dossier(request):
    nom = _nom_saisi(request)
    if not nom:
        messages.error(request, "Le nom du dossier est obligatoire.")
        return redirect('dossiers')
    dossier = Dossier.objects.create(nom=nom, proprietaire=request.user)
    messages.success(request, f"Dossier « {nom} » créé.")
    return redirect('detail_dossier', dossier_id=dossier.id)


@login_required
@require_POST
def renommer_dossier(request, dossier_id):
    dossier = get_object_or_404(Dossier, id=dossier_id)
    nom = _nom_saisi(request)
    if not nom:
        messages.error(request, "Le nom du dossier est obligatoire.")
    else:
        dossier.nom = nom
        dossier.save(update_fields=['nom'])
        messages.success(request, "Dossier renommé.")
    return redirect('detail_dossier', dossier_id=dossier_id)


@login_required
@require_POST
def supprimer_dossier(request, dossier_id):
    """Supprime un dossier ; les médias qu'il contient sont conservés."""
    dossier = get_object_or_404(Dossier, id=dossier_id)
    dossier.delete()
    messages.success(request, f"Dossier « {dossier.nom} » supprimé. Les médias sont conservés.")
    return redirect('dossiers')


@login_required
@require_POST
def ajouter_au_dossier(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    dossier = Dossier.objects.filter(id=request.POST.get('dossier')).first()
    if not dossier:
        messages.error(request, "Dossier invalide.")
    else:
        dossier.medias.add(media)
        messages.success(request, f"« {media.nom} » ajouté au dossier « {dossier.nom} ».")
    return redirect('detail_media', media_id=media_id)


@login_required
@require_POST
def retirer_du_dossier(request, dossier_id, media_id):
    dossier = get_object_or_404(Dossier, id=dossier_id)
    media = get_object_or_404(Media, id=media_id)
    dossier.medias.remove(media)
    messages.success(request, f"« {media.nom} » retiré du dossier.")
    return redirect('detail_dossier', dossier_id=dossier_id)
