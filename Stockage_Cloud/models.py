from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .storage_backends import MinIOMediaStorage

# Create your models here.

class Role(models.Model):
    role_name = models.CharField(max_length=100)

    def attribuer_role(self):
        pass
    
    def __str__(self):
        return self.role_name

class Utilisateur(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    
    def authentifier(self):
        pass
    
    def creer_compte(self):
        pass
    
    def __str__(self):
        return self.user.username

class Media(models.Model):
    nom = models.CharField(max_length=255)
    taille = models.BigIntegerField(default=0)  # Valeur par défaut ajoutée
    date_creation = models.DateTimeField(default=timezone.now)
    proprietaire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medias')
    
    def telecharger(self):
        pass
    
    def partager(self):
        pass
    
    def get_taille_display(self):
        """Retourne la taille formatée"""
        if self.taille < 1024:
            return f"{self.taille} bytes"
        elif self.taille < 1024 * 1024:
            return f"{self.taille / 1024:.1f} KB"
        elif self.taille < 1024 * 1024 * 1024:
            return f"{self.taille / (1024 * 1024):.1f} MB"
        else:
            return f"{self.taille / (1024 * 1024 * 1024):.1f} GB"
    
    class Meta:
        abstract = False

class Image(Media):
    largeur = models.IntegerField(default=0)
    hauteur = models.IntegerField(default=0)
    fichier = models.ImageField(
        upload_to='images/',
        storage=MinIOMediaStorage()  # UTILISER LE STOCKAGE PERSONNALISÉ
    )
    
    def get_dimensions_display(self):
        if self.largeur <= 0 or self.hauteur <= 0:
            return "Dimensions inconnues"
        return f"{self.largeur} x {self.hauteur} px"

# Même chose pour Video et Document :
class Video(Media):
    duree = models.IntegerField(default=0)
    format = models.CharField(max_length=20, default='mp4')
    fichier = models.FileField(
        upload_to='videos/',
        storage=MinIOMediaStorage()  # AJOUTER CETTE LIGNE
    )

class Document(Media):
    type = models.CharField(max_length=100, default='pdf')
    nombre_pages = models.IntegerField(default=1)
    fichier = models.FileField(
        upload_to='documents/',
        storage=MinIOMediaStorage()  # AJOUTER CETTE LIGNE
    )

class Dossier(models.Model):
    nom = models.CharField(max_length=255)
    proprietaire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dossiers')
    medias = models.ManyToManyField(Media, blank=True, related_name='dossiers')  # blank=True ajouté
    date_creation = models.DateTimeField(default=timezone.now)  # Champ ajouté pour plus de cohérence
    
    def creer_dossier(self):
        pass
    
    def ajouter_media(self):
        pass
    
    def get_media_count(self):
        """Retourne le nombre de médias dans le dossier"""
        return self.medias.count()
    
    def get_total_size(self):
        """Retourne la taille totale des médias dans le dossier"""
        return self.medias.aggregate(models.Sum('taille'))['taille__sum'] or 0
    
    def __str__(self):
        return self.nom

class Corbeille(models.Model):
    id = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='corbeilles')
    media_supprime = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='corbeilles')
    date_suppression = models.DateTimeField(default=timezone.now)  # Champ ajouté pour traçabilité
    
    def restaurer_media(self):
        pass
    
    def supprimer_definitivement(self):
        pass
    
    def vider_corbeille(self):
        pass
    
    def __str__(self):
        return f"Corbeille - {self.media_supprime.nom}"

class Partage(models.Model):
    id = models.AutoField(primary_key=True)
    media_partage = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='partages')
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partages_recus')
    date_partage = models.DateTimeField(default=timezone.now)
    actif = models.BooleanField(default=True)
    
    def generer_lien_partage(self):
        pass
    
    def modifier_autorisation(self):
        pass
    
    def __str__(self):
        return f"Partage: {self.media_partage.nom} -> {self.destinataire.username}"
    
def get_total_size_display(self):
    total_size = self.get_total_size()
    
    if total_size < 1024:
        return f"{total_size} B"
    elif total_size < 1024 * 1024:
        return f"{total_size / 1024:.1f} KB"
    elif total_size < 1024 * 1024 * 1024:
        return f"{total_size / (1024 * 1024):.1f} MB"
    else:
        return f"{total_size / (1024 * 1024 * 1024):.1f} GB"