"""
Serveur web FastAPI pour l'Assistant Fiction RAG - Ecrituria v2.0
Interface graphique avec visualisation du graphe de connaissances
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import os
import sys
from typing import List, Optional, Dict, Any
import json
import asyncio
import threading
from datetime import datetime, timedelta

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===== GLOBAL TASK STATUS =====
# Statut global pour les tâches longues (population graphe, etc.)
TASK_STATUS = {
    "populate_graph": {
        "running": False,
        "progress": 0,
        "total": 0,
        "current_file": "",
        "step": "",
        "started_at": None,
        "error": None,
        "completed": False,
        "result": None
    }
}

from src.rag import ask, get_relevant_passages
from src.llm_providers import get_llm_factory, list_available_models, PRESET_MODELS

app = FastAPI(
    title="Écrituria v2.0",
    description="Assistant Fiction RAG avec GraphRAG et agents spécialisés",
    version="2.0.0"
)

# CORS pour le développement
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
PROJECT_NAME = "anomalie2084"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data"


# Modèles Pydantic
class ChatMessage(BaseModel):
    question: str
    show_sources: bool = False
    project: str = PROJECT_NAME
    model: str | None = None
    use_graph: bool = False
    use_agents: bool = False


class SearchQuery(BaseModel):
    query: str
    k: int = 5
    project: str = PROJECT_NAME


class GraphQuery(BaseModel):
    project: str = PROJECT_NAME
    entity_id: str | None = None
    depth: int = 2


# Routes API
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Page principale de l'application Ecrituria v2.0"""
    return get_html_interface()


@app.get("/api/projects")
async def list_projects():
    """Liste les projets disponibles"""
    projects = []
    if DATA_PATH.exists():
        for folder in DATA_PATH.iterdir():
            if folder.is_dir() and not folder.name.startswith('.'):
                projects.append({
                    "name": folder.name,
                    "path": str(folder),
                    "has_index": (BASE_DIR / "db" / folder.name).exists()
                })
    return projects


@app.get("/api/files/{project}")
async def get_files(project: str):
    """Récupère la liste des fichiers d'un projet"""
    try:
        project_path = DATA_PATH / project
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Projet non trouvé: {project}")
        
        files_by_folder = {}
        
        for folder in project_path.iterdir():
            if folder.is_dir() and not folder.name.startswith('.'):
                files = [f.name for f in folder.glob("*.md")]
                files.extend([f.name for f in folder.glob("*.txt")])
                if files:
                    files_by_folder[folder.name] = sorted(files)
        
        return files_by_folder
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/file/{project}/{folder}/{filename}")
async def get_file_content(project: str, folder: str, filename: str):
    """Récupère le contenu d'un fichier"""
    file_path = DATA_PATH / project / folder / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Conversion markdown vers HTML basique
    html_content = markdown_to_html(content)
    
    return {
        "filename": filename,
        "folder": folder,
        "content": content,
        "content_html": html_content
    }


class FileWriteRequest(BaseModel):
    content: str
    append: bool = False  # True = ajouter à la fin, False = remplacer


@app.post("/api/file/{project}/{folder}/{filename}")
async def write_file_content(project: str, folder: str, filename: str, request: FileWriteRequest):
    """Écrit ou modifie le contenu d'un fichier"""
    file_path = DATA_PATH / project / folder / filename
    
    # Sécurité : vérifier que le chemin reste dans DATA_PATH
    try:
        file_path.resolve().relative_to(DATA_PATH.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Chemin non autorisé")
    
    # Créer le dossier si nécessaire
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if request.append and file_path.exists():
            # Mode ajout
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write("\n\n" + request.content)
            mode = "ajouté"
        else:
            # Mode remplacement ou nouveau fichier
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(request.content)
            mode = "écrit" if file_path.exists() else "créé"
        
        return {
            "success": True,
            "message": f"Fichier {mode} avec succès",
            "path": str(file_path.relative_to(DATA_PATH))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'écriture: {str(e)}")


@app.delete("/api/file/{project}/{folder}/{filename}")
async def delete_file(project: str, folder: str, filename: str):
    """Supprime un fichier"""
    file_path = DATA_PATH / project / folder / filename
    
    # Sécurité
    try:
        file_path.resolve().relative_to(DATA_PATH.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Chemin non autorisé")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    try:
        file_path.unlink()
        return {"success": True, "message": "Fichier supprimé"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.get("/api/models")
async def get_models():
    """Liste les modèles disponibles"""
    models = []
    
    # Modèles présets
    for name, config in PRESET_MODELS.items():
        models.append({
            "id": config.name,
            "label": f"{name} - {config.description[:50]}",
            "provider": config.provider.value
        })
    
    # Modèles Ollama si disponible
    try:
        factory = get_llm_factory()
        available = list_available_models()
        
        if "ollama" in available:
            for model in available["ollama"][:5]:  # Limiter
                models.append({
                    "id": model,
                    "label": f"🏠 {model} (local)",
                    "provider": "ollama"
                })
    except Exception:
        pass
    
    return models


@app.post("/api/chat")
async def chat(message: ChatMessage):
    """Envoie une question à l'IA et retourne la réponse"""
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env")
        
        # Déterminer le mode
        if message.use_agents:
            # Utiliser l'orchestrateur d'agents
            from src.agents.orchestrator import AgentOrchestrator
            orchestrator = AgentOrchestrator(message.project)
            result = orchestrator.run(message.question, show_chain=False)
            
            return {
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "workflow": result.get("workflow", ""),
                "agents": result.get("agent_chain", [])
            }
        
        elif message.use_graph:
            # Utiliser GraphRAG
            from src.graph.graph_rag import GraphRAGEngine
            engine = GraphRAGEngine(message.project, model=message.model or "gpt-4o-mini")
            result = engine.ask(message.question, show_sources=message.show_sources)
            
            if message.show_sources:
                return {
                    "answer": result["answer"],
                    "sources": [
                        doc.metadata.get('relative_path', 'source inconnue')
                        for doc in result.get("vector_sources", [])
                    ],
                    "graph_entities": result.get("graph_entities", []),
                    "detected_entities": result.get("detected_entities", [])
                }
            return {"answer": result, "sources": []}
        
        else:
            # RAG classique (avec hybrid search + reranking)
            result = ask(
                message.project,
                message.question,
                model=message.model or "gpt-4o-mini",
                show_sources=message.show_sources,
                use_hybrid=True,
                use_reranking=True
            )
            
            if message.show_sources:
                sources = [
                    doc.metadata.get('relative_path', 'source inconnue')
                    for doc in result.get('sources', [])
                ]
                return {"answer": result['answer'], "sources": sources}
            
            return {"answer": result, "sources": []}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def search(query: SearchQuery):
    """Recherche dans les documents"""
    try:
        passages = get_relevant_passages(query.project, query.query, k=query.k)
        results = []
        
        for doc in passages:
            results.append({
                "source": doc.metadata.get('relative_path', 'source inconnue'),
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
            })
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/{project}")
async def get_graph_data(project: str, depth: int = 2):
    """Récupère les données du graphe pour visualisation"""
    try:
        from src.graph.neo4j_client import get_neo4j_client
        
        client = get_neo4j_client(simulation_mode=True)
        
        # Récupérer tous les nœuds
        nodes = client.find_nodes(limit=100)
        
        # Formater pour la visualisation
        graph_nodes = []
        for node in nodes:
            graph_nodes.append({
                "id": node.get("id", ""),
                "label": node.get("nom", node.get("name", node.get("id", ""))),
                "type": node.get("label", "Unknown"),
                "properties": {k: v for k, v in node.items() if k not in ["id", "label"]}
            })
        
        # Récupérer les relations (mode simulation simplifié)
        edges = []
        for node in nodes:
            node_id = node.get("id", "")
            rels = client.get_relationships(node_id, direction="outgoing")
            for rel in rels:
                edges.append({
                    "source": node_id,
                    "target": rel.get("target_id", rel.get("other_id", "")),
                    "type": rel.get("type", "LIEN"),
                    "properties": {k: v for k, v in rel.items() if k not in ["source_id", "target_id", "type"]}
                })
        
        return {
            "nodes": graph_nodes,
            "edges": edges,
            "stats": client.get_stats()
        }
    except Exception as e:
        return {"nodes": [], "edges": [], "error": str(e)}


def run_populate_graph_task(project: str):
    """Tâche en arrière-plan pour peupler le graphe avec suivi de progression."""
    global TASK_STATUS
    status = TASK_STATUS["populate_graph"]
    
    try:
        status["running"] = True
        status["error"] = None
        status["completed"] = False
        status["started_at"] = datetime.now().isoformat()
        status["step"] = "Initialisation..."
        status["progress"] = 0
        status["total"] = 0
        status["current_file"] = ""
        
        from src.graph.graph_rag import GraphRAGEngine
        from src.graph.neo4j_client import Node, Relationship
        from src.loaders import load_project_documents
        
        status["step"] = "Chargement du moteur GraphRAG..."
        engine = GraphRAGEngine(project)
        
        # Charger les documents
        status["step"] = "Chargement des documents..."
        project_path = Path("data") / project
        docs = load_project_documents(project_path, extensions=[".md", ".txt"])
        status["total"] = len(docs)
        
        all_entities = []
        all_relations = []
        
        # Extraire entités de chaque document
        status["step"] = "Extraction des entités..."
        for i, doc in enumerate(docs):
            source_file = doc.metadata.get("relative_path", f"doc_{i}")
            status["current_file"] = source_file
            status["progress"] = i + 1
            
            try:
                entities, relations = engine.entity_extractor.extract_from_document(doc)
                all_entities.extend(entities)
                all_relations.extend(relations)
            except Exception as e:
                print(f"⚠️ Erreur extraction {source_file}: {e}")
        
        # Dédupliquer entités
        status["step"] = "Dédupplication des entités..."
        unique_entities = {}
        for entity in all_entities:
            if entity.id not in unique_entities:
                unique_entities[entity.id] = entity
            else:
                existing = unique_entities[entity.id]
                existing.properties.update(entity.properties)
        
        entities_list = list(unique_entities.values())
        
        # Ajouter au graphe
        status["step"] = f"Ajout de {len(entities_list)} entités au graphe..."
        status["total"] = len(entities_list) + len(all_relations)
        status["progress"] = 0
        
        for i, entity in enumerate(entities_list):
            node = Node(
                id=entity.id,
                label=entity.type,
                properties={
                    "nom": entity.name,
                    **entity.properties
                }
            )
            engine.graph_client.create_node(node)
            status["progress"] = i + 1
            status["current_file"] = f"Entité: {entity.name}"
        
        status["step"] = f"Ajout de {len(all_relations)} relations..."
        for i, rel in enumerate(all_relations):
            relationship = Relationship(
                source_id=rel.source_entity,
                target_id=rel.target_entity,
                type=rel.relation_type,
                properties=rel.properties
            )
            engine.graph_client.create_relationship(relationship)
            status["progress"] = len(entities_list) + i + 1
            status["current_file"] = f"Relation: {rel.relation_type}"
        
        stats = engine.graph_client.get_stats()
        
        status["step"] = "Terminé!"
        status["completed"] = True
        status["running"] = False
        status["result"] = {
            "nodes": stats["node_count"],
            "relationships": stats["relationship_count"]
        }
        
    except Exception as e:
        status["error"] = str(e)
        status["running"] = False
        status["completed"] = False
        status["step"] = f"Erreur: {e}"
        import traceback
        traceback.print_exc()


@app.post("/api/graph/populate/{project}")
async def populate_graph(project: str):
    """Lance la population du graphe dans un thread séparé"""
    global TASK_STATUS
    status = TASK_STATUS["populate_graph"]
    
    # Vérifier si déjà en cours
    if status["running"]:
        return {
            "status": "already_running",
            "message": "Population déjà en cours, utilisez /api/graph/status pour suivre."
        }
    
    # Initialiser le statut AVANT de lancer la tâche
    status["running"] = True
    status["completed"] = False
    status["error"] = None
    status["progress"] = 0
    status["total"] = 0
    status["step"] = "Démarrage..."
    status["current_file"] = ""
    status["started_at"] = datetime.now().isoformat()
    status["result"] = None
    
    # Lancer dans un thread séparé pour ne pas bloquer les requêtes
    thread = threading.Thread(target=run_populate_graph_task, args=(project,), daemon=True)
    thread.start()
    
    return {
        "status": "started",
        "message": "Population du graphe lancée. Utilisez /api/graph/status pour suivre la progression."
    }


@app.get("/api/task/graph-status")
async def get_graph_status():
    """Récupère le statut de la population du graphe"""
    status = TASK_STATUS["populate_graph"]
    
    # Calcul du pourcentage
    percent = 0
    if status["total"] > 0:
        percent = int((status["progress"] / status["total"]) * 100)
    
    # Temps écoulé
    elapsed = ""
    if status["started_at"]:
        try:
            start = datetime.fromisoformat(status["started_at"])
            delta = datetime.now() - start
            elapsed = f"{int(delta.total_seconds())}s"
        except:
            pass
    
    return {
        "running": status["running"],
        "completed": status["completed"],
        "progress": status["progress"],
        "total": status["total"],
        "percent": percent,
        "current_file": status["current_file"],
        "step": status["step"],
        "elapsed": elapsed,
        "error": status["error"],
        "result": status["result"]
    }


@app.get("/api/stats/{project}")
async def get_project_stats(project: str):
    """Récupère les statistiques d'un projet"""
    try:
        from src.indexer import get_index_stats
        from src.graph.neo4j_client import get_neo4j_client
        
        stats = {
            "project": project,
            "index": {},
            "graph": {}
        }
        
        # Stats de l'index
        try:
            stats["index"] = get_index_stats(project)
        except Exception:
            stats["index"] = {"error": "Index non disponible"}
        
        # Stats du graphe
        try:
            client = get_neo4j_client(simulation_mode=True)
            stats["graph"] = client.get_stats()
        except Exception:
            stats["graph"] = {"error": "Graphe non disponible"}
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Utilitaires
def markdown_to_html(content: str) -> str:
    """Conversion Markdown vers HTML basique"""
    import re
    
    # Headers
    content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
    
    # Bold et italic
    content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
    
    # Listes
    content = re.sub(r'^- (.+)$', r'<li>\1</li>', content, flags=re.MULTILINE)
    
    # Paragraphes
    content = re.sub(r'\n\n', '</p><p>', content)
    content = f'<p>{content}</p>'
    
    return content


def get_html_interface() -> str:
    """Retourne l'interface HTML complète v2.0"""
    return """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>✨ Écrituria v2.0 - Assistant Fiction RAG</title>
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #8b5cf6;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-input: #334155;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --border: #475569;
            --success: #22c55e;
            --warning: #f59e0b;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
            overflow-y: auto;
        }
        
        .app-container {
            display: grid;
            grid-template-columns: 280px 1fr 400px;
            min-height: 100vh;
        }
        
        /* Sidebar */
        .sidebar {
            background: var(--bg-card);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
        }
        
        .logo {
            padding: 20px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            text-align: center;
        }
        
        .logo h1 { font-size: 24px; margin-bottom: 5px; }
        .logo span { font-size: 12px; opacity: 0.8; }
        
        .project-select {
            padding: 15px;
            border-bottom: 1px solid var(--border);
        }
        
        .project-select select {
            width: 100%;
            padding: 10px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            font-size: 14px;
        }
        
        .file-tree {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }
        
        .folder { margin: 10px 0; }
        
        .folder-name {
            display: flex;
            align-items: center;
            padding: 8px 12px;
            cursor: pointer;
            border-radius: 6px;
            transition: background 0.2s;
        }
        
        .folder-name:hover { background: var(--bg-input); }
        
        .file-item {
            padding: 6px 12px 6px 30px;
            cursor: pointer;
            border-radius: 6px;
            font-size: 13px;
            color: var(--text-muted);
            transition: all 0.2s;
        }
        
        .file-item:hover {
            background: var(--bg-input);
            color: var(--text);
        }
        
        .file-item.active {
            background: var(--primary);
            color: white;
        }
        
        /* Main Content */
        .main-content {
            display: flex;
            flex-direction: column;
            background: var(--bg-dark);
        }
        
        .toolbar {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 15px 20px;
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
        }
        
        .toolbar .highlight-box {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .highlight-input {
            width: 180px;
            padding: 8px 10px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            font-size: 13px;
        }
        
        .highlight-input:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .toolbar h2 {
            flex: 1;
            font-size: 18px;
            font-weight: 500;
        }
        
        .toolbar-btn {
            padding: 8px 16px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text);
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
        }
        
        .toolbar-btn:hover { background: var(--primary); }
        .toolbar-btn.active { background: var(--primary); }
        
        .content-area {
            flex: 1;
            overflow-y: auto;
            padding: 30px;
        }
        
        .file-viewer {
            width: min(1100px, 100%);
            margin: 0 auto;
            background: var(--bg-card);
            border-radius: 12px;
            padding: 30px;
            line-height: 1.8;
        }
        
        .file-viewer h1 { font-size: 28px; margin: 20px 0; color: var(--primary); }
        .file-viewer h2 { font-size: 22px; margin: 16px 0; }
        .file-viewer h3 { font-size: 18px; margin: 14px 0; color: var(--text-muted); }
        .file-viewer p { margin: 12px 0; }
        
        .empty-state {
            text-align: center;
            padding: 60px;
            color: var(--text-muted);
        }
        
        .empty-state-icon { font-size: 64px; margin-bottom: 20px; }
        
        /* Chat Panel */
        .chat-panel {
            background: var(--bg-card);
            border-left: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }
        
        .chat-header {
            padding: 20px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
        }
        
        .chat-header h3 { font-size: 18px; margin-bottom: 10px; }
        
        .chat-options {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .chat-help {
            margin-top: 6px;
            font-size: 11px;
            color: var(--text-muted);
            line-height: 1.4;
        }
        
        .chat-options label {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 12px;
            cursor: pointer;
        }
        
        .chat-options input[type="checkbox"] {
            accent-color: var(--success);
        }
        
        .model-select {
            flex: 1;
            min-width: 150px;
            padding: 8px 12px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text);
            font-size: 12px;
            cursor: pointer;
        }
        
        .model-select:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .model-select option {
            background: var(--bg-card);
            color: var(--text);
            padding: 8px;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            max-height: calc(100vh - 240px);
        }
        
        .message {
            margin-bottom: 20px;
            animation: fadeIn 0.3s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message-user {
            background: var(--primary);
            padding: 12px 16px;
            border-radius: 16px 16px 4px 16px;
            margin-left: 40px;
        }
        
        .message-assistant {
            background: var(--bg-input);
            padding: 12px 16px;
            border-radius: 16px 16px 16px 4px;
            margin-right: 40px;
        }
        
        .message-label {
            font-size: 11px;
            color: var(--text-muted);
            margin-bottom: 5px;
            font-weight: 600;
        }
        
        .message-sources {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--border);
            font-size: 12px;
        }
        
        .source-item {
            display: inline-block;
            padding: 4px 8px;
            background: var(--bg-dark);
            border-radius: 4px;
            margin: 4px 4px 0 0;
        }
        
        /* Actions sur les messages */
        .message-actions {
            margin-top: 12px;
            padding-top: 10px;
            border-top: 1px dashed var(--border);
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .action-btn {
            padding: 6px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--bg-dark);
            color: var(--text);
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }
        
        .action-btn:hover {
            background: var(--primary);
            border-color: var(--primary);
            color: white;
        }
        
        .action-btn:disabled {
            opacity: 0.5;
            cursor: wait;
        }
        
        .copy-btn:hover { background: #10b981; border-color: #10b981; }
        .apply-btn:hover { background: #3b82f6; border-color: #3b82f6; }
        .new-file-btn:hover { background: #8b5cf6; border-color: #8b5cf6; }
        
        /* Actions fichiers */
        .file-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .separator {
            color: var(--border);
            margin: 0 5px;
        }
        
        .danger-btn {
            color: #f87171 !important;
        }
        .danger-btn:hover {
            background: #ef4444 !important;
            color: white !important;
        }
        
        .success-btn {
            background: var(--primary) !important;
            color: white !important;
        }
        .success-btn:hover {
            background: #059669 !important;
        }
        
        /* Mode édition */
        .edit-mode {
            display: flex;
            flex-direction: column;
            height: 100%;
            gap: 10px;
        }
        
        .edit-textarea {
            flex: 1;
            width: 100%;
            min-height: 400px;
            padding: 20px;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 14px;
            line-height: 1.6;
            background: var(--bg-dark);
            color: var(--text);
            border: 2px solid var(--border);
            border-radius: 8px;
            resize: vertical;
            outline: none;
        }
        
        .edit-textarea:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
        }
        
        .edit-toolbar {
            display: flex;
            gap: 10px;
            align-items: center;
            padding: 10px;
            background: var(--bg-dark);
            border-radius: 8px;
        }
        
        .save-btn {
            padding: 10px 20px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }
        .save-btn:hover {
            background: #059669;
            transform: translateY(-1px);
        }
        
        .cancel-btn {
            padding: 10px 20px;
            background: var(--bg-card);
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .cancel-btn:hover {
            background: #ef4444;
            color: white;
            border-color: #ef4444;
        }
        
        .edit-hint {
            margin-left: auto;
            font-size: 12px;
            color: var(--text-muted);
        }
        
        .edit-btn.active {
            background: var(--primary) !important;
            color: white !important;
        }
        
        /* Droits IA */
        .ai-permission-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .ai-permission-content {
            background: var(--bg-card);
            padding: 30px;
            border-radius: 12px;
            max-width: 500px;
            border: 2px solid var(--primary);
        }
        
        .ai-permission-content h3 {
            color: var(--primary);
            margin-bottom: 15px;
        }
        
        .ai-permission-preview {
            background: var(--bg-dark);
            padding: 15px;
            border-radius: 8px;
            max-height: 200px;
            overflow-y: auto;
            margin: 15px 0;
            font-size: 13px;
            white-space: pre-wrap;
        }
        
        .ai-permission-buttons {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        
        .agent-badge {
            display: inline-block;
            padding: 2px 8px;
            background: var(--secondary);
            border-radius: 12px;
            font-size: 10px;
            margin-right: 5px;
        }
        
        .chat-input-area {
            padding: 20px;
            border-top: 1px solid var(--border);
        }
        
        /* Global status */
        .status {
            position: fixed;
            right: 16px;
            bottom: 16px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.25);
            z-index: 9999;
        }
        
        .status.hidden { display: none; }
        
        .status .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--text-muted);
        }
        .status.info .dot { background: var(--warning); }
        .status.success .dot { background: var(--success); }
        .status.error .dot { background: #f87171; }
        
        .status .msg {
            font-size: 12px;
            color: var(--text);
        }
        
        .status .progress-wrap {
            flex: 1;
            height: 6px;
            background: var(--bg-input);
            border-radius: 6px;
            overflow: hidden;
            border: 1px solid var(--border);
        }
        
        .status .progress-bar {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            transition: width 0.4s ease;
        }
        
        .chat-input {
            display: flex;
            gap: 10px;
        }
        
        .chat-input textarea {
            flex: 1;
            padding: 12px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: var(--text);
            font-family: inherit;
            font-size: 14px;
            resize: none;
        }
        
        .highlight {
            background: rgba(245, 158, 11, 0.25);
            color: #fef3c7;
            padding: 2px 3px;
            border-radius: 4px;
        }
        
        .chat-input textarea:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .btn-send {
            padding: 12px 24px;
            background: var(--primary);
            border: none;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-send:hover {
            background: var(--primary-dark);
            transform: translateY(-2px);
        }
        
        .btn-send:disabled {
            background: var(--bg-input);
            cursor: not-allowed;
            transform: none;
        }
        
        .spinner {
            width: 24px;
            height: 24px;
            border: 3px solid var(--bg-input);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="logo">
                <h1>✨ Écrituria</h1>
                <span>v2.0 - Assistant Fiction RAG</span>
            </div>
            
            <div class="project-select">
                <select id="projectSelect" onchange="loadProject()">
                    <option value="anomalie2084">📖 Anomalie 2084</option>
                </select>
            </div>
            
            <div class="file-tree" id="fileTree">
                <div class="empty-state">
                    <div class="spinner"></div>
                    <p style="margin-top: 10px;">Chargement...</p>
                </div>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="main-content">
            <div class="toolbar">
                <h2 id="pageTitle">Bienvenue sur Écrituria v2.0</h2>
                <div class="highlight-box">
                    <input id="highlightInput" class="highlight-input" type="text" placeholder="Surligner..." />
                    <button class="toolbar-btn" onclick="highlightText()">🎯 Surligner</button>
                    <button class="toolbar-btn" onclick="resetHighlight()">↺ Réinitialiser</button>
                </div>
                <button class="toolbar-btn" onclick="showStats()">📊 Stats</button>
                <button class="toolbar-btn" onclick="populateGraph()">🔗 Peupler Graphe</button>
                
                <!-- Actions fichier -->
                <div class="file-actions" id="fileActions" style="display:none;">
                    <span class="separator">|</span>
                    <button class="toolbar-btn edit-btn" onclick="toggleEditMode()" id="editBtn">✏️ Éditer</button>
                    <button class="toolbar-btn" onclick="duplicateFile()">📋 Dupliquer</button>
                    <button class="toolbar-btn" onclick="renameFile()">✏️ Renommer</button>
                    <button class="toolbar-btn danger-btn" onclick="deleteFile()">🗑️ Supprimer</button>
                </div>
                
                <button class="toolbar-btn success-btn" onclick="createNewFile()" style="margin-left:auto;">➕ Nouveau fichier</button>
            </div>
            
            <div class="content-area">
                <!-- Mode lecture -->
                <div id="fileContent" class="file-viewer">
                    <div class="empty-state">
                        <div class="empty-state-icon">📚</div>
                        <h3>Sélectionnez un fichier</h3>
                        <p>Choisissez un fichier dans la barre latérale pour afficher son contenu</p>
                        <p style="margin-top: 20px; font-size: 14px; color: var(--text-muted);">
                            <strong>Nouveautés v2.0:</strong><br>
                            🔍 Recherche hybride BM25 + vecteurs<br>
                            🔗 Graphe de connaissances (GraphRAG)<br>
                            🤖 Agents spécialisés<br>
                            🏠 Support modèles locaux (Ollama)
                        </p>
                    </div>
                </div>
                
                <!-- Mode édition -->
                <div id="editMode" class="edit-mode" style="display:none;">
                    <textarea id="editTextarea" class="edit-textarea" placeholder="Contenu du fichier..."></textarea>
                    <div class="edit-toolbar">
                        <button class="save-btn" onclick="saveFile()">💾 Sauvegarder</button>
                        <button class="cancel-btn" onclick="cancelEdit()">❌ Annuler</button>
                        <span class="edit-hint">Ctrl+S pour sauvegarder</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Chat Panel -->
        <div class="chat-panel">
            <div class="chat-header">
                <h3>💬 Chat IA</h3>
                <div class="chat-options">
                    <select id="modelSelect" class="model-select"></select>
                    <label title="Active le graphe de connaissances (extraction d'entités, contextes reliés) en plus du RAG vectoriel">
                        <input type="checkbox" id="useGraph"> GraphRAG
                    </label>
                    <label title="Orchestrateur multi-agents (Rechercheur, Coherence, Creatif) pour des réponses chaînées et spécialisées">
                        <input type="checkbox" id="useAgents"> Agents
                    </label>
                </div>
                <div class="chat-help">
                    GraphRAG = graphe + RAG vectoriel. Agents = orchestration (Rechercheur, Coherence, Creatif).
                </div>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <div class="message">
                    <div class="message-assistant">
                        <div class="message-label">✨ ÉCRITURIA v2.0</div>
                        Bienvenue! Je suis votre assistant d'écriture augmenté.<br><br>
                        <strong>Nouveautés:</strong><br>
                        • Cochez <em>GraphRAG</em> pour utiliser le graphe de connaissances<br>
                        • Cochez <em>Agents</em> pour des réponses multi-agents<br>
                        • Recherche hybride BM25+vecteurs activée par défaut
                    </div>
                </div>
            </div>
            
            <div class="chat-input-area">
                <div class="chat-input">
                    <textarea id="chatInput" rows="3" placeholder="Posez votre question..."></textarea>
                    <button id="sendButton" class="btn-send" onclick="sendMessage()">Envoyer</button>
                </div>
            </div>
        </div>
        
        <div id="globalStatus" class="status hidden">
            <div class="dot"></div>
            <div class="msg">Prêt</div>
            <div class="progress-wrap"><div class="progress-bar" id="statusProgress"></div></div>
        </div>
    </div>
    
    <script>
        let currentProject = 'anomalie2084';
        let currentFile = null;  // Fichier actuellement ouvert (ex: "personnages/hero.md")
        let fileContentRaw = '';
        let longChatTimer = null;
        let longGraphTimer = null;
        let progressTimer = null;
        let progressValue = 0;
        
        // Initialisation
        window.addEventListener('DOMContentLoaded', () => {
            loadProjects();
            loadFileTree();
            loadModels();
            
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
        });
        
        function setStatus(text, mode = 'info') {
            const box = document.getElementById('globalStatus');
            if (!box) return;
            const dot = box.querySelector('.dot');
            const msg = box.querySelector('.msg');
            msg.textContent = text || '...';
            box.classList.remove('hidden', 'info', 'success', 'error');
            box.classList.add(mode || 'info');
            if (dot) {
                dot.className = 'dot';
            }
            const bar = document.getElementById('statusProgress');
            if (bar) bar.style.width = '0%';
        }
        
        function clearStatus() {
            const box = document.getElementById('globalStatus');
            if (box) box.classList.add('hidden');
            const bar = document.getElementById('statusProgress');
            if (bar) bar.style.width = '0%';
        }
        
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
        
        let fileContentRawText = '';  // Contenu texte brut pour l'éditeur
        
        async function loadFile(folder, filename) {
            try {
                document.querySelectorAll('.file-item').forEach(el => el.classList.remove('active'));
                if (event && event.target) event.target.classList.add('active');
                
                const response = await fetch(`/api/file/${currentProject}/${folder}/${filename}`);
                const data = await response.json();
                
                // Tracker le fichier courant
                currentFile = `${folder}/${filename}`;
                
                // Stocker les deux versions du contenu
                fileContentRaw = data.content_html;      // HTML pour l'affichage
                fileContentRawText = data.content;       // Texte brut pour l'éditeur
                
                document.getElementById('fileContent').innerHTML = data.content_html;
                
                // Indicateur visuel du fichier ouvert
                document.getElementById('pageTitle').innerHTML = `📂 ${currentFile} <span style="font-size:11px;color:var(--primary)">(ouvert)</span>`;
                
                // Afficher les boutons d'action
                document.getElementById('fileActions').style.display = 'flex';
                
                // Revenir en mode lecture si on était en mode édition
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
                
                // Badges agents si utilisés
                if (data.agents && data.agents.length > 0) {
                    content = data.agents.map(a => 
                        `<span class="agent-badge">${a}</span>`
                    ).join('') + '<br><br>' + content;
                }
                
                // Sources
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
            
            // Pour les réponses IA, ajouter un bouton d'actions
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
        
        // Copier le contenu du message
        function copyMessageContent(btn) {
            const msgContent = btn.closest('.message-assistant, .message-user').querySelector('.message-content');
            const text = msgContent.innerText || msgContent.textContent;
            navigator.clipboard.writeText(text).then(() => {
                btn.textContent = '✅ Copié!';
                setTimeout(() => btn.textContent = '📋 Copier', 2000);
            });
        }
        
        // Ajouter au fichier actuellement ouvert
        async function applyToFile(btn) {
            if (!currentFile) {
                alert('Ouvrez d\\'abord un fichier dans la sidebar gauche');
                return;
            }
            
            const msgContent = btn.closest('.message-assistant').querySelector('.message-content');
            let text = msgContent.innerText || msgContent.textContent;
            
            // Nettoyer les sources et badges
            text = text.replace(/📚 Sources:.*$/s, '').trim();
            text = text.replace(/^(Rechercheur|Coherence|Creatif|GraphRAG)\s*/gm, '').trim();
            
            if (!confirm(`Ajouter ce contenu à "${currentFile}" ?`)) return;
            
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
                    // Recharger le fichier
                    loadFile(currentFile);
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
        
        // Créer un nouveau fichier avec le contenu de l'IA
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
        
        // ========== FONCTIONS ÉDITION UTILISATEUR ==========
        
        let isEditMode = false;
        let originalContent = '';
        
        // Créer un nouveau fichier vide (toolbar)
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
        
        // Basculer mode édition
        function toggleEditMode() {
            if (!currentFile) {
                alert('Ouvrez d\\'abord un fichier');
                return;
            }
            
            isEditMode = !isEditMode;
            const editBtn = document.getElementById('editBtn');
            const fileContent = document.getElementById('fileContent');
            const editMode = document.getElementById('editMode');
            const textarea = document.getElementById('editTextarea');
            
            if (isEditMode) {
                // Passer en mode édition
                originalContent = fileContentRawText || '';
                textarea.value = originalContent;
                fileContent.style.display = 'none';
                editMode.style.display = 'flex';
                editBtn.textContent = '👁️ Aperçu';
                editBtn.classList.add('active');
                textarea.focus();
            } else {
                // Retour mode lecture
                fileContent.style.display = 'block';
                editMode.style.display = 'none';
                editBtn.textContent = '✏️ Éditer';
                editBtn.classList.remove('active');
            }
        }
        
        // Sauvegarder les modifications
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
                    // Recharger et revenir en mode lecture
                    await loadFile(folder, filename);
                    toggleEditMode();
                } else {
                    throw new Error(data.detail || 'Erreur');
                }
            } catch (err) {
                alert('❌ Erreur: ' + err.message);
            }
        }
        
        // Annuler les modifications
        function cancelEdit() {
            if (confirm('Annuler les modifications ?')) {
                document.getElementById('editTextarea').value = originalContent;
                toggleEditMode();
            }
        }
        
        // Supprimer le fichier
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
        
        // Renommer le fichier
        async function renameFile() {
            if (!currentFile) return;
            
            const [folder, oldFilename] = currentFile.split('/');
            const newFilename = prompt('✏️ Nouveau nom:', oldFilename);
            
            if (!newFilename || newFilename === oldFilename) return;
            
            try {
                // Lire le contenu actuel
                const readResponse = await fetch(`/api/file/${currentProject}/${folder}/${oldFilename}`);
                const fileData = await readResponse.json();
                
                // Créer avec le nouveau nom
                const createResponse = await fetch(`/api/file/${currentProject}/${folder}/${newFilename}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: fileData.content, append: false })
                });
                
                if ((await createResponse.json()).success) {
                    // Supprimer l'ancien
                    await fetch(`/api/file/${currentProject}/${folder}/${oldFilename}`, { method: 'DELETE' });
                    
                    alert('✅ Fichier renommé !');
                    loadFileTree();
                    setTimeout(() => loadFile(folder, newFilename), 500);
                }
            } catch (err) {
                alert('❌ Erreur: ' + err.message);
            }
        }
        
        // Dupliquer le fichier
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
        
        // Raccourci clavier Ctrl+S
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 's' && isEditMode) {
                e.preventDefault();
                saveFile();
            }
            if (e.key === 'Escape' && isEditMode) {
                cancelEdit();
            }
        });
        
        // ========== DROITS IA ==========
        
        let aiPermissionLevel = 'ask';  // 'ask', 'auto', 'readonly'
        
        // Demander permission à l'utilisateur pour l'action IA
        function askAIPermission(action, targetFile, content) {
            return new Promise((resolve) => {
                const modal = document.createElement('div');
                modal.className = 'ai-permission-modal';
                modal.innerHTML = `
                    <div class="ai-permission-content">
                        <h3>🤖 L'IA veut ${action}</h3>
                        <p><strong>Fichier:</strong> ${targetFile}</p>
                        <div class="ai-permission-preview">${content.substring(0, 500)}${content.length > 500 ? '...' : ''}</div>
                        <div class="ai-permission-buttons">
                            <button class="cancel-btn" onclick="this.closest('.ai-permission-modal').remove(); window.aiPermissionResolve(false);">❌ Refuser</button>
                            <button class="save-btn" onclick="this.closest('.ai-permission-modal').remove(); window.aiPermissionResolve(true);">✅ Autoriser</button>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
                window.aiPermissionResolve = resolve;
            });
        }
        
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
        
        let graphPollInterval = null;
        
        async function populateGraph() {
            // Démarrer la population en arrière-plan
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
                
                // Démarrer le polling
                startGraphPolling();
                
            } catch (error) {
                addMessage('assistant', '❌ Erreur: ' + error.message);
                failProgress('Erreur de lancement');
            }
        }
        
        function startGraphPolling() {
            // Nettoyer un polling existant
            if (graphPollInterval) clearInterval(graphPollInterval);
            
            let pollCount = 0;
            const maxPolls = 200; // 5 min max (1.5s * 200 = 300s)
            
            // Polling toutes les 1.5 secondes
            graphPollInterval = setInterval(async () => {
                pollCount++;
                
                try {
                    const response = await fetch('/api/task/graph-status');
                    const status = await response.json();
                    
                    // Toujours mettre à jour l'affichage
                    updateGraphStatus(status);
                    
                    // Arrêter si terminé avec résultat
                    if (status.completed && status.result) {
                        clearInterval(graphPollInterval);
                        graphPollInterval = null;
                        addMessage('assistant', 
                            `✅ Graphe peuplé avec succès!<br>• ${status.result.nodes} nœuds<br>• ${status.result.relationships} relations<br>⏱️ Temps: ${status.elapsed}`
                        );
                        finishProgress('Graphe peuplé!');
                        return;
                    }
                    
                    // Arrêter si erreur
                    if (status.error) {
                        clearInterval(graphPollInterval);
                        graphPollInterval = null;
                        addMessage('assistant', '❌ Erreur: ' + status.error);
                        failProgress('Erreur: ' + status.error);
                        return;
                    }
                    
                    // Timeout après maxPolls
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
            
            // Mettre à jour la barre de progression
            const progressBar = document.getElementById('progressBar');
            const globalStatus = document.getElementById('globalStatus');
            
            if (progressBar) {
                progressBar.style.width = percent + '%';
            }
            
            // Message de statut détaillé
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
    </script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn
    import sys
    import io
    
    # Forcer UTF-8 pour Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("\n" + "=" * 60)
    print("[*] Demarrage d'Ecrituria v2.0")
    print("=" * 60)
    print("\n[>] Interface: http://localhost:8000")
    print("[>] API Docs: http://localhost:8000/docs")
    print("\nAppuyez sur Ctrl+C pour arreter\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
