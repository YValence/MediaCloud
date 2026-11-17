# static — CSS et JavaScript

Seulement deux fichiers, chargés par `Templates/app/base.html`. Pas de framework, pas de build, pas de CDN JS.

## `css/coss.css`

- Thème inspiré de **coss ui** : gris neutres, bouton principal noir, bordures fines, ombres légères, police Inter.
- Les couleurs sont des **variables** en haut du fichier (`--primary`, `--border`, `--muted`, `--img-bg`…) :
  les réutiliser, ne pas écrire de nouvel hexadécimal ailleurs.
- Le fichier est découpé en sections commentées (`/* ---------- Layout ---------- */`, `Primitives`, `Media grid`, `Table`…) :
  ajouter une règle dans la bonne section.
- Classes de base : `btn` (+ `btn-primary`, `btn-danger`, `btn-ghost`, `btn-icon`, `btn-sm`), `input`, `badge`, `card`,
  `tabs`/`tab`, `media-grid`, `table`, `empty`, `modal-overlay`/`modal`.
- Les classes `success` / `error` servent aux messages flash Django (`message.tags`) : ne pas les supprimer
  même si on ne les voit pas dans les templates.
- Avant de supprimer une règle, vérifier qu'aucun template ni `app.js` n'utilise la classe.

## `js/app.js`

JavaScript simple (pas de modules, pas de dépendance), dans une fonction auto-appelée, avec des noms en français.
Comportements branchés par attributs HTML :

| Attribut / classe | Effet |
|---|---|
| `data-modal-open="id"` | ouvre la fenêtre `.modal-overlay#id` |
| `data-modal-close` (dans la fenêtre) | la ferme ; Échap et clic sur le fond aussi |
| `role="tab"` + `aria-controls="idPanneau"` | onglets |
| `data-copy="texte"` | copie le texte dans le presse-papiers |
| `.dropzone` avec un `input[type=file]` et un `.dz-file` | glisser-déposer + affichage du nom |

Pour un nouveau comportement : l'ajouter ici, branché par un attribut `data-…`, plutôt qu'un `<script>` dans un template.
