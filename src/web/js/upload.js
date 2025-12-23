/**
 * Interface Upload - Ecrituria
 * Gestion du drag & drop et upload de fichiers
 */

class UploadManager {
    constructor() {
        this.files = [];
        this.project = 'anomalie2084';
        this.init();
    }

    init() {
        this.uploadZone = document.getElementById('uploadZone');
        this.fileInput = document.getElementById('fileInput');
        this.browseBtn = document.getElementById('browseBtn');
        this.folderSelect = document.getElementById('folderSelect');
        this.filesList = document.getElementById('filesList');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.cancelBtn = document.getElementById('cancelBtn');
        this.actions = document.getElementById('actions');
        this.feedback = document.getElementById('feedback');

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Drag & Drop
        this.uploadZone.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadZone.addEventListener('drop', (e) => this.handleDrop(e));

        // Browse button
        this.browseBtn.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Actions
        this.uploadBtn.addEventListener('click', () => this.uploadFiles());
        this.cancelBtn.addEventListener('click', () => this.reset());
    }

    handleDragOver(e) {
        e.preventDefault();
        this.uploadZone.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.uploadZone.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.uploadZone.classList.remove('dragover');

        const files = Array.from(e.dataTransfer.files).filter(f =>
            f.name.endsWith('.md') || f.name.endsWith('.txt')
        );

        if (files.length > 0) {
            this.addFiles(files);
        } else {
            this.showFeedback('Seuls les fichiers .md et .txt sont acceptés', 'error');
        }
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.addFiles(files);
    }

    addFiles(newFiles) {
        newFiles.forEach(file => {
            if (!this.files.find(f => f.name === file.name)) {
                this.files.push(file);
            }
        });

        this.renderFilesList();
        this.actions.style.display = 'flex';
    }

    removeFile(fileName) {
        this.files = this.files.filter(f => f.name !== fileName);
        this.renderFilesList();

        if (this.files.length === 0) {
            this.actions.style.display = 'none';
        }
    }

    renderFilesList() {
        if (this.files.length === 0) {
            this.filesList.innerHTML = '';
            return;
        }

        this.filesList.innerHTML = `
            <h3>Fichiers sélectionnés (${this.files.length})</h3>
            <div class="files-items">
                ${this.files.map(file => `
                    <div class="file-item">
                        <div class="file-info">
                            <span class="file-name">📄 ${file.name}</span>
                            <span class="file-size">${this.formatSize(file.size)}</span>
                        </div>
                        <button class="file-remove" onclick="uploadManager.removeFile('${file.name}')">
                            ✖
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    async uploadFiles() {
        const folder = this.folderSelect.value;

        if (this.files.length === 0) {
            this.showFeedback('Aucun fichier sélectionné', 'error');
            return;
        }

        this.uploadBtn.disabled = true;
        this.uploadBtn.textContent = '⏳ Upload en cours...';

        let uploaded = 0;
        let failed = 0;

        for (const file of this.files) {
            try {
                await this.uploadFile(file, folder);
                uploaded++;
            } catch (error) {
                console.error(`Erreur upload ${file.name}:`, error);
                failed++;
            }
        }

        // Réindexer après upload
        if (uploaded > 0) {
            await this.reindex();
        }

        // Feedback
        if (failed === 0) {
            this.showFeedback(`✅ ${uploaded} fichier(s) ajouté(s) avec success !`, 'success');
        } else {
            this.showFeedback(`⚠️ ${uploaded} réussi(s), ${failed} échec(s)`, 'warning');
        }

        this.uploadBtn.disabled = false;
        this.uploadBtn.textContent = '📤 Ajouter et indexer';

        setTimeout(() => this.reset(), 2000);
    }

    async uploadFile(file, folder) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`/api/upload/${this.project}/${folder}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
    }

    async reindex() {
        try {
            this.showFeedback('🔄 Réindexation...', 'info');

            const response = await fetch(`/api/index/${this.project}`, {
                method: 'POST'
            });

            if (response.ok) {
                this.showFeedback('✅ Index mis à jour !', 'success');
            }
        } catch (error) {
            console.error('Erreur réindexation:', error);
        }
    }

    showFeedback(message, type = 'info') {
        this.feedback.textContent = message;
        this.feedback.className = `feedback feedback-${type}`;
        this.feedback.style.display = 'block';

        setTimeout(() => {
            this.feedback.style.display = 'none';
        }, 5000);
    }

    reset() {
        this.files = [];
        this.renderFilesList();
        this.actions.style.display = 'none';
        this.fileInput.value = '';
        this.feedback.style.display = 'none';
    }
}

// Init
let uploadManager;
document.addEventListener('DOMContentLoaded', () => {
    uploadManager = new UploadManager();
});
