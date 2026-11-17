// Comportements communs à toutes les pages de MediaCloud.
(function () {
  // ----- Fenêtres modales -----
  // Bouton d'ouverture : data-modal-open="idDeLaModale". Bouton de fermeture : data-modal-close.
  function ouvrir(modal) {
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    var champ = modal.querySelector('input[type="text"]');
    if (champ) { champ.focus(); champ.select(); }
  }

  function fermer(modal) {
    modal.hidden = true;
    document.body.style.overflow = '';
  }

  document.querySelectorAll('[data-modal-open]').forEach(function (bouton) {
    var modal = document.getElementById(bouton.dataset.modalOpen);
    if (modal) bouton.addEventListener('click', function () { ouvrir(modal); });
  });

  document.querySelectorAll('.modal-overlay').forEach(function (modal) {
    modal.addEventListener('click', function (e) { if (e.target === modal) fermer(modal); });
    modal.querySelectorAll('[data-modal-close]').forEach(function (bouton) {
      bouton.addEventListener('click', function () { fermer(modal); });
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    document.querySelectorAll('.modal-overlay:not([hidden])').forEach(fermer);
  });

  // ----- Onglets (role="tab" + aria-controls) -----
  var onglets = document.querySelectorAll('[role="tab"][aria-controls]');
  onglets.forEach(function (onglet) {
    onglet.addEventListener('click', function () {
      onglets.forEach(function (o) {
        var actif = o === onglet;
        o.classList.toggle('active', actif);
        o.setAttribute('aria-selected', actif);
        document.getElementById(o.getAttribute('aria-controls')).hidden = !actif;
      });
    });
  });

  // ----- Copier un lien (data-copy="url") -----
  document.querySelectorAll('[data-copy]').forEach(function (bouton) {
    bouton.addEventListener('click', function () {
      navigator.clipboard.writeText(bouton.dataset.copy).then(function () {
        bouton.querySelector('span').textContent = 'Lien copié';
      });
    });
  });

  // ----- Zone de dépôt de fichier (.dropzone) -----
  document.querySelectorAll('.dropzone').forEach(function (zone) {
    var input = zone.querySelector('input[type="file"]');
    var nomFichier = zone.querySelector('.dz-file');
    var afficherNom = function () {
      nomFichier.textContent = input.files.length ? input.files[0].name : '';
    };

    input.addEventListener('change', afficherNom);
    ['dragover', 'dragenter'].forEach(function (ev) {
      zone.addEventListener(ev, function (e) { e.preventDefault(); zone.classList.add('dragging'); });
    });
    ['dragleave', 'drop'].forEach(function (ev) {
      zone.addEventListener(ev, function (e) { e.preventDefault(); zone.classList.remove('dragging'); });
    });
    zone.addEventListener('drop', function (e) {
      if (e.dataTransfer.files.length) { input.files = e.dataTransfer.files; afficherNom(); }
    });
  });
})();
