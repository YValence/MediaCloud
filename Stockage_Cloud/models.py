from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import filesizeformat
from django.utils import timezone

from .storage_backends import MinIOMediaStorage


class Role(models.Model):
    role_name = models.CharField(max_length=100)

    def __str__(self):
        return self.role_name


class Utilisateur(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')

    def __str__(self):
        return self.user.username


class Media(models.Model):
    """Champs communs à tous les médias (Image, Video, Document en héritent)."""
    nom = models.CharField(max_length=255)
    taille = models.BigIntegerField(default=0)  # en octets
    date_creation = models.DateTimeField(default=timezone.now)
    proprietaire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medias')

    def get_taille_display(self):
        return filesizeformat(self.taille)

    def __str__(self):
        return self.nom


class Image(Media):
    largeur = models.IntegerField(default=0)
    hauteur = models.IntegerField(default=0)
    fichier = models.ImageField(upload_to='images/', storage=MinIOMediaStorage())

    def get_dimensions_display(self):
        if self.largeur <= 0 or self.hauteur <= 0:
            return "Dimensions inconnues"
        return f"{self.largeur} × {self.hauteur} px"


class Video(Media):
    duree = models.IntegerField(default=0)  # en secondes
    format = models.CharField(max_length=20, default='mp4')
    fichier = models.FileField(upload_to='videos/', storage=MinIOMediaStorage())

    def get_duree_display(self):
        if not self.duree:
            return ''
        return f"{self.duree // 60}:{self.duree % 60:02d}"


class Document(Media):
    type = models.CharField(max_length=100, default='pdf')
    nombre_pages = models.IntegerField(default=1)
    fichier = models.FileField(upload_to='documents/', storage=MinIOMediaStorage())


class Dossier(models.Model):
    nom = models.CharField(max_length=255)
    proprietaire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dossiers')
    medias = models.ManyToManyField(Media, blank=True, related_name='dossiers')
    date_creation = models.DateTimeField(default=timezone.now)

    def get_media_count(self):
        return self.medias.count()

    def get_total_size(self):
        return self.medias.aggregate(models.Sum('taille'))['taille__sum'] or 0

    def __str__(self):
        return self.nom


class Corbeille(models.Model):
    """Un média présent ici est « supprimé » (suppression douce, restaurable)."""
    id = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='corbeilles')
    media_supprime = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='corbeilles')
    date_suppression = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Corbeille - {self.media_supprime.nom}"


class Partage(models.Model):
    id = models.AutoField(primary_key=True)
    media_partage = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='partages')
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partages_recus')
    date_partage = models.DateTimeField(default=timezone.now)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"Partage: {self.media_partage.nom} -> {self.destinataire.username}"
