import os
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Corbeille, Document, Dossier, Favori, Image, Media, Partage, Video

# Toutes les vues exigent d'être connecté : c'est LoginRequiredMiddleware (settings.py) qui s'en charge.

# Sous-classe de Media pour chaque type (sert aux filtres ?type=…)
MODELES = {'image': Image, 'video': Video, 'document': Document}
TYPE_LABELS = {'image': 'Image', 'video': 'Vidéo', 'document': 'Document', 'media': 'Fichier'}
MEDIAS_PAR_PAGE = 12
MEDIAS_PAR_PAGE_CHRONOLOGIE = 48
DOSSIERS_PAR_PAGE = 8

# Tags EXIF de la date de prise de vue
EXIF_IFD = 0x8769
EXIF_DATE_ORIGINALE = 36867
EXIF_DATE = 306


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


def _enrichir_liste(medias, user):
    """_enrichir sur chaque média + est_favori (étoile sur la carte)."""
    medias = list(medias)
    favoris = set(Favori.objects.filter(utilisateur=user, media__in=medias).values_list('media_id', flat=True))
    for media in medias:
        _enrichir(media)
        media.est_favori = media.id in favoris
    return medias


def _paginer(request, queryset, par_page):
    return Paginator(queryset, par_page).get_page(request.GET.get('page'))


def _contexte(request, section, **extra):
    """Contexte commun à toutes les pages : menu actif, espace utilisé, dossiers pour l'upload."""
    return {
        'section': section,
        'stockage_total': _hors_corbeille(Media.objects).aggregate(Sum('taille'))['taille__sum'] or 0,
        'dossiers_modifiables': _dossiers_modifiables(request.user),
        'extensions_acceptees': settings.MEDIA_EXTENSIONS.values(),
        **extra,
    }


def _dossiers_modifiables(user):
    dossiers = Dossier.objects.order_by('nom')
    return dossiers if user.is_staff else dossiers.filter(proprietaire=user)


def _verifier_droit(objet, user):
    """Seul le propriétaire (ou un administrateur) peut modifier un média ou un dossier."""
    if not objet.peut_etre_modifie_par(user):
        raise PermissionDenied("Vous n'êtes pas le propriétaire.")


def _retour(request, defaut, **kwargs):
    """Revient à la page indiquée dans le champ caché « next », sinon à la page par défaut."""
    suivant = request.POST.get('next')
    if suivant and url_has_allowed_host_and_scheme(suivant, allowed_hosts={request.get_host()}):
        return redirect(suivant)
    return redirect(defaut, **kwargs)


def _detecter_type(nom_fichier):
    """Déduit ('image'|'video'|'document', extension) d'un nom de fichier, via settings.MEDIA_EXTENSIONS."""
    ext = os.path.splitext(nom_fichier)[1].lower()
    for type_media, extensions in settings.MEDIA_EXTENSIONS.items():
        if ext in extensions:
            return type_media, ext
    return None, ext


def _nom_saisi(request):
    return (request.POST.get('nom') or '').strip()[:255]


def _infos_image(fichier):
    """(largeur, hauteur, date de prise de vue) lues avec Pillow ; (0, 0, None) si l'image est illisible."""
    from PIL import Image as PILImage, UnidentifiedImageError
    try:
        with PILImage.open(fichier) as im:
            exif = im.getexif()
            texte = exif.get_ifd(EXIF_IFD).get(EXIF_DATE_ORIGINALE) or exif.get(EXIF_DATE)
            return im.width, im.height, _date_exif(texte)
    except (UnidentifiedImageError, OSError):
        return 0, 0, None
    finally:
        fichier.seek(0)


def _date_exif(texte):
    """Convertit « 2024:08:15 14:32:10 » (format EXIF) en date, ou None."""
    try:
        return timezone.make_aware(datetime.strptime(str(texte).strip(), '%Y:%m:%d %H:%M:%S'))
    except (TypeError, ValueError):
        return None


# ===== Pages =====

def galerie(request):
    type_filtre = request.GET.get('type')
    search = request.GET.get('search', '')

    medias = _hors_corbeille(MODELES.get(type_filtre, Media).objects.order_by('-date_creation'))
    if search:
        medias = medias.filter(nom__icontains=search)

    page_obj = _paginer(request, medias, MEDIAS_PAR_PAGE)
    page_obj.object_list = _enrichir_liste(page_obj.object_list, request.user)

    return render(request, 'app/galerie.html', _contexte(
        request, 'galerie',
        page_obj=page_obj,
        stats=_stats(),
        type_actuel=type_filtre,
        search_query=search,
    ))


def chronologie(request):
    """Médias classés par mois, selon la date de prise de vue (ou la date d'ajout si inconnue)."""
    medias = (_hors_corbeille(Media.objects)
              .annotate(date_ref=Coalesce('date_prise', 'date_creation'))
              .annotate(mois=TruncMonth('date_ref'))
              .order_by('-date_ref'))
    page_obj = _paginer(request, medias, MEDIAS_PAR_PAGE_CHRONOLOGIE)
    page_obj.object_list = _enrichir_liste(page_obj.object_list, request.user)
    return render(request, 'app/chronologie.html', _contexte(request, 'chronologie', page_obj=page_obj))


def favoris(request):
    liste = (Favori.objects
             .filter(utilisateur=request.user)
             .exclude(media_id__in=_ids_corbeille())
             .select_related('media')
             .order_by('-date_ajout'))
    page_obj = _paginer(request, liste, MEDIAS_PAR_PAGE)
    page_obj.object_list = _enrichir_liste([f.media for f in page_obj.object_list], request.user)
    return render(request, 'app/favoris.html', _contexte(request, 'favoris', page_obj=page_obj))


def dossiers(request):
    search = request.GET.get('search', '')
    liste = Dossier.objects.order_by('-date_creation')
    if search:
        liste = liste.filter(nom__icontains=search)

    return render(request, 'app/dossiers.html', _contexte(
        request, 'dossiers',
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
    page_obj.object_list = _enrichir_liste(page_obj.object_list, request.user)

    return render(request, 'app/detail_dossier.html', _contexte(
        request, 'dossiers',
        dossier=dossier,
        peut_modifier=dossier.peut_etre_modifie_par(request.user),
        page_obj=page_obj,
        type_actuel=type_filtre,
    ))


def detail_media(request, media_id):
    media = _enrichir(get_object_or_404(Media, id=media_id))

    similaires = Media.objects.filter(proprietaire=media.proprietaire).exclude(id=media.id)[:6]
    deja_partage_avec = media.partages.values_list('destinataire_id', flat=True)

    return render(request, 'app/detail_media.html', _contexte(
        request, 'galerie',
        media=media,
        media_specifique=media.specifique,
        type_media=media.type_media,
        peut_modifier=media.peut_etre_modifie_par(request.user),
        est_favori=Favori.objects.filter(utilisateur=request.user, media=media).exists(),
        medias_similaires=_enrichir_liste(similaires, request.user),
        destinataires=User.objects.exclude(id=media.proprietaire_id)
                                  .exclude(id__in=deja_partage_avec).order_by('username'),
        dossiers_disponibles=_dossiers_modifiables(request.user).exclude(medias=media),
        en_corbeille=media.id in _ids_corbeille(),
    ))


def corbeille(request):
    """Médias de l'utilisateur en corbeille (tous les médias pour un administrateur)."""
    elements = Corbeille.objects.select_related('utilisateur', 'media_supprime').order_by('-date_suppression')
    if not request.user.is_staff:
        elements = elements.filter(media_supprime__proprietaire=request.user)
    medias = []
    for element in elements:
        media = _enrichir(element.media_supprime)
        media.supprime_par = element.utilisateur
        media.date_suppression = element.date_suppression
        medias.append(media)
    return render(request, 'app/corbeille.html', _contexte(request, 'corbeille', medias=medias))


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
    return render(request, 'app/partages.html', _contexte(request, 'partages', medias=medias))


# ===== Téléversement =====

@require_POST
def upload_media(request):
    """Téléverse un ou plusieurs fichiers, éventuellement directement dans un dossier."""
    fichiers = request.FILES.getlist('fichiers')
    if not fichiers:
        messages.error(request, "Aucun fichier sélectionné.")
        return _retour(request, 'accueil')

    dossier = None
    if request.POST.get('dossier'):
        dossier = get_object_or_404(Dossier, id=request.POST['dossier'])
        _verifier_droit(dossier, request.user)

    nom_saisi = _nom_saisi(request) if len(fichiers) == 1 else ''
    reussis, refuses = 0, []
    for fichier in fichiers:
        media = _creer_media(fichier, nom_saisi, request.user)
        if media is None:
            refuses.append(fichier.name)
            continue
        try:
            media.save()
        except Exception as e:  # erreur réseau/MinIO : on prévient l'utilisateur
            messages.error(request, f"Échec du téléversement de « {fichier.name} » : {e}")
            continue
        if dossier:
            dossier.medias.add(media)
        reussis += 1

    if refuses:
        messages.error(request, f"Type de fichier non pris en charge : {', '.join(refuses)}.")
    if reussis:
        destination = f" dans « {dossier.nom} »" if dossier else ""
        messages.success(request, f"{reussis} fichier(s) téléversé(s){destination}.")
    return _retour(request, 'accueil')


def _creer_media(fichier, nom_saisi, proprietaire):
    """Prépare (sans l'enregistrer) l'Image, la Video ou le Document correspondant au fichier, ou None."""
    type_media, ext = _detecter_type(fichier.name)
    if not type_media:
        return None

    nom = nom_saisi or os.path.splitext(fichier.name)[0][:255] or 'Sans titre'
    commun = {'nom': nom, 'taille': fichier.size, 'proprietaire': proprietaire, 'fichier': fichier}

    if type_media == 'image':
        largeur, hauteur, date_prise = _infos_image(fichier)
        return Image(**commun, largeur=largeur, hauteur=hauteur, date_prise=date_prise)
    if type_media == 'video':
        return Video(**commun, format=ext.lstrip('.'))
    return Document(**commun, type=ext.lstrip('.'))


# ===== Favoris =====

@require_POST
def basculer_favori(request, media_id):
    """Ajoute le média aux favoris, ou l'en retire s'il y est déjà."""
    media = get_object_or_404(Media, id=media_id)
    favori, cree = Favori.objects.get_or_create(utilisateur=request.user, media=media)
    if not cree:
        favori.delete()
    return _retour(request, 'detail_media', media_id=media_id)


# ===== Corbeille =====

@require_POST
def supprimer_media(request, media_id):
    """Déplace un média dans la corbeille (suppression douce)."""
    media = get_object_or_404(Media, id=media_id)
    _verifier_droit(media, request.user)
    Corbeille.objects.get_or_create(media_supprime=media, defaults={'utilisateur': request.user})
    messages.success(request, f"« {media.nom} » a été déplacé dans la corbeille.")
    return redirect('accueil')


@require_POST
def restaurer_media(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    _verifier_droit(media, request.user)
    Corbeille.objects.filter(media_supprime=media).delete()
    messages.success(request, f"« {media.nom} » a été restauré.")
    return redirect('corbeille')


@require_POST
def supprimer_definitif(request, media_id):
    """Supprime définitivement un média (fichier sur MinIO + ligne en base)."""
    media = get_object_or_404(Media, id=media_id)
    _verifier_droit(media, request.user)
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

@require_POST
def partager_media(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    _verifier_droit(media, request.user)
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


@require_POST
def retirer_partage(request, partage_id):
    """Le propriétaire du média (ou le destinataire lui-même) peut retirer un partage."""
    partage = get_object_or_404(Partage, id=partage_id)
    if partage.destinataire_id != request.user.id:
        _verifier_droit(partage.media_partage, request.user)
    partage.delete()
    messages.success(request, "Le partage a été retiré.")
    return redirect('detail_media', media_id=partage.media_partage_id)


# ===== Dossiers =====

@require_POST
def creer_dossier(request):
    nom = _nom_saisi(request)
    if not nom:
        messages.error(request, "Le nom du dossier est obligatoire.")
        return redirect('dossiers')
    dossier = Dossier.objects.create(nom=nom, proprietaire=request.user)
    messages.success(request, f"Dossier « {nom} » créé.")
    return redirect('detail_dossier', dossier_id=dossier.id)


@require_POST
def renommer_dossier(request, dossier_id):
    dossier = get_object_or_404(Dossier, id=dossier_id)
    _verifier_droit(dossier, request.user)
    nom = _nom_saisi(request)
    if not nom:
        messages.error(request, "Le nom du dossier est obligatoire.")
    else:
        dossier.nom = nom
        dossier.save(update_fields=['nom'])
        messages.success(request, "Dossier renommé.")
    return redirect('detail_dossier', dossier_id=dossier_id)


@require_POST
def supprimer_dossier(request, dossier_id):
    """Supprime un dossier ; les médias qu'il contient sont conservés."""
    dossier = get_object_or_404(Dossier, id=dossier_id)
    _verifier_droit(dossier, request.user)
    dossier.delete()
    messages.success(request, f"Dossier « {dossier.nom} » supprimé. Les médias sont conservés.")
    return redirect('dossiers')


@require_POST
def ajouter_au_dossier(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    dossier = get_object_or_404(Dossier, id=request.POST.get('dossier') or 0)
    _verifier_droit(dossier, request.user)
    dossier.medias.add(media)
    messages.success(request, f"« {media.nom} » ajouté au dossier « {dossier.nom} ».")
    return redirect('detail_media', media_id=media_id)


@require_POST
def retirer_du_dossier(request, dossier_id, media_id):
    dossier = get_object_or_404(Dossier, id=dossier_id)
    _verifier_droit(dossier, request.user)
    media = get_object_or_404(Media, id=media_id)
    dossier.medias.remove(media)
    messages.success(request, f"« {media.nom} » retiré du dossier.")
    return _retour(request, 'detail_dossier', dossier_id=dossier_id)
