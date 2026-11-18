# Stockage_Cloud — code Django

Ce dossier est à la fois le **projet** (settings, urls, wsgi) et l'**application** (models, views, admin).

## Fichiers

| Fichier | Rôle |
|---|---|
| `models.py` | `Media` (base) → `Image`, `Video`, `Document` (héritage multi-tables) ; `Dossier`, `Corbeille`, `Partage`, `Favori`, `Role`, `Utilisateur` |
| `views.py` | toutes les vues, en sections : utilitaires, pages, téléversement, favoris, corbeille, partage, dossiers |
| `urls.py` | toutes les routes (regroupées par section, `name=` utilisé par les templates) |
| `admin.py` | admin Django ; `MediaAdmin` est la base des admins Image/Video/Document |
| `storage_backends.py` | `MinIOMediaStorage` (lit les réglages `AWS_*`) |
| `settings.py` | réglages ; `MEDIA_EXTENSIONS` définit les extensions acceptées par type |

## À savoir avant de coder

- **Connexion obligatoire partout** : `LoginRequiredMiddleware` (settings.py) protège toutes les vues.
  Ne pas ajouter `@login_required` ; pour une page publique, utiliser `@login_not_required`.
- **Droits** : tout membre connecté voit toute la bibliothèque, mais seul le **propriétaire ou un admin** (`is_staff`)
  modifie un média ou un dossier. Dans chaque action, appeler `_verifier_droit(objet, request.user)`
  (lève `PermissionDenied` → 403) ; dans les templates, utiliser `peut_modifier` passé par la vue.
  Exception : le destinataire d'un partage peut retirer ce partage lui-même.
- **Type d'un média** : un `Media` ne sait pas s'il est une image, une vidéo ou un document.
  Toujours passer par `_enrichir(media)` dans `views.py` : il ajoute `type_media` (`'image'|'video'|'document'|'media'`),
  `specifique` (l'objet `Image`/`Video`/`Document`, qui porte `fichier`) et `type_label`. Les templates en dépendent.
  Pour une liste affichée en cartes, utiliser `_enrichir_liste(medias, user)`, qui ajoute aussi `est_favori` (étoile).
- **Date de prise de vue** : `Media.date_prise` est lue dans l'EXIF des photos au téléversement (`_infos_image`).
  Elle peut être vide ; la chronologie utilise alors `date_creation` (`Coalesce`).
- **Téléversement** : le champ s'appelle `fichiers` (plusieurs fichiers), avec un `dossier` optionnel
  et un champ caché `next` pour revenir sur la page d'origine (`_retour`).
- **Corbeille = suppression douce** : un média est « supprimé » s'il a une ligne `Corbeille`. Il reste en base.
  Toute liste de médias affichée doit passer par `_hors_corbeille(qs)`. Restaurer = supprimer la ligne `Corbeille`.
- **Contexte commun** : chaque page rend `_contexte(request, '<section>', ...)` ; `section` choisit l'entrée active du menu
  (`galerie`, `chronologie`, `favoris`, `dossiers`, `partages`, `corbeille`). Il fournit aussi `dossiers_modifiables`
  et `extensions_acceptees`, utilisés par la fenêtre de téléversement.
- **Actions** : les vues qui modifient des données ont `@require_POST`, vérifient les droits,
  affichent un `messages.success/error` puis font un `redirect(...)`.
- **Filtre par type** : utiliser le dictionnaire `MODELES` (`?type=image|video|document`), pas des `if/elif`.
- **Nouvelle page** : vue dans la bonne section de `views.py` + route nommée dans `urls.py` + template dans `Templates/app/`.
- **Modèles** : après toute modification, `makemigrations` ; ne pas supprimer `Role` / `Utilisateur`
  (inutilisés mais ils ont des tables) sans demander.
- `LOGIN_URL = 'connexion'` : les visiteurs non connectés sont redirigés vers `/connexion/`.
- L'upload garde les fichiers en mémoire jusqu'à 500 Mo (`FILE_UPLOAD_MAX_MEMORY_SIZE`).
