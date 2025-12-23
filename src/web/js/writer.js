/**
 * Writer Mode - Interface pour permettre à l'IA d'écrire/modifier des fichiers
 * Ecrituria v2.1 - Writer Mode
 */

class WriterMode {
    constructor() {
        this.project = 'anomalie2084';
        this.files = {};
        this.previewContent = null;
        this.currentRequest = null;

        this.init();
    }

    init() {
        console.log('[Writer Mode] Initialisation...');
        this.loadFiles();
        this.setupEventListeners();
    }

    async loadFiles() {
        try {
            const response = await fetch(`/api/files/${this.project}`);
            const files = await response.json();
            this.files = files;
            this.populateFileSelector();
        } catch (error) {
            console.error('[Writer Mode] Erreur chargement fichiers:', error);
        }
    }

    populateFileSelector() {
        const selector = document.getElementById('writer-file-selector');
        if (!selector) return;

        selector.innerHTML = '<option value="">-- Sélectionner un fichier --</option>';

        for (const [folder, fileList] of Object.entries(this.files)) {
            const optgroup = document.createElement('optgroup');
            optgroup.label = folder;

            fileList.forEach(file => {
                const option = document.createElement('option');
                option.value = `${folder}/${file}`;
                option.textContent = file;
                optgroup.appendChild(option);
            });

            selector.appendChild(optgroup);
        }
    }

    setupEventListeners() {
        // Bouton générer preview
        const btnPreview = document.getElementById('btn-writer-preview');
        if (btnPreview) {
            btnPreview.addEventListener('click', () => this.generate(true));
        }

        // Bouton sauvegarder
        const btnSave = document.getElementById('btn-writer-save');
        if (btnSave) {
            btnSave.addEventListener('click', () => this.saveContent());
        }

        // Bouton annuler
        const btnCancel = document.getElementById('btn-writer-cancel');
        if (btnCancel) {
            btnCancel.addEventListener('click', () => this.cancel());
        }

        // Bouton régénérer
        const btnRegenerate = document.getElementById('btn-writer-regenerate');
        if (btnRegenerate) {
            btnRegenerate.addEventListener('click', () => this.generate(true));
        }

        // Changement d'action
        const actionSelector = document.getElementById('writer-action-selector');
        if (actionSelector) {
            actionSelector.addEventListener('change', (e) => this.onActionChange(e.target.value));
        }
    }

    onActionChange(action) {
        const fileSelector = document.getElementById('writer-file-selector');
        const fileSelectorGroup = document.getElementById('writer-file-selector-group');

        if (action === 'create') {
            // Mode création: permettre de saisir un nouveau nom
            fileSelectorGroup.innerHTML = `
                <label>Nom du nouveau fichier</label>
                <div style="display: flex; gap: 10px;">
                    <select id="writer-folder-selector" style="flex: 0 0 150px;">
                        <option value="chapitres">chapitres</option>
                        <option value="personnages">personnages</option>
                        <option value="lore">lore</option>
                        <option value="notes">notes</option>
                    </select>
                    <input type="text" id="writer-new-filename" placeholder="nom_fichier.md" style="flex: 1;">
                </div>
            `;
        } else {
            // Autres modes: sélecteur normal
            fileSelectorGroup.innerHTML = `
                <label>Fichier à modifier</label>
                <select id="writer-file-selector"></select>
            `;
            this.populateFileSelector();
        }
    }

    async generate(previewOnly = true) {
        const action = document.getElementById('writer-action-selector')?.value;
        const instruction = document.getElementById('writer-instruction')?.value;

        if (!action) {
            this.showError('Sélectionnez une action');
            return;
        }

        if (!instruction || instruction.trim() === '') {
            this.showError('Donnez des instructions à l\'IA');
            return;
        }

        let filePath;
        if (action === 'create') {
            const folder = document.getElementById('writer-folder-selector')?.value;
            const filename = document.getElementById('writer-new-filename')?.value;
            if (!filename) {
                this.showError('Donnez un nom au fichier');
                return;
            }
            filePath = `${folder}/${filename}`;
        } else {
            filePath = document.getElementById('writer-file-selector')?.value;
            if (!filePath) {
                this.showError('Sélectionnez un fichier');
                return;
            }
        }

        this.currentRequest = {
            action,
            file_path: filePath,
            instruction,
            preview_only: previewOnly,
            context_files: []
        };

        this.showLoading(true);
        this.hidePreview();
        this.hideError();

        try {
            const response = await fetch(`/api/ai-write/${this.project}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.currentRequest)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erreur serveur');
            }

            const result = await response.json();

            if (result.preview) {
                this.showPreview(result);
            } else {
                this.showSuccess(result);
            }

        } catch (error) {
            console.error('[Writer Mode] Erreur:', error);
            this.showError(`Erreur: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    async saveContent() {
        if (!this.currentRequest) {
            this.showError('Aucun contenu à sauvegarder');
            return;
        }

        // Confirmation
        if (!confirm(`Confirmer l'action: ${this.getActionLabel(this.currentRequest.action)} du fichier ${this.currentRequest.file_path} ?`)) {
            return;
        }

        this.currentRequest.preview_only = false;
        this.showLoading(true);

        try {
            const response = await fetch(`/api/ai-write/${this.project}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.currentRequest)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erreur serveur');
            }

            const result = await response.json();
            this.showSuccess(result);
            this.loadFiles(); // Recharger la liste des fichiers

        } catch (error) {
            console.error('[Writer Mode] Erreur sauvegarde:', error);
            this.showError(`Erreur: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    cancel() {
        this.hidePreview();
        this.currentRequest = null;
        document.getElementById('writer-instruction').value = '';
    }

    showPreview(result) {
        const previewSection = document.getElementById('writer-preview-section');
        const previewContent = document.getElementById('writer-preview-content');
        const originalContent = document.getElementById('writer-original-content');
        const previewActions = document.getElementById('writer-preview-actions');

        if (previewSection) previewSection.style.display = 'block';
        if (previewContent) previewContent.textContent = result.content;

        // Afficher l'original si disponible
        if (result.original_content && originalContent) {
            originalContent.style.display = 'block';
            originalContent.querySelector('pre').textContent = result.original_content;
        } else if (originalContent) {
            originalContent.style.display = 'none';
        }

        if (previewActions) previewActions.style.display = 'flex';

        const genTime = document.getElementById('writer-gen-time');
        if (genTime) {
            genTime.textContent = `Généré en ${result.generation_time?.toFixed(2)}s`;
        }
    }

    hidePreview() {
        const previewSection = document.getElementById('writer-preview-section');
        if (previewSection) previewSection.style.display = 'none';
    }

    showSuccess(result) {
        this.hidePreview();

        const successMsg = `
            ✅ Fichier ${result.mode} avec succès !
            
            Fichier: ${result.file_path}
            Temps: ${result.total_time?.toFixed(2)}s
            ${result.backup_created ? '💾 Backup créé' : ''}
        `;

        alert(successMsg);

        // Réinitialiser
        this.cancel();
    }

    showError(message) {
        const errorDiv = document.getElementById('writer-error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }

    hideError() {
        const errorDiv = document.getElementById('writer-error');
        if (errorDiv) errorDiv.style.display = 'none';
    }

    showLoading(show) {
        const loadingDiv = document.getElementById('writer-loading');
        const btnPreview = document.getElementById('btn-writer-preview');
        const btnSave = document.getElementById('btn-writer-save');

        if (loadingDiv) loadingDiv.style.display = show ? 'block' : 'none';
        if (btnPreview) btnPreview.disabled = show;
        if (btnSave) btnSave.disabled = show;
    }

    getActionLabel(action) {
        const labels = {
            'rewrite': 'Réécriture',
            'append': 'Ajout',
            'create': 'Création',
            'edit': 'Modification'
        };
        return labels[action] || action;
    }
}

// Initialiser le Writer Mode au chargement
if (typeof window !== 'undefined') {
    window.writerMode = null;
}
