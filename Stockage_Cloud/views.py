from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Media, Image, Video, Document, Dossier
from django.db.models import Sum
import os
import json


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
        'stockage_total': Media.objects.aggregate(Sum('taille'))['taille__sum'] or 0,
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
    
    search = request.GET.get('search')
    if search:
        medias = medias.filter(nom__icontains=search)
    
    paginator = Paginator(medias, 12) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total_medias': Media.objects.count(),
        'total_images': Image.objects.count(),
        'total_videos': Video.objects.count(),
        'total_documents': Document.objects.count(),
        'total_dossiers': Dossier.objects.count(),
    }
    
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
    medias = dossier.medias.all().order_by('-date_creation')
    
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

    context = {
        **_contexte_commun('galerie'),
        'media': media,
        'media_specifique': media.specifique,
        'type_media': media.type_media,
        'medias_similaires': medias_similaires,
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