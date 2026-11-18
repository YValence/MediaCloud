# Templates — interface HTML

Tous les templates utilisés sont dans `app/`. Le réglage `TEMPLATES['DIRS']` pointe sur ce dossier `Templates/`
(avec un T majuscule : important sous Linux).

## Structure

- `app/base.html` — layout commun : menu latéral, fil d'Ariane, messages flash, chargement de `coss.css` et `app.js`.
  Blocs : `title`, `breadcrumb`, `topbar_actions`, `content`, et `body` (remplacé en entier par `connexion.html`).
- Pages : `galerie.html`, `chronologie.html` (médias groupés par mois avec `{% regroup ... by mois %}`),
  `favoris.html`, `dossiers.html`, `detail_dossier.html`, `detail_media.html`, `corbeille.html`,
  `partages.html`, `connexion.html`.
- Morceaux réutilisables (préfixe `_`) :
  - `_icon.html` — icônes SVG : `{% include "app/_icon.html" with name="folder" size=16 %}`.
    Noms disponibles : voir les `{% elif name == ... %}` dans le fichier ; ajouter une icône là, au même format (trait, viewBox 24).
  - `_media_card.html` — carte cliquable d'un média (variable `m`, enrichie par `_enrichir`).
  - `_thumb.html` — vignette seule (image, bouton lecture vidéo ou icône document).
  - `_pagination.html` — attend `page_obj`, et garde `type_actuel` / `search_query` dans les liens.
  - `_upload_modal.html` — fenêtre de téléversement (plusieurs fichiers + dossier). S'ouvre avec
    `data-modal-open="uploadModal"`. `{% include ... with dossier_courant=dossier %}` présélectionne le dossier.

## Règles

- **Pas de `<script>` dans les templates** : tout le JS est dans `static/js/app.js`, branché par attributs
  (`data-modal-open="idModale"`, `data-modal-close`, `data-copy`, `.dropzone`, `role="tab"` + `aria-controls`).
- **Pas de nouvelle couleur en dur** : utiliser les classes de `coss.css` (`btn`, `btn-primary`, `card`, `badge`, `tabs`…).
  Les petits `style="..."` de mise en page existent déjà, mais préférer une classe s'il faut le réutiliser.
- Toutes les pages sont réservées aux membres connectés : pas besoin de tester `user.is_authenticated`.
- Les actions qui modifient des données sont des `<form method="post">` avec `{% csrf_token %}`,
  affichées seulement si `peut_modifier` (fourni par la vue) ; `user.is_staff` pour les liens vers l'admin.
- Accessibilité : vrais `<button>`/`<a>`, `aria-label` sur les boutons qui n'ont qu'une icône, `<label>` pour chaque champ.
- Textes en français.
