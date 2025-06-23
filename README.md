# MEDIASTORE
Ce projet a ete realiser avec Django et MinIO pour la partie cloud avec Docker.

## 1- Installation des dépendances Python
### Créer un environnement virtuel
python -m venv env

### Activer l'environnement
### Windows
env\Scripts\activate
### Linux/Mac
source env/bin/activate

### Installer les dépendances
pip install -r requirements.txt

python setup_minio.py

## 2- Démarrage des services
### Démarrer MinIO
docker-compose up -d
MinIO est accessible sur [le port ](http://localhost:9001)

### Appliquer les migrations Django
python manage.py migrate

### Créer un superutilisateur
python manage.py createsuperuser

### Démarrer le serveur Django
python manage.py runserver

## 3- Configuration
### Configuration MinIO

Accès local : http://localhost:9001

Utilisateur : admin
Mot de passe : admin123


### Création du bucket
le mieux est de le creer manuelement

## Erreur de Migration Django
### Supprimer les migrations (attention : perte de données)
rm -rf */migrations/0*.py
