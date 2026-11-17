from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Media, Image, Video, Document, Dossier
import json



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
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'type_actuel': type_filtre,
        'search_query': search or '',
    }
    
    return render(request, 'index-3-one-page.html', context)

def dossiers_publics(request):
    dossiers = Dossier.objects.all().order_by('-date_creation')

    search = request.GET.get('search')
    if search:
        dossiers = dossiers.filter(nom__icontains=search)
    paginator = Paginator(dossiers, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search or '',
    }
    
    return render(request, 'dossiers.html', context)

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
    
    context = {
        'dossier': dossier,
        'page_obj': page_obj,
        'type_actuel': type_filtre,
    }
    
    return render(request, 'media_app/galerie/detail_dossier.html', context)

def detail_media(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    
    media_specifique = None
    type_media = 'media'
    
    try:
        media_specifique = media.image
        type_media = 'image'
    except:
        try:
            media_specifique = media.video
            type_media = 'video'
        except:
            try:
                media_specifique = media.document
                type_media = 'document'
            except:
                pass
    
    medias_similaires = Media.objects.filter(
        proprietaire=media.proprietaire
    ).exclude(id=media.id)[:6]
    
    context = {
        'media': media,
        'media_specifique': media_specifique,
        'type_media': type_media,
        'medias_similaires': medias_similaires,
    }
    
    return render(request, 'media_app/galerie/detail_media.html', context)

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