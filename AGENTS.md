# MediaCloud — guide pour les agents

Application Django de **sauvegarde familiale** : photos, vidéos et documents stockés sur **MinIO** (compatible S3),
rangés en dossiers, partagés entre membres, avec une corbeille. Interface en français, style « coss ui ».

Avant de modifier un dossier, lire son `AGENTS.md` :
- [Stockage_Cloud/AGENTS.md](Stockage_Cloud/AGENTS.md) — le code Django (modèles, vues, URLs, admin, réglages)
- [Templates/AGENTS.md](Templates/AGENTS.md) — les templates HTML
- [static/AGENTS.md](static/AGENTS.md) — le CSS et le JavaScript

## Arborescence

```
manage.py
Stockage_Cloud/     projet ET application Django (un seul module, pas d'app séparée)
Templates/app/      tous les templates de l'interface
static/css/coss.css toute la feuille de style
static/js/app.js    tout le JavaScript
minIO/              docker-compose de MinIO + données locales (ignorées par git)
setup_minio.py      rend le bucket « appstockage » lisible publiquement
env/                environnement virtuel Python (ignoré par git)
```

## Lancer le projet (Windows)

```bash
cd minIO && docker-compose up -d          # MinIO : API :9000, console :9001 (admin / admin123)
./env/Scripts/python.exe manage.py migrate
./env/Scripts/python.exe manage.py runserver
```

Sans MinIO démarré, les pages s'affichent mais les fichiers (images, vidéos) ne chargent pas et l'upload échoue.

## Vérifier un changement

```bash
./env/Scripts/python.exe manage.py check
./env/Scripts/python.exe manage.py makemigrations --check --dry-run   # doit dire « No changes detected »
```

Il n'y a pas encore de tests automatisés. Pour tester sans abîmer la base, utiliser le client de test Django
dans un `transaction.atomic()` avec `transaction.set_rollback(True)`.
Ne jamais tester `upload_media` ni `supprimer_definitif` contre le vrai MinIO sans prévenir : ils écrivent ou suppriment de vrais fichiers.
Pour tester l'upload sans MinIO, remplacer `S3Boto3Storage._save` et `S3Boto3Storage.exists` avec `unittest.mock.patch.object`.

## Règles du projet

- Tout en **français** : noms de variables métier, messages, commentaires, textes de l'interface.
- **Ne pas commiter** `db.sqlite3`, `__pycache__/`, `minIO/data/`, `minIO/minio_data/`, `.claude/`.
- Les clés MinIO et la `SECRET_KEY` sont en clair dans `Stockage_Cloud/settings.py` et `setup_minio.py` :
  ne pas en ajouter ailleurs, ne jamais les copier dans un autre fichier.
- Branche principale : `main`. Travailler sur une branche (`feat/…`, `fix/…`, `chore/…`).
- Pas de nouvelle dépendance (Python, CSS ou JS) sans demander.
