class CloudStorageApp {
    constructor() {
        this.currentFilter = 'all';
        this.currentSearch = '';
        this.apiBaseUrl = '/api';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadData();
    }

    setupEventListeners() {
        // Navigation sidebar
        document.querySelectorAll('.sidebar-item[data-type]').forEach(item => {
            item.addEventListener('click', (e) => {
                const type = e.currentTarget.dataset.type;
                this.filterByType(type);
            });
        });

        // Recherche
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', (e) => {
            this.currentSearch = e.target.value;
            this.debounceSearch();
        });

        // Actualisation
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.loadData();
        });

        // Actions sur les fichiers
        document.addEventListener('click', (e) => {
            if (e.target.closest('.file-actions button')) {
                const action = e.target.closest('button').dataset.action;
                const mediaId = e.target.closest('tr').dataset.mediaId;
                this.handleFileAction(action, mediaId);
            }
        });
    }

    debounceSearch() {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.loadFiles();
        }, 300);
    }

    filterByType(type) {
        this.currentFilter = type;
        
        // Mettre à jour l'UI
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-type="${type}"]`).classList.add('active');

        this.loadFiles();
    }

    async loadData() {
        try {
            await Promise.all([
                this.loadFolders(),
                this.loadFiles(),
                this.loadStats()
            ]);
        } catch (error) {
            console.error('Erreur lors du chargement des données:', error);
        }
    }

    async loadFolders() {
        try {
            const response = await fetch('/dossiers/');
            if (!response.ok) throw new Error('Erreur réseau');
            
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Extraire les dossiers depuis la réponse HTML
            // Ou utiliser une API dédiée
            this.renderFolders([]);
        } catch (error) {
            console.error('Erreur lors du chargement des dossiers:', error);
            this.renderFolders([]);
        }
    }

    async loadFiles() {
        try {
            const params = new URLSearchParams({
                type: this.currentFilter,
                search: this.currentSearch,
                per_page: 20
            });

            const response = await fetch(`${this.apiBaseUrl}/medias/?${params}`);
            if (!response.ok) throw new Error('Erreur réseau');
            
            const data = await response.json();
            this.renderFiles(data.medias);
        } catch (error) {
            console.error('Erreur lors du chargement des fichiers:', error);
            this.renderError('Impossible de charger les fichiers');
        }
    }

    async loadStats() {
        try {
            const response = await fetch('/api/statistiques/');
            if (!response.ok) throw new Error('Erreur réseau');
            
            const stats = await response.json();
            this.updateStats(stats);
        } catch (error) {
            console.error('Erreur lors du chargement des statistiques:', error);
        }
    }

    renderFolders(folders) {
        const grid = document.getElementById('foldersGrid');
        
        if (folders.length === 0) {
            grid.innerHTML = '<div class="loading">Aucun dossier trouvé</div>';
            return;
        }

        grid.innerHTML = folders.map(folder => `
            <div class="folder-card" onclick="window.location.href='/dossier/${folder.id}/'">
                <div class="folder-icon">
                    <i class="fas fa-folder"></i>
                </div>
                <div class="folder-name">${folder.nom}</div>
                <div class="folder-meta">
                    <span class="folder-owner">${folder.proprietaire}</span>
                    <span>${folder.date_creation}</span>
                </div>
                <div class="folder-meta">
                    <span>${folder.nombre_medias || 0} fichiers</span>
                </div>
            </div>
        `).join('');
    }

    renderFiles(files) {
        const tbody = document.getElementById('filesTableBody');
        
        if (files.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Aucun fichier trouvé</td></tr>';
            return;
        }

        tbody.innerHTML = files.map(file => `
            <tr data-media-id="${file.id}">
                <td>
                    <div class="file-name">
                        <div class="file-icon">
                            <i class="fas fa-${this.getFileIcon(file.type, file.nom)}"></i>
                        </div>
                        ${file.nom}
                    </div>
                </td>
                <td>
                    <div class="file-meta">${this.getFileTypeLabel(file.type)}</div>
                </td>
                <td>
                    <div class="file-meta">${file.taille}</div>
                </td>
                <td>
                    <div class="file-meta">${file.date_creation}</div>
                </td>
                <td>
                    <div class="file-owner">
                        <div class="owner-avatar ${file.proprietaire.toLowerCase()}">
                            ${file.proprietaire.charAt(0).toUpperCase()}
                        </div>
                        <span>${file.proprietaire}</span>
                    </div>
                </td>
                <td>
                    <div class="file-actions">
                        <button title="Voir" data-action="view">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button title="Télécharger" data-action="download">
                            <i class="fas fa-download"></i>
                        </button>
                        <button title="Plus d'options" data-action="more">
                            <i class="fas fa-ellipsis-h"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    renderError(message) {
        const tbody = document.getElementById('filesTableBody');
        tbody.innerHTML = `<tr><td colspan="6" class="error">${message}</td></tr>`;
    }

    updateStats(stats) {
        const setCount = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value || 0;
        };
        setCount('images-count', stats.total_images);
        setCount('videos-count', stats.total_videos);
        setCount('documents-count', stats.total_documents);
    }

    getFileIcon(type, fileName = '') {
        const extension = fileName.split('.').pop()?.toLowerCase();
        
        // Icônes spécifiques par extension
        const extensionIcons = {
            // Images
            'jpg': 'file-image', 'jpeg': 'file-image', 'png': 'file-image',
            'gif': 'file-image', 'bmp': 'file-image', 'svg': 'file-image',
            'webp': 'file-image', 'ico': 'file-image', 'tiff': 'file-image',
            
            // Vidéos
            'mp4': 'file-video', 'avi': 'file-video', 'mov': 'file-video',
            'mkv': 'file-video', 'wmv': 'file-video', 'flv': 'file-video',
            'webm': 'file-video', 'm4v': 'file-video', '3gp': 'file-video',
            
            // Audio
            'mp3': 'file-audio', 'wav': 'file-audio', 'flac': 'file-audio',
            'aac': 'file-audio', 'ogg': 'file-audio', 'wma': 'file-audio',
            
            // Documents texte
            'pdf': 'file-pdf', 'doc': 'file-word', 'docx': 'file-word',
            'txt': 'file-alt', 'rtf': 'file-alt', 'odt': 'file-alt',
            
            // Tableurs
            'xls': 'file-excel', 'xlsx': 'file-excel', 'csv': 'file-csv',
            'ods': 'file-excel',
            
            // Présentations
            'ppt': 'file-powerpoint', 'pptx': 'file-powerpoint',
            'odp': 'file-powerpoint',
            
            // Archives
            'zip': 'file-archive', 'rar': 'file-archive', '7z': 'file-archive',
            'tar': 'file-archive', 'gz': 'file-archive', 'bz2': 'file-archive',
            
            // Code
            'html': 'file-code', 'css': 'file-code', 'js': 'file-code',
            'php': 'file-code', 'py': 'file-code', 'java': 'file-code',
            'cpp': 'file-code', 'c': 'file-code', 'json': 'file-code',
            'xml': 'file-code', 'sql': 'file-code',
            
            // Autres
            'exe': 'cogs', 'msi': 'cogs', 'dmg': 'cogs',
            'iso': 'compact-disc', 'img': 'compact-disc'
        };
        
        // Vérifier d'abord l'extension spécifique
        if (extension && extensionIcons[extension]) {
            return extensionIcons[extension];
        }
        
        // Fallback sur le type générique
        const typeIcons = {
            'image': 'file-image',
            'video': 'file-video',
            'document': 'file-alt',
            'archive': 'file-archive',
            'audio': 'file-audio'
        };
        
        return typeIcons[type] || 'file';
    }

    getFileTypeLabel(type) {
        const labels = {
            'image': 'Image',
            'video': 'Vidéo',
            'document': 'Document'
        };
        return labels[type] || 'Fichier';
    }

    handleFileAction(action, mediaId) {
        switch (action) {
            case 'view':
                window.location.href = `/media/${mediaId}/`;
                break;
            case 'download':
                this.downloadFile(mediaId);
                break;
            case 'more':
                this.showMoreOptions(mediaId);
                break;
        }
    }

    async downloadFile(mediaId) {
        try {
            const response = await fetch(`/api/medias/${mediaId}/download/`);
            if (!response.ok) throw new Error('Erreur de téléchargement');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '';
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Erreur lors du téléchargement:', error);
            alert('Erreur lors du téléchargement du fichier');
        }
    }

    showMoreOptions(mediaId) {
        // Implémentation des options supplémentaires
        console.log('Options pour le média:', mediaId);
    }
}

// Initialiser l'application
document.addEventListener('DOMContentLoaded', () => {
    new CloudStorageApp();
});