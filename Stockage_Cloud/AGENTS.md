# Stockage_Cloud — code Django

Ce dossier est à la fois le **projet** (settings, urls, wsgi) et l'**application** (models, views, admin).

## Fichiers

| Fichier | Rôle |
|---|---|
| `models.py` | `Media` (base) → `Image`, `Video`, `Document` (héritage multi-tables) ; `Dossier`, `Corbeille`, `Partage`, `Role`, `Utilisateur` |
| `views.py` | toutes les vues, en sections : utilitaires, pages, téléversement, corbeille, partage, dossiers |
| `urls.py` | toutes les routes (regroupées par section, `name=` utilisé par les templates) |
| `admin.py` | admin Django ; `MediaAdmin` est la base des admins Image/Video/Document |
| `storage_backends.py` | `MinIOMediaStorage` (lit les réglages `AWS_*`) |
| `settings.py` | réglages ; `MEDIA_EXTENSIONS` définit les extensions acceptées par type |

## À savoir avant de coder

- **Type d'un média** : un `Media` ne sait pas s'il est une image, une vidéo ou un document.
  Toujours passer par `_enrichir(media)` dans `views.py` : il ajoute `type_media` (`'image'|'video'|'document'|'media'`),
  `specifique` (l'objet `Image`/`Video`/`Document`, qui porte `fichier`) et `type_label`. Les templates en dépendent.
- **Corbeille = suppression douce** : un média est « supprimé » s'il a une ligne `Corbeille`. Il reste en base.
  Toute liste de médias affichée doit passer par `_hors_corbeille(qs)`. Restaurer = supprimer la ligne `Corbeille`.
- **Contexte commun** : chaque page rend `_contexte('<section>', ...)` ; `section` choisit l'entrée active du menu
  (`galerie`, `dossiers`, `partages`, `corbeille`).
- **Actions** : les vues qui modifient des données ont `@login_required` puis `@require_POST`,
  affichent un `messages.success/error` puis font un `redirect(...)`.
- **Filtre par type** : utiliser le dictionnaire `MODELES` (`?type=image|video|document`), pas des `if/elif`.
- **Nouvelle page** : vue dans la bonne section de `views.py` + route nommée dans `urls.py` + template dans `Templates/app/`.
- **Modèles** : après toute modification, `makemigrations` ; ne pas supprimer `Role` / `Utilisateur`
  (inutilisés mais ils ont des tables) sans demander.
- `LOGIN_URL = 'connexion'` : `@login_required` redirige vers `/connexion/`.
- L'upload garde les fichiers en mémoire jusqu'à 500 Mo (`FILE_UPLOAD_MAX_MEMORY_SIZE`).
