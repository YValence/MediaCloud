
from django import forms
from django.core.exceptions import ValidationError
from .models import Video, Image, Document
import os

class BaseMediaForm(forms.ModelForm):
    """Formulaire de base avec validation commune"""
    
    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        if not nom:
            raise ValidationError('Le nom est obligatoire.')
        return nom.strip()

class VideoAdminForm(BaseMediaForm):
    class Meta:
        model = Video
        fields = '__all__'
        widgets = {
            'nom': forms.TextInput(attrs={'placeholder': 'Nom de la vidéo'}),
            'duree': forms.NumberInput(attrs={'placeholder': 'Durée en secondes'}),
            'format': forms.TextInput(attrs={'placeholder': 'ex: mp4, avi, mov'}),
            'taille': forms.NumberInput(attrs={'placeholder': 'Taille en octets (auto-calculée)'}),
        }
    
    def clean_fichier(self):
        fichier = self.cleaned_data.get('fichier')
        if fichier:
            ext = os.path.splitext(fichier.name)[1].lower()
            if ext not in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']:
                raise ValidationError(f'Format "{ext}" non supporté. Formats autorisés: mp4, avi, mov, wmv, flv, webm, mkv')
            
            # Limite de 1GB pour les vidéos
            if fichier.size > 1024 * 1024 * 1024:
                raise ValidationError('Fichier trop volumineux (max 1GB pour les vidéos).')
        return fichier
    
    def clean_duree(self):
        duree = self.cleaned_data.get('duree')
        if duree and duree < 0:
            raise ValidationError('La durée doit être positive.')
        return duree

class ImageAdminForm(BaseMediaForm):
    class Meta:
        model = Image
        fields = '__all__'
        widgets = {
            'nom': forms.TextInput(attrs={'placeholder': 'Nom de l\'image'}),
            'largeur': forms.NumberInput(attrs={'placeholder': 'Largeur en pixels'}),
            'hauteur': forms.NumberInput(attrs={'placeholder': 'Hauteur en pixels'}),
            'taille': forms.NumberInput(attrs={'placeholder': 'Taille en octets (auto-calculée)'}),
        }
    
    def clean_fichier(self):
        fichier = self.cleaned_data.get('fichier')
        if fichier:
            ext = os.path.splitext(fichier.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']:
                raise ValidationError(f'Format "{ext}" non supporté. Formats autorisés: jpg, png, gif, bmp, webp, svg')
            
            # Limite de 50MB pour les images
            if fichier.size > 50 * 1024 * 1024:
                raise ValidationError('Fichier trop volumineux (max 50MB pour les images).')
        return fichier

class DocumentAdminForm(BaseMediaForm):
    class Meta:
        model = Document
        fields = '__all__'
        widgets = {
            'nom': forms.TextInput(attrs={'placeholder': 'Nom du document'}),
            'type': forms.TextInput(attrs={'placeholder': 'ex: PDF, Word, Excel'}),
            'nombre_pages': forms.NumberInput(attrs={'placeholder': 'Nombre de pages'}),
            'taille': forms.NumberInput(attrs={'placeholder': 'Taille en octets (auto-calculée)'}),
        }
    
    def clean_fichier(self):
        fichier = self.cleaned_data.get('fichier')
        if fichier:
            ext = os.path.splitext(fichier.name)[1].lower()
            if ext not in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.ppt', '.pptx', '.xls', '.xlsx']:
                raise ValidationError(f'Format "{ext}" non supporté. Formats autorisés: pdf, doc, docx, txt, rtf, odt, ppt, pptx, xls, xlsx')
            
            # Limite de 200MB pour les documents
            if fichier.size > 200 * 1024 * 1024:
                raise ValidationError('Fichier trop volumineux (max 200MB pour les documents).')
        return fichier
    
    def clean_nombre_pages(self):
        pages = self.cleaned_data.get('nombre_pages')
        if pages and pages < 0:
            raise ValidationError('Le nombre de pages doit être positif.')
        return pages