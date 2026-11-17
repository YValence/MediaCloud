from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from .models import Media, Image, Video, Document, Dossier, Corbeille, Partage
from django.db.models import Sum
import os
import json


def _ids_corbeille():
    """IDs des médias actuellement dans la corbeille."""
    return list(Corbeille.objects.values_list('media_supprime_id', flat=True))


def _hors_corbeille(qs):
    """Exclut d'un queryset (Media ou sous-classe) les médias en corbeille."""
    return qs.exclude(id__in=_ids_corbeille())


def _stats():
    """Compteurs de la bibliothèque, hors corbeille."""
    trashed = _ids_corbeille()
    return {
        'total_medias': Media.objects.exclude(id__in=trashed).count(),
        'total_images': Image.objects.exclude(id__in=trashed).count(),
        'total_videos': Video.objects.exclude(id__in=trashed).count(),
        'total_documents': Document.objects.exclude(id__in=trashed).count(),
        'total_dossiers': Dossier.objects.count(),
    }


TYPE_LABELS = {'image': 'Image', 'video': 'Vidéo', 'document': 'Document', 'media': 'Fichier'}


def _type_et_specifique(media):
    """Retourne (type, objet spécifique) pour un Media ou une de ses sous-classes."""
    for type_media, modele in (('image', Image), ('video', Video), ('document', Document)):
        if isinstance(media, modele):
            return type_media, media
    for type_media in ('image', 'video', 'document'):
        try:
            return type_media, getattr(media, type_media)
        except (Image.DoesNotExist, Video.DoesNotExist, Document.DoesNotExist):
            continue
    return 'media', None


def _enrichir(media):
    """Ajoute type_media, specifique, type_label et duree_display pour les templates."""
    media.type_media, media.specifique = _type_et_specifique(media)
    media.type_label = TYPE_LABELS[media.type_media]
    duree = getattr(media.specifique, 'duree', 0) if media.type_media == 'video' else 0
    media.duree_display = f"{duree // 60}:{duree % 60:02d}" if duree else ''
    return media


def _contexte_commun(section):
    return {
        'section': section,
        'stockage_total': _hors_corbeille(Media.objects).aggregate(Sum('taille'))['taille__sum'] or 0,
    }



def _detecter_type(filename):
    """Déduit ('image'|'video'|'document', extension) d'un nom de fichier, via settings.MEDIA_EXTENSIONS."""
    ext = os.path.splitext(filename)[1].lower()
    correspondance = {'images': 'image', 'videos': 'video', 'documents': 'document'}
    for categorie, extensions in settings.MEDIA_EXTENSIONS.items():
        if ext in extensions:
            return correspondance[categorie], ext
    return None, ext


@login_required
def upload_media(request):
    """Téléverse un fichier depuis l'UI : détecte le type, remplit les métadonnées, stocke sur MinIO."""
    if request.method != 'POST':
        return redirect('accueil')

    fichier = request.FILES.get('fichier')
    if not fichier:
        messages.error(request, "Aucun fichier sélectionné.")
        return redirect('accueil')

    type_media, ext = _detecter_type(fichier.name)
    if not type_media:
        messages.error(request, f"Type de fichier non pris en charge ({ext or 'inconnu'}).")
        return redirect('accueil')

    nom = (request.POST.get('nom') or os.path.splitext(fichier.name)[0]).strip()[:255] or 'Sans titre'
    commun = {'nom': nom, 'taille': fichier.size, 'proprietaire': request.user, 'fichier': fichier}

    try:
        if type_media == 'image':
            media = Image(**commun)
            try:
                from PIL import Image as PILImage
                fichier.seek(0)
                with PILImage.open(fichier) as im:
                    media.largeur, media.hauteur = im.width, im.height
            except Exception:
                pass
            finally:
                fichier.seek(0)
            media.save()
        elif type_media == 'video':
            media = Video(**commun, format=ext.lstrip('.'))
            media.save()
        else:
            media = Document(**commun, type=ext.lstrip('.'))
            media.save()
        messages.success(request, f"« {nom} » a été téléversé.")
    except Exception as e:
        messages.error(request, f"Échec du téléversement : {e}")

    return redirect('accueil')


def galerie_publique(request):
    medias = Media.objects.all().order_by('-date_creation')

    type_filtre = request.GET.get('type')
    if type_filtre:
        if type_filtre == 'image':
            medias = Image.objects.all().order_by('-date_creation')
        elif type_filtre == 'video':
            medias = Video.objects.all().order_by('-date_creation')
        elif type_filtre == 'document':
            medias = Document.objects.all().order_by('-date_creation')

    medias = _hors_corbeille(medias)

    search = request.GET.get('search')
    if search:
        medias = medias.filter(nom__icontains=search)

    paginator = Paginator(medias, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistiques
    stats = _stats()

    for media in page_obj:
        _enrichir(media)

    context = {
        **_contexte_commun('galerie'),
        'page_obj': page_obj,
        'stats': stats,
        'type_actuel': type_filtre,
        'search_query': search or '',
    }

    return render(request, 'app/galerie.html', context)

def dossiers_publics(request):
    dossiers = Dossier.objects.all().order_by('-date_creation')

    search = request.GET.get('search')
    if search:
        dossiers = dossiers.filter(nom__icontains=search)
    paginator = Paginator(dossiers, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        **_contexte_commun('dossiers'),
        'page_obj': page_obj,
        'search_query': search or '',
    }

    return render(request, 'app/dossiers.html', context)

def detail_dossier(request, dossier_id):
    """Vue pour afficher le contenu d'un dossier"""
    dossier = get_object_or_404(Dossier, id=dossier_id)
    medias = _hors_corbeille(dossier.medias.all()).order_by('-date_creation')

    type_filtre = request.GET.get('type')
    if type_filtre:
        if type_filtre == 'image':
            medias = medias.filter(image__isnull=False)
        elif type_filtre == 'video':
            medias = medias.filter(video__isnull=False)
        elif type_filtre == 'document':
            medias = medias.filter(document__isnull=False)
    
    paginator = Paginator(medias, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    for media in page_obj:
        _enrichir(media)

    context = {
        **_contexte_commun('dossiers'),
        'dossier': dossier,
        'page_obj': page_obj,
        'type_actuel': type_filtre,
    }

    return render(request, 'app/detail_dossier.html', context)

def detail_media(request, media_id):
    media = get_object_or_404(Media, id=media_id)

    medias_similaires = Media.objects.filter(
        proprietaire=media.proprietaire
    ).exclude(id=media.id)[:6]
    
    _enrichir(media)
    medias_similaires = [_enrichir(m) for m in medias_similaires]

    deja_partages = media.partages.values_list('destinataire_id', flat=True)
    destinataires = User.objects.exclude(id=media.proprietaire_id).exclude(id__in=deja_partages).order_by('username')

    dossiers_disponibles = Dossier.objects.exclude(medias=media).order_by('nom')

    context = {
        **_contexte_commun('galerie'),
        'media': media,
        'media_specifique': media.specifique,
        'type_media': media.type_media,
        'medias_similaires': medias_similaires,
        'destinataires': destinataires,
        'dossiers_disponibles': dossiers_disponibles,
        'en_corbeille': media.id in _ids_corbeille(),
    }

    return render(request, 'app/detail_media.html', context)

def api_medias(request):
    type_filtre = request.GET.get('type', 'all')
    search = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 12))
    
    if type_filtre == 'image':
        medias = Image.objects.all()
    elif type_filtre == 'video':
        medias = Video.objects.all()
    elif type_filtre == 'document':
        medias = Document.objects.all()
    else:
        medias = Media.objects.all()

    medias = _hors_corbeille(medias)

    if search:
        medias = medias.filter(nom__icontains=search)

    medias = medias.order_by('-date_creation')
    
    paginator = Paginator(medias, per_page)
    page_obj = paginator.get_page(page)
    

    medias_data = []
    for media in page_obj:
        media_data = {
            'id': media.id,
            'nom': media.nom,
            'taille': media.get_taille_display(),
            'date_creation': media.date_creation.strftime('%d/%m/%Y %H:%M'),
            'proprietaire': media.proprietaire.username,
            'type': media.__class__.__name__.lower(),
        }
        
        if hasattr(media, 'fichier') and media.fichier:
            media_data['fichier_url'] = media.fichier.url
            
            if isinstance(media, Image):
                media_data['dimensions'] = media.get_dimensions_display()
            elif isinstance(media, Video):
                media_data['duree'] = f"{media.duree//60}:{media.duree%60:02d}" if media.duree else "N/A"
                media_data['format'] = media.format
            elif isinstance(media, Document):
                media_data['type_doc'] = media.type
                media_data['pages'] = media.nombre_pages
        
        medias_data.append(media_data)
    
    return JsonResponse({
        'medias': medias_data,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'total_count': paginator.count,
    })

def statistiques_api(request):
    total_medias = Media.objects.count()
    total_images = Image.objects.count()
    total_videos = Video.objects.count()
    total_documents = Document.objects.count()
    total_dossiers = Dossier.objects.count()
    
    from django.db.models import Sum
    taille_totale = Media.objects.aggregate(Sum('taille'))['taille__sum'] or 0
    
    if taille_totale < 1024 * 1024:
        taille_formatee = f"{taille_totale / 1024:.1f} KB"
    elif taille_totale < 1024 * 1024 * 1024:
        taille_formatee = f"{taille_totale / (1024 * 1024):.1f} MB"
    else:
        taille_formatee = f"{taille_totale / (1024 * 1024 * 1024):.1f} GB"

    from django.db.models import Count
    proprietaires_stats = Media.objects.values('proprietaire__username').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    return JsonResponse({
        'total_medias': total_medias,
        'total_images': total_images,
        'total_videos': total_videos,
        'total_documents': total_documents,
        'total_dossiers': total_dossiers,
        'taille_totale': taille_formatee,
        'taille_octets': taille_totale,
        'top_proprietaires': list(proprietaires_stats),
    })


# ===== Corbeille =====

@login_required
def supprimer_media(request, media_id):
    """Déplace un média dans la corbeille (suppression douce)."""
    if request.method != 'POST':
        return redirect('detail_media', media_id=media_id)
    media = get_object_or_404(Media, id=media_id)
    Corbeille.objects.get_or_create(media_supprime=media, defaults={'utilisateur': request.user})
    messages.success(request, f"« {media.nom} » a été déplacé dans la corbeille.")
    return redirect('accueil')


@login_required
def corbeille_view(request):
    """Liste les médias dans la corbeille."""
    corbeilles = Corbeille.objects.select_related('utilisateur', 'media_supprime').order_by('-date_suppression')
    medias = []
    for c in corbeilles:
        media = c.media_supprime
        _enrichir(media)
        media.supprime_par = c.utilisateur
        media.date_suppression = c.date_suppression
        medias.append(media)
    context = {
        **_contexte_commun('corbeille'),
        'medias': medias,
        'stats': _stats(),
    }
    return render(request, 'app/corbeille.html', context)


@login_required
def restaurer_media(request, media_id):
    """Sort un média de la corbeille."""
    if request.method != 'POST':
        return redirect('corbeille')
    media = get_object_or_404(Media, id=media_id)
    Corbeille.objects.filter(media_supprime=media).delete()
    messages.success(request, f"« {media.nom} » a été restauré.")
    return redirect('corbeille')


@login_required
def supprimer_definitif(request, media_id):
    """Supprime définitivement un média (fichier MinIO + base)."""
    if request.method != 'POST':
        return redirect('corbeille')
    media = get_object_or_404(Media, id=media_id)
    nom = media.nom
    _, specifique = _type_et_specifique(media)
    if specifique is not None and getattr(specifique, 'fichier', None):
        try:
            specifique.fichier.delete(save=False)
        except Exception:
            pass
    media.delete()
    messages.success(request, f"« {nom} » a été supprimé définitivement.")
    return redirect('corbeille')


# ===== Partage =====

@login_required
def partager_media(request, media_id):
    """Partage un média avec un autre utilisateur."""
    if request.method != 'POST':
        return redirect('detail_media', media_id=media_id)
    media = get_object_or_404(Media, id=media_id)
    destinataire = User.objects.filter(id=request.POST.get('destinataire')).first()
    if not destinataire:
        messages.error(request, "Destinataire invalide.")
    elif destinataire == media.proprietaire:
        messages.error(request, "Le propriétaire a déjà accès à ce média.")
    else:
        _, cree = Partage.objects.update_or_create(
            media_partage=media, destinataire=destinataire, defaults={'actif': True}
        )
        messages.success(
            request,
            f"« {media.nom} » est partagé avec {destinataire.get_full_name() or destinataire.username}."
        )
    return redirect('detail_media', media_id=media_id)


@login_required
def retirer_partage(request, partage_id):
    """Retire un partage existant."""
    if request.method != 'POST':
        return redirect('accueil')
    partage = get_object_or_404(Partage, id=partage_id)
    media_id = partage.media_partage_id
    partage.delete()
    messages.success(request, "Le partage a été retiré.")
    return redirect('detail_media', media_id=media_id)


# ===== Dossiers =====

@login_required
def creer_dossier(request):
    """Crée un dossier."""
    if request.method != 'POST':
        return redirect('dossiers')
    nom = (request.POST.get('nom') or '').strip()[:255]
    if not nom:
        messages.error(request, "Le nom du dossier est obligatoire.")
        return redirect('dossiers')
    dossier = Dossier.objects.create(nom=nom, proprietaire=request.user)
    messages.success(request, f"Dossier « {nom} » créé.")
    return redirect('detail_dossier', dossier_id=dossier.id)


@login_required
def renommer_dossier(request, dossier_id):
    """Renomme un dossier."""
    dossier = get_object_or_404(Dossier, id=dossier_id)
    if request.method != 'POST':
        return redirect('detail_dossier', dossier_id=dossier_id)
    nom = (request.POST.get('nom') or '').strip()[:255]
    if not nom:
        messages.error(request, "Le nom du dossier est obligatoire.")
    else:
        dossier.nom = nom
        dossier.save()
        messages.success(request, "Dossier renommé.")
    return redirect('detail_dossier', dossier_id=dossier_id)


@login_required
def supprimer_dossier(request, dossier_id):
    """Supprime un dossier (les médias qu'il contient sont conservés)."""
    if request.method != 'POST':
        return redirect('detail_dossier', dossier_id=dossier_id)
    dossier = get_object_or_404(Dossier, id=dossier_id)
    nom = dossier.nom
    dossier.delete()
    messages.success(request, f"Dossier « {nom} » supprimé. Les médias sont conservés.")
    return redirect('dossiers')


@login_required
def ajouter_au_dossier(request, media_id):
    """Ajoute un média à un dossier."""
    if request.method != 'POST':
        return redirect('detail_media', media_id=media_id)
    media = get_object_or_404(Media, id=media_id)
    dossier = Dossier.objects.filter(id=request.POST.get('dossier')).first()
    if not dossier:
        messages.error(request, "Dossier invalide.")
    else:
        dossier.medias.add(media)
        messages.success(request, f"« {media.nom} » ajouté au dossier « {dossier.nom} ».")
    return redirect('detail_media', media_id=media_id)


@login_required
def retirer_du_dossier(request, dossier_id, media_id):
    """Retire un média d'un dossier."""
    if request.method != 'POST':
        return redirect('detail_dossier', dossier_id=dossier_id)
    dossier = get_object_or_404(Dossier, id=dossier_id)
    media = get_object_or_404(Media, id=media_id)
    dossier.medias.remove(media)
    messages.success(request, f"« {media.nom} » retiré du dossier.")
    return redirect('detail_dossier', dossier_id=dossier_id)


@login_required
def partages_view(request):
    """Médias partagés avec l'utilisateur courant."""
    partages = Partage.objects.filter(
        destinataire=request.user, actif=True
    ).select_related('media_partage', 'media_partage__proprietaire').order_by('-date_partage')
    medias = []
    for p in partages:
        media = _hors_corbeille(Media.objects.filter(id=p.media_partage_id)).first()
        if media is None:
            continue
        _enrichir(media)
        media.partage_par = p.media_partage.proprietaire
        media.date_partage = p.date_partage
        medias.append(media)
    context = {
        **_contexte_commun('partages'),
        'medias': medias,
        'stats': _stats(),
    }
    return render(request, 'app/partages.html', context)