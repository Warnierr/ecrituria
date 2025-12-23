// Écrituria v2.1 - Frontend Application

let currentProject = 'anomalie2084';
let currentFile = null;
let fileContentRaw = '';
let fileContentRawText = '';
let longChatTimer = null;
let progressTimer = null;
let progressValue = 0;
let graphPollInterval = null;
let isEditMode = false;
let originalContent = '';

// ========== INITIALISATION ==========

window.addEventListener('DOMContentLoaded', () => {
    loadProjects();
    loadFileTree();
    loadModels();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('chatInput').addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') sendMessage();
    });

    const hi = document.getElementById('highlightInput');
    if (hi) {
        hi.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                highlightText();
            }
        });
    }

    // Raccourcis clavier globaux
    document.addEventListener('keydown', function (e) {
        if (e.ctrlKey && e.key === 's' && isEditMode) {
            e.preventDefault();
            saveFile();
        }
        if (e.key === 'Escape' && isEditMode) {
            cancelEdit();
        }
    });

    // Setup upload zone
    setupUploadZone();
}

// ========== STATUS ==========

function setStatus(text, mode = 'info') {
    const box = document.getElementById('globalStatus');
    if (!box) return;
    const msg = box.querySelector('.msg');
    msg.innerHTML = text || '...';
    box.classList.remove('hidden', 'info', 'success', 'error');
    box.classList.add(mode || 'info');
    const bar = document.getElementById('statusProgress');
    if (bar) bar.style.width = '0%';
}

function clearStatus() {
    const box = document.getElementById('globalStatus');
    if (box) box.classList.add('hidden');
    const bar = document.getElementById('statusProgress');
    if (bar) bar.style.width = '0%';
}

function startProgress(label) {
    const bar = document.getElementById('statusProgress');
    progressValue = 5;
    if (bar) bar.style.width = progressValue + '%';
    if (progressTimer) clearInterval(progressTimer);
    progressTimer = setInterval(() => {
        progressValue = Math.min(progressValue + 5, 90);
        if (bar) bar.style.width = progressValue + '%';
    }, 1500);
    setStatus(label, 'info');
}

function finishProgress(msg) {
    const bar = document.getElementById('statusProgress');
    if (progressTimer) clearInterval(progressTimer);
    progressTimer = null;
    progressValue = 100;
    if (bar) bar.style.width = progressValue + '%';
    setStatus(msg || 'Terminé', 'success');
    setTimeout(() => { clearStatus(); }, 1200);
}

function failProgress(msg) {
    if (progressTimer) clearInterval(progressTimer);
    progressTimer = null;
    const bar = document.getElementById('statusProgress');
    if (bar) bar.style.width = '0%';
    setStatus(msg || 'Erreur', 'error');
}

// ========== PROJECTS & FILES ==========

async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const projects = await response.json();
        const select = document.getElementById('projectSelect');
        select.innerHTML = '';
        projects.forEach(p => {
            const option = document.createElement('option');
            option.value = p.name;
            option.textContent = `📖 ${p.name}${p.has_index ? ' ✓' : ''}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Erreur chargement projets:', error);
    }
}

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const models = await response.json();
        const select = document.getElementById('modelSelect');
        select.innerHTML = '';
        models.forEach(m => {
            const option = document.createElement('option');
            option.value = m.id;
            option.textContent = m.label;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Erreur chargement modèles:', error);
    }
}

async function loadFileTree() {
    try {
        const response = await fetch(`/api/files/${currentProject}`);
        const files = await response.json();
        displayFileTree(files);
    } catch (error) {
        document.getElementById('fileTree').innerHTML =
            '<p style="color: #f87171; padding: 20px;">Erreur de chargement</p>';
    }
}

function displayFileTree(files) {
    const tree = document.getElementById('fileTree');
    tree.innerHTML = '';

    for (const [folder, fileList] of Object.entries(files)) {
        const folderDiv = document.createElement('div');
        folderDiv.className = 'folder';

        folderDiv.innerHTML = `
            <div class="folder-name">📁 ${folder}</div>
            <div class="file-list">
                ${fileList.map(f => `
                    <div class="file-item" onclick="loadFile('${folder}', '${f}')">
                        📄 ${f}
                    </div>
                `).join('')}
            </div>
        `;

        tree.appendChild(folderDiv);
    }
}

async function loadFile(folder, filename) {
    try {
        document.querySelectorAll('.file-item').forEach(el => el.classList.remove('active'));
        if (event && event.target) event.target.classList.add('active');

        const response = await fetch(`/api/file/${currentProject}/${folder}/${filename}`);
        const data = await response.json();

        currentFile = `${folder}/${filename}`;
        fileContentRaw = data.content_html;
        fileContentRawText = data.content;

        document.getElementById('fileContent').innerHTML = data.content_html;
        document.getElementById('pageTitle').innerHTML = `📂 ${currentFile} <span style="font-size:11px;color:var(--primary)">(ouvert)</span>`;
        document.getElementById('fileActions').style.display = 'flex';

        if (isEditMode) {
            isEditMode = false;
            document.getElementById('fileContent').style.display = 'block';
            document.getElementById('editMode').style.display = 'none';
            document.getElementById('editBtn').textContent = '✏️ Éditer';
            document.getElementById('editBtn').classList.remove('active');
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

function loadProject() {
    currentProject = document.getElementById('projectSelect').value;
    loadFileTree();
}

// ========== HIGHLIGHT ==========

function highlightText() {
    const term = document.getElementById('highlightInput').value.trim();
    const viewer = document.getElementById('fileContent');
    if (!viewer || !fileContentRaw) return;

    let html = fileContentRaw;
    if (term) {
        const escaped = term.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
        const regex = new RegExp(`(${escaped})`, 'gi');
        html = html.replace(regex, '<span class="highlight">$1</span>');
    }
    viewer.innerHTML = html;
}

function resetHighlight() {
    const viewer = document.getElementById('fileContent');
    const input = document.getElementById('highlightInput');
    if (!viewer || !fileContentRaw) return;
    viewer.innerHTML = fileContentRaw;
    if (input) input.value = '';
}

// ========== CHAT ==========

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();
    if (!question) return;

    addMessage('user', question);
    input.value = '';

    const btn = document.getElementById('sendButton');
    btn.disabled = true;
    btn.textContent = '...';

    const loadingId = 'loading-' + Date.now();
    addMessage('assistant', '<div class="spinner"></div>', loadingId);
    startProgress('Réponse IA en cours...');

    if (longChatTimer) clearTimeout(longChatTimer);
    longChatTimer = setTimeout(() => {
        setStatus('Toujours en cours... (IA)', 'info');
    }, 25000);

    try {
        const model = document.getElementById('modelSelect').value;
        const useGraph = document.getElementById('useGraph').checked;
        const useAgents = document.getElementById('useAgents').checked;

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question,
                show_sources: true,
                project: currentProject,
                model,
                use_graph: useGraph,
                use_agents: useAgents
            })
        });

        const data = await response.json();
        document.getElementById(loadingId).remove();

        let content = data.answer;

        if (data.agents && data.agents.length > 0) {
            content = data.agents.map(a =>
                `<span class="agent-badge">${a}</span>`
            ).join('') + '<br><br>' + content;
        }

        if (data.sources && data.sources.length > 0) {
            content += '<div class="message-sources"><strong>📚 Sources:</strong><br>';
            data.sources.forEach(s => {
                content += `<span class="source-item">📄 ${s}</span>`;
            });
            content += '</div>';
        }

        addMessage('assistant', content);
        finishProgress('Réponse IA reçue');
    } catch (error) {
        document.getElementById(loadingId).remove();
        addMessage('assistant', '❌ Erreur: ' + error.message);
        failProgress('Erreur IA: ' + error.message);
    }

    btn.disabled = false;
    btn.textContent = 'Envoyer';
    if (longChatTimer) clearTimeout(longChatTimer);
    longChatTimer = null;
}

function addMessage(type, content, id = null) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'message';
    if (id) div.id = id;

    const label = type === 'user' ? '💭 VOUS' : '✨ ASSISTANT';
    const className = type === 'user' ? 'message-user' : 'message-assistant';

    let actionsHtml = '';
    if (type === 'assistant' && !content.includes('spinner')) {
        actionsHtml = `
            <div class="message-actions">
                <button class="action-btn copy-btn" onclick="copyMessageContent(this)" title="Copier">📋 Copier</button>
                <button class="action-btn apply-btn" onclick="applyToFile(this)" title="Ajouter au fichier ouvert">📝 Ajouter au fichier</button>
                <button class="action-btn new-file-btn" onclick="createNewFileFromAI(this)" title="Créer un nouveau fichier">📄 Nouveau fichier</button>
            </div>
        `;
    }

    div.innerHTML = `
        <div class="${className}">
            <div class="message-label">${label}</div>
            <div class="message-content">${content}</div>
            ${actionsHtml}
        </div>
    `;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function copyMessageContent(btn) {
    const msgContent = btn.closest('.message-assistant, .message-user').querySelector('.message-content');
    const text = msgContent.innerText || msgContent.textContent;
    navigator.clipboard.writeText(text).then(() => {
        btn.textContent = '✅ Copié!';
        setTimeout(() => btn.textContent = '📋 Copier', 2000);
    });
}

async function applyToFile(btn) {
    if (!currentFile) {
        alert('Ouvrez d\'abord un fichier dans la sidebar gauche');
        return;
    }

    const msgContent = btn.closest('.message-assistant').querySelector('.message-content');
    let text = msgContent.innerText || msgContent.textContent;
    text = text.replace(/📚 Sources:.*$/s, '').trim();
    text = text.replace(/^(Rechercheur|Coherence|Creatif|GraphRAG)\s*/gm, '').trim();

    const approved = await showAIConfirmModal('ajouter du contenu', currentFile, text, 'append');
    if (!approved) return;

    btn.disabled = true;
    btn.textContent = '⏳...';

    try {
        const [folder, filename] = currentFile.includes('/')
            ? currentFile.split('/')
            : ['', currentFile];

        const response = await fetch(`/api/file/${currentProject}/${folder}/${filename}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: text, append: true })
        });

        const data = await response.json();
        if (data.success) {
            btn.textContent = '✅ Ajouté!';
            const [f, fn] = currentFile.split('/');
            loadFile(f, fn);
        } else {
            throw new Error(data.detail || 'Erreur');
        }
    } catch (err) {
        alert('Erreur: ' + err.message);
        btn.textContent = '📝 Ajouter au fichier';
    }

    setTimeout(() => {
        btn.disabled = false;
        btn.textContent = '📝 Ajouter au fichier';
    }, 2000);
}

async function createNewFileFromAI(btn) {
    const folder = prompt('Dossier (ex: personnages, lore, chapitres):', 'notes');
    if (!folder) return;

    const filename = prompt('Nom du fichier (avec .md):', 'nouveau.md');
    if (!filename) return;

    const msgContent = btn.closest('.message-assistant').querySelector('.message-content');
    let text = msgContent.innerText || msgContent.textContent;
    text = text.replace(/📚 Sources:.*$/s, '').trim();

    btn.disabled = true;
    btn.textContent = '⏳...';

    try {
        const response = await fetch(`/api/file/${currentProject}/${folder}/${filename}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: text, append: false })
        });

        const data = await response.json();
        if (data.success) {
            btn.textContent = '✅ Créé!';
            loadFileTree();
            setTimeout(() => loadFile(folder, filename), 500);
        } else {
            throw new Error(data.detail || 'Erreur');
        }
    } catch (err) {
        alert('Erreur: ' + err.message);
    }

    setTimeout(() => {
        btn.disabled = false;
        btn.textContent = '📄 Nouveau fichier';
    }, 2000);
}

// ========== EDIT ==========

async function createNewFile() {
    const folder = prompt('📁 Dossier (ex: personnages, lore, chapitres):', 'notes');
    if (!folder) return;

    const filename = prompt('📄 Nom du fichier (avec .md):', 'nouveau.md');
    if (!filename) return;

    const content = `# ${filename.replace('.md', '')}\n\n<!-- Écrivez votre contenu ici -->\n`;

    try {
        const response = await fetch(`/api/file/${currentProject}/${folder}/${filename}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, append: false })
        });

        const data = await response.json();
        if (data.success) {
            alert('✅ Fichier créé !');
            loadFileTree();
            setTimeout(() => loadFile(folder, filename), 500);
        } else {
            throw new Error(data.detail || 'Erreur');
        }
    } catch (err) {
        alert('❌ Erreur: ' + err.message);
    }
}

function toggleEditMode() {
    if (!currentFile) {
        alert('Ouvrez d\'abord un fichier');
        return;
    }

    isEditMode = !isEditMode;
    const editBtn = document.getElementById('editBtn');
    const fileContent = document.getElementById('fileContent');
    const editMode = document.getElementById('editMode');
    const textarea = document.getElementById('editTextarea');

    if (isEditMode) {
        originalContent = fileContentRawText || '';
        textarea.value = originalContent;
        fileContent.style.display = 'none';
        editMode.style.display = 'flex';
        editBtn.textContent = '👁️ Aperçu';
        editBtn.classList.add('active');
        textarea.focus();
    } else {
        fileContent.style.display = 'block';
        editMode.style.display = 'none';
        editBtn.textContent = '✏️ Éditer';
        editBtn.classList.remove('active');
    }
}

async function saveFile() {
    if (!currentFile) return;

    const textarea = document.getElementById('editTextarea');
    const newContent = textarea.value;

    if (newContent === originalContent) {
        alert('Aucune modification détectée');
        return;
    }

    try {
        const [folder, filename] = currentFile.split('/');
        const response = await fetch(`/api/file/${currentProject}/${folder}/${filename}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: newContent, append: false })
        });

        const data = await response.json();
        if (data.success) {
            alert('💾 Fichier sauvegardé !');
            await loadFile(folder, filename);
            toggleEditMode();
        } else {
            throw new Error(data.detail || 'Erreur');
        }
    } catch (err) {
        alert('❌ Erreur: ' + err.message);
    }
}

function cancelEdit() {
    if (confirm('Annuler les modifications ?')) {
        document.getElementById('editTextarea').value = originalContent;
        toggleEditMode();
    }
}

async function deleteFile() {
    if (!currentFile) return;

    if (!confirm(`🗑️ Supprimer "${currentFile}" ?\n\nCette action est irréversible.`)) return;

    try {
        const [folder, filename] = currentFile.split('/');
        const response = await fetch(`/api/file/${currentProject}/${folder}/${filename}`, {
            method: 'DELETE'
        });

        const data = await response.json();
        if (data.success) {
            alert('🗑️ Fichier supprimé');
            currentFile = null;
            document.getElementById('fileActions').style.display = 'none';
            document.getElementById('pageTitle').textContent = 'Sélectionnez un fichier';
            document.getElementById('fileContent').innerHTML = '<div class="empty-state"><div class="empty-state-icon">📚</div><h3>Fichier supprimé</h3></div>';
            loadFileTree();
        } else {
            throw new Error(data.detail || 'Erreur');
        }
    } catch (err) {
        alert('❌ Erreur: ' + err.message);
    }
}

async function renameFile() {
    if (!currentFile) return;

    const [folder, oldFilename] = currentFile.split('/');
    const newFilename = prompt('✏️ Nouveau nom:', oldFilename);

    if (!newFilename || newFilename === oldFilename) return;

    try {
        const readResponse = await fetch(`/api/file/${currentProject}/${folder}/${oldFilename}`);
        const fileData = await readResponse.json();

        const createResponse = await fetch(`/api/file/${currentProject}/${folder}/${newFilename}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: fileData.content, append: false })
        });

        if ((await createResponse.json()).success) {
            await fetch(`/api/file/${currentProject}/${folder}/${oldFilename}`, { method: 'DELETE' });
            alert('✅ Fichier renommé !');
            loadFileTree();
            setTimeout(() => loadFile(folder, newFilename), 500);
        }
    } catch (err) {
        alert('❌ Erreur: ' + err.message);
    }
}

async function duplicateFile() {
    if (!currentFile) return;

    const [folder, filename] = currentFile.split('/');
    const baseName = filename.replace('.md', '');
    const newFilename = prompt('📋 Nom de la copie:', `${baseName}_copie.md`);

    if (!newFilename) return;

    try {
        const readResponse = await fetch(`/api/file/${currentProject}/${folder}/${filename}`);
        const fileData = await readResponse.json();

        const createResponse = await fetch(`/api/file/${currentProject}/${folder}/${newFilename}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: fileData.content, append: false })
        });

        if ((await createResponse.json()).success) {
            alert('📋 Fichier dupliqué !');
            loadFileTree();
            setTimeout(() => loadFile(folder, newFilename), 500);
        }
    } catch (err) {
        alert('❌ Erreur: ' + err.message);
    }
}

// ========== UPLOAD ==========

function setupUploadZone() {
    const zone = document.getElementById('uploadZone');
    const input = document.getElementById('fileInput');

    if (!zone || !input) return;

    zone.addEventListener('click', () => input.click());

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    input.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

function openUploadModal() {
    document.getElementById('uploadModal').style.display = 'flex';
    document.getElementById('uploadResults').innerHTML = '';
    document.getElementById('uploadProgress').style.display = 'none';
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
}

async function handleFiles(files) {
    if (!files.length) return;

    const folder = document.getElementById('uploadFolder').value;
    const resultsDiv = document.getElementById('uploadResults');
    const progressDiv = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('uploadProgressBar');

    progressDiv.style.display = 'block';
    resultsDiv.innerHTML = '';

    let uploaded = 0;
    const total = files.length;

    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`/api/upload/${currentProject}/${folder}`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                resultsDiv.innerHTML += `
                    <div class="upload-result-item success">
                        ✅ ${file.name} → ${folder}/
                    </div>
                `;
            } else {
                throw new Error(data.detail || 'Erreur');
            }
        } catch (err) {
            resultsDiv.innerHTML += `
                <div class="upload-result-item error">
                    ❌ ${file.name}: ${err.message}
                </div>
            `;
        }

        uploaded++;
        progressBar.style.width = `${(uploaded / total) * 100}%`;
    }

    // Réindexer si option cochée
    if (document.getElementById('autoReindex').checked) {
        resultsDiv.innerHTML += `<div class="upload-result-item">🔄 Réindexation en cours...</div>`;
        await triggerReindexInternal();
        resultsDiv.innerHTML += `<div class="upload-result-item success">✅ Index mis à jour!</div>`;
    }

    loadFileTree();
}

async function triggerReindex() {
    startProgress('Réindexation en cours...');
    addMessage('assistant', '🔄 Lancement de la réindexation...');

    try {
        const response = await fetch(`/api/index/${currentProject}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            addMessage('assistant', `✅ Réindexation terminée!<br>• Nouveaux: ${data.new || 0}<br>• Modifiés: ${data.modified || 0}<br>• Supprimés: ${data.deleted || 0}`);
            finishProgress('Index mis à jour!');
        } else {
            throw new Error(data.detail || 'Erreur');
        }
    } catch (err) {
        addMessage('assistant', '❌ Erreur: ' + err.message);
        failProgress('Erreur réindexation');
    }
}

async function triggerReindexInternal() {
    try {
        await fetch(`/api/index/${currentProject}`, { method: 'POST' });
    } catch (err) {
        console.error('Reindex error:', err);
    }
}

// ========== STATS & GRAPH ==========

async function showStats() {
    try {
        const response = await fetch(`/api/stats/${currentProject}`);
        const stats = await response.json();

        let content = `<strong>📊 Statistiques - ${currentProject}</strong><br><br>`;
        content += `<strong>Index:</strong><br>`;
        content += `• Fichiers: ${stats.index?.file_count || 0}<br>`;
        content += `• Chunks: ${stats.index?.total_chunks || 0}<br><br>`;
        content += `<strong>Graphe:</strong><br>`;
        content += `• Nœuds: ${stats.graph?.node_count || 0}<br>`;
        content += `• Relations: ${stats.graph?.relationship_count || 0}`;

        addMessage('assistant', content);
    } catch (error) {
        addMessage('assistant', '❌ Erreur: ' + error.message);
    }
}

async function populateGraph() {
    addMessage('assistant', '🔄 Lancement de la population du graphe...');
    startProgress('Initialisation...');

    try {
        const response = await fetch(`/api/graph/populate/${currentProject}`, {
            method: 'POST'
        });
        const result = await response.json();

        if (result.status === 'already_running') {
            addMessage('assistant', '⏳ Population déjà en cours. Suivi de la progression...');
        } else if (result.status === 'started') {
            addMessage('assistant', '✅ Population lancée! Suivi en temps réel...');
        }

        startGraphPolling();

    } catch (error) {
        addMessage('assistant', '❌ Erreur: ' + error.message);
        failProgress('Erreur de lancement');
    }
}

function startGraphPolling() {
    if (graphPollInterval) clearInterval(graphPollInterval);

    let pollCount = 0;
    const maxPolls = 200;

    graphPollInterval = setInterval(async () => {
        pollCount++;

        try {
            const response = await fetch('/api/task/graph-status');
            const status = await response.json();

            updateGraphStatus(status);

            if (status.completed && status.result) {
                clearInterval(graphPollInterval);
                graphPollInterval = null;
                addMessage('assistant',
                    `✅ Graphe peuplé avec succès!<br>• ${status.result.nodes} nœuds<br>• ${status.result.relationships} relations<br>⏱️ Temps: ${status.elapsed}`
                );
                finishProgress('Graphe peuplé!');
                return;
            }

            if (status.error) {
                clearInterval(graphPollInterval);
                graphPollInterval = null;
                addMessage('assistant', '❌ Erreur: ' + status.error);
                failProgress('Erreur: ' + status.error);
                return;
            }

            if (pollCount >= maxPolls) {
                clearInterval(graphPollInterval);
                graphPollInterval = null;
                addMessage('assistant', '⚠️ Timeout: population trop longue (5min). Vérifie les logs serveur.');
                finishProgress('Timeout');
                return;
            }

        } catch (e) {
            console.error('Polling error:', e);
        }
    }, 1500);
}

function updateGraphStatus(status) {
    const percent = status.percent || 0;
    const step = status.step || 'En cours...';
    const file = status.current_file || '';
    const elapsed = status.elapsed || '';

    let statusMsg = `${step}`;
    if (status.total > 0) {
        statusMsg += ` (${status.progress}/${status.total} - ${percent}%)`;
    }
    if (file) {
        statusMsg += `<br><small>📄 ${file}</small>`;
    }
    if (elapsed) {
        statusMsg += ` <small>[${elapsed}]</small>`;
    }

    setStatus(statusMsg, 'info');
}

// ========== AI PERMISSION ==========

function showAIConfirmModal(action, targetFile, content, mode = 'append') {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'ai-permission-modal';
        modal.id = 'aiPermissionModal';

        const modeLabel = mode === 'append' ? '➕ Ajouter à la fin' :
            mode === 'replace' ? '🔄 Remplacer tout' : '📄 Créer nouveau';
        const modeColor = mode === 'append' ? '#10b981' :
            mode === 'replace' ? '#f59e0b' : '#3b82f6';

        const safeContent = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .substring(0, 800);

        modal.innerHTML = `
            <div class="ai-permission-content">
                <div class="ai-permission-header">
                    <span class="ai-icon">🤖</span>
                    <h3>L'IA demande l'autorisation</h3>
                </div>
                
                <div class="ai-action-info">
                    <div class="ai-action-row">
                        <span class="ai-label">Action:</span>
                        <span class="ai-value" style="color: ${modeColor}">${modeLabel}</span>
                    </div>
                    <div class="ai-action-row">
                        <span class="ai-label">Fichier:</span>
                        <span class="ai-value">📄 ${targetFile}</span>
                    </div>
                    <div class="ai-action-row">
                        <span class="ai-label">Taille:</span>
                        <span class="ai-value">${content.length} caractères</span>
                    </div>
                </div>
                
                <div class="ai-preview-label">👁️ Aperçu du contenu:</div>
                <div class="ai-permission-preview">${safeContent}${content.length > 800 ? '\n\n... (tronqué)' : ''}</div>
                
                <div class="ai-permission-buttons">
                    <button class="ai-btn ai-btn-cancel" id="aiRejectBtn">
                        ❌ Refuser
                    </button>
                    <button class="ai-btn ai-btn-accept" id="aiAcceptBtn">
                        ✅ Autoriser
                    </button>
                </div>
                
                <div class="ai-permission-hint">
                    💡 Vous gardez le contrôle total sur vos fichiers
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        document.getElementById('aiAcceptBtn').onclick = () => {
            modal.remove();
            resolve(true);
        };
        document.getElementById('aiRejectBtn').onclick = () => {
            modal.remove();
            resolve(false);
        };

        const escHandler = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', escHandler);
                resolve(false);
            }
        };
        document.addEventListener('keydown', escHandler);

        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.remove();
                resolve(false);
            }
        };
    });
}

// ========== CONFIGURATION ==========

let actualApiKey = ''; // Stocke la vraie clé API pour l'affichage

async function openConfigModal() {
    document.getElementById('configModal').style.display = 'flex';
    await loadCurrentApiKey();
}

function closeConfigModal() {
    document.getElementById('configModal').style.display = 'none';
    document.getElementById('newApiKey').value = '';
    actualApiKey = '';
}

async function loadCurrentApiKey() {
    try {
        const response = await fetch('/api/config/apikey');
        const data = await response.json();

        const input = document.getElementById('currentApiKey');
        input.value = data.masked_key || '************';
        actualApiKey = data.masked_key || '';

        if (!data.has_key) {
            input.placeholder = 'Aucune clé configurée';
        }
    } catch (error) {
        console.error('Erreur chargement clé API:', error);
        document.getElementById('currentApiKey').value = 'Erreur de chargement';
    }
}

async function saveApiKey() {
    const newKey = document.getElementById('newApiKey').value.trim();

    if (!newKey) {
        alert('Veuillez entrer une clé API');
        return;
    }

    if (!newKey.startsWith('sk-or-')) {
        if (!confirm('La clé ne commence pas par "sk-or-". Continuer quand même ?')) {
            return;
        }
    }

    try {
        const response = await fetch('/api/config/apikey', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: newKey })
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Clé API enregistrée avec succès!\n\nRedémarrez le serveur pour que les changements prennent effet.');
            document.getElementById('newApiKey').value = '';
            await loadCurrentApiKey();
        } else {
            throw new Error(data.detail || 'Erreur inconnue');
        }
    } catch (error) {
        alert('❌ Erreur lors de la sauvegarde: ' + error.message);
    }
}

function toggleApiKeyVisibility() {
    const input = document.getElementById('currentApiKey');
    const btn = event.target;

    if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = '🙈';
    } else {
        input.type = 'password';
        btn.textContent = '👁️';
    }
}
