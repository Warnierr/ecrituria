"""
Indexation des documents dans la base vectorielle ChromaDB.
Version 2.0 avec support de l'indexation incrémentale.
"""
import sys
import os
import io
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv

# Permet d'exécuter le fichier directement avec `python src/indexer.py ...`
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Chargement de l'environnement (.env) pour les clés API
load_dotenv(BASE_DIR / ".env")

# Compatibilité console Windows + emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Si seule OPENROUTER_API_KEY est définie, l'utiliser comme OPENAI_API_KEY pour OpenRouter
if not os.getenv("OPENAI_API_KEY") and os.getenv("OPENROUTER_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")

# Détecter automatiquement si la clé est OpenRouter (commence par sk-or-v1-)
openai_key = os.getenv("OPENAI_API_KEY", "")
is_openrouter_key = openai_key.startswith("sk-or-v1-") if openai_key else False

# Debug: afficher si la clé est chargée (masquée pour sécurité)
if openai_key:
    print(f"✓ Clé API détectée: {openai_key[:10]}... (OpenRouter: {is_openrouter_key})")
else:
    print("⚠️  Aucune clé API détectée dans OPENAI_API_KEY")

from src.loaders import load_project_documents, split_documents
from src.utils.file_hash import FileHashTracker, get_file_hash


class ProjectIndexer:
    """
    Indexeur de projet avec support de l'indexation incrémentale.
    
    L'indexation incrémentale permet de ne réindexer que les fichiers
    qui ont été modifiés, ajoutés ou supprimés, ce qui est beaucoup
    plus rapide que de tout reconstruire.
    """
    
    def __init__(
        self,
        project_name: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        use_openrouter: bool = None
    ):
        """
        Initialise l'indexeur.
        
        Args:
            project_name: Nom du projet (dossier dans data/)
            chunk_size: Taille des chunks en caractères
            chunk_overlap: Chevauchement entre chunks
            use_openrouter: Utiliser OpenRouter pour les embeddings (None = auto-détection)
        """
        self.project_name = project_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Chemins
        self.project_path = Path("data") / project_name
        self.db_path = Path("db") / project_name
        
        # Tracker de fichiers pour l'indexation incrémentale
        self.tracker = FileHashTracker(project_name)
        
        # Détection automatique d'OpenRouter si non spécifié
        if use_openrouter is None:
            use_openrouter = is_openrouter_key
        
        # Configuration des embeddings
        if use_openrouter:
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-ada-002",
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/fiction-assistant",
                    "X-Title": "Fiction Assistant RAG"
                }
            )
        else:
            self.embeddings = OpenAIEmbeddings()
    
    def _get_vectordb(self) -> Chroma:
        """Récupère ou crée la base vectorielle."""
        return Chroma(
            embedding_function=self.embeddings,
            persist_directory=str(self.db_path),
            collection_name=self.project_name
        )
    
    def build_full_index(self) -> dict:
        """
        Construit l'index complet depuis zéro.
        
        Returns:
            Dict avec les statistiques d'indexation
        """
        print(f"\n🔧 Construction complète de l'index pour '{self.project_name}'...")
        
        if not self.project_path.exists():
            raise FileNotFoundError(
                f"Le projet {self.project_name} n'existe pas.\n"
                f"Chemin attendu: {self.project_path.absolute()}"
            )
        
        # Charger tous les documents
        print(f"\n📚 Chargement des documents depuis {self.project_path}...")
        docs = load_project_documents(self.project_path)
        
        if not docs:
            print("⚠️  Aucun document trouvé.")
            return {"status": "empty", "files": 0, "chunks": 0}
        
        # Découper en chunks
        print(f"\n✂️  Découpage des documents...")
        chunks = split_documents(
            docs,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        # Supprimer l'ancien index
        if self.db_path.exists():
            shutil.rmtree(self.db_path)
            print(f"   ♻️  Ancien index supprimé")
        
        # Créer le nouvel index
        print(f"\n🔮 Création des embeddings...")
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(self.db_path),
            collection_name=self.project_name
        )
        
        # Mettre à jour le tracker
        self.tracker.clear()
        self._update_tracker_from_docs(docs, chunks)
        
        # Sauvegarder les métadonnées
        self.tracker.set_metadata("chunk_size", self.chunk_size)
        self.tracker.set_metadata("chunk_overlap", self.chunk_overlap)
        self.tracker.set_metadata("index_type", "full")
        
        stats = {
            "status": "success",
            "files": len(docs),
            "chunks": len(chunks),
            "db_path": str(self.db_path.absolute())
        }
        
        print(f"\n✅ Index construit avec succès!")
        print(f"   📊 {stats['files']} fichiers → {stats['chunks']} chunks")
        print(f"   💾 Sauvegardé dans: {stats['db_path']}")
        
        return stats
    
    def build_incremental_index(self) -> dict:
        """
        Met à jour l'index de façon incrémentale.
        
        Ne réindexe que les fichiers modifiés, ajoutés ou supprimés.
        
        Returns:
            Dict avec les statistiques de mise à jour
        """
        print(f"\n🔄 Mise à jour incrémentale de l'index pour '{self.project_name}'...")
        
        if not self.project_path.exists():
            raise FileNotFoundError(f"Le projet {self.project_name} n'existe pas.")
        
        # Si pas d'index existant, faire une construction complète
        if not self.db_path.exists():
            print("   ℹ️  Pas d'index existant, construction complète...")
            return self.build_full_index()
        
        # Détecter les changements
        new_files, modified_files, deleted_files = self.tracker.detect_changes(
            self.project_path,
            extensions=[".txt", ".md", ".pdf", ".docx"]
        )
        
        total_changes = len(new_files) + len(modified_files) + len(deleted_files)
        
        if total_changes == 0:
            print("   ✅ Aucun changement détecté, index à jour!")
            return {
                "status": "up_to_date",
                "new": 0,
                "modified": 0,
                "deleted": 0
            }
        
        print(f"\n📊 Changements détectés:")
        print(f"   ➕ {len(new_files)} nouveaux fichiers")
        print(f"   📝 {len(modified_files)} fichiers modifiés")
        print(f"   🗑️  {len(deleted_files)} fichiers supprimés")
        
        # Récupérer la base vectorielle existante
        vectordb = self._get_vectordb()
        collection = vectordb._collection
        
        # Traiter les suppressions
        if deleted_files:
            print(f"\n🗑️  Suppression des chunks obsolètes...")
            for rel_path in deleted_files:
                # Supprimer les chunks associés
                self._delete_chunks_for_file(collection, rel_path)
                self.tracker.remove_file(rel_path)
        
        # Traiter les modifications (supprimer puis réajouter)
        if modified_files:
            print(f"\n📝 Mise à jour des fichiers modifiés...")
            for file_path in modified_files:
                rel_path = str(file_path.relative_to(self.project_path))
                self._delete_chunks_for_file(collection, rel_path)
        
        # Charger et indexer les nouveaux/modifiés
        files_to_index = new_files + modified_files
        if files_to_index:
            print(f"\n🔮 Indexation de {len(files_to_index)} fichiers...")
            docs, chunks = self._index_files(files_to_index, vectordb)
            self._update_tracker_from_docs(docs, chunks)
        
        stats = {
            "status": "updated",
            "new": len(new_files),
            "modified": len(modified_files),
            "deleted": len(deleted_files)
        }
        
        print(f"\n✅ Index mis à jour avec succès!")
        
        return stats
    
    def _delete_chunks_for_file(self, collection, relative_path: str):
        """Supprime tous les chunks associés à un fichier."""
        try:
            # Récupérer les IDs des documents avec ce chemin
            results = collection.get(
                where={"relative_path": relative_path},
                include=[]
            )
            
            if results and results.get("ids"):
                collection.delete(ids=results["ids"])
                print(f"   ✓ Supprimé {len(results['ids'])} chunks de {relative_path}")
        except Exception as e:
            print(f"   ⚠️  Erreur suppression {relative_path}: {e}")
    
    def _index_files(
        self,
        files: List[Path],
        vectordb: Chroma
    ) -> Tuple[List[Document], List[Document]]:
        """
        Indexe une liste de fichiers.
        
        Returns:
            Tuple (documents originaux, chunks)
        """
        from src.loaders import TextLoader
        
        all_docs = []
        all_chunks = []
        
        for file_path in files:
            try:
                # Charger le document
                loader = TextLoader(str(file_path), encoding="utf-8")
                docs = loader.load()
                
                # Ajouter les métadonnées
                for doc in docs:
                    doc.metadata["relative_path"] = str(
                        file_path.relative_to(self.project_path)
                    )
                    doc.metadata["file_name"] = file_path.name
                
                all_docs.extend(docs)
                
                # Découper en chunks
                chunks = split_documents(
                    docs,
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap
                )
                all_chunks.extend(chunks)
                
                # Ajouter à la base vectorielle
                if chunks:
                    vectordb.add_documents(chunks)
                
                print(f"   ✓ {file_path.name}: {len(chunks)} chunks")
                
            except Exception as e:
                print(f"   ✗ Erreur {file_path.name}: {e}")
        
        return all_docs, all_chunks
    
    def _update_tracker_from_docs(
        self,
        docs: List[Document],
        chunks: List[Document]
    ):
        """Met à jour le tracker avec les documents indexés."""
        # Compter les chunks par fichier
        chunk_counts = {}
        for chunk in chunks:
            rel_path = chunk.metadata.get("relative_path", "")
            chunk_counts[rel_path] = chunk_counts.get(rel_path, 0) + 1
        
        # Mettre à jour le tracker
        for doc in docs:
            rel_path = doc.metadata.get("relative_path", "")
            if rel_path:
                file_path = self.project_path / rel_path
                if file_path.exists():
                    self.tracker.update_file(
                        file_path=rel_path,
                        file_hash=get_file_hash(file_path),
                        size=file_path.stat().st_size,
                        modified=file_path.stat().st_mtime,
                        chunk_count=chunk_counts.get(rel_path, 0)
                    )
    
    def get_index_stats(self) -> dict:
        """Retourne les statistiques de l'index."""
        stats = self.tracker.get_stats()
        stats["project"] = self.project_name
        stats["chunk_size"] = self.tracker.get_metadata("chunk_size")
        stats["chunk_overlap"] = self.tracker.get_metadata("chunk_overlap")
        return stats


def build_index(project_name: str, chunk_size: int = 1000, chunk_overlap: int = 150):
    """
    Construit l'index vectoriel pour un projet (reconstruction complète).
    
    Args:
        project_name: Nom du projet (dossier dans data/)
        chunk_size: Taille des chunks
        chunk_overlap: Chevauchement entre chunks
    """
    indexer = ProjectIndexer(
        project_name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return indexer.build_full_index()


def update_index(project_name: str):
    """
    Met à jour un index existant (incrémental).
    
    Args:
        project_name: Nom du projet
    """
    indexer = ProjectIndexer(project_name)
    return indexer.build_incremental_index()


def get_index_stats(project_name: str) -> dict:
    """
    Retourne les statistiques d'un index.
    
    Args:
        project_name: Nom du projet
        
    Returns:
        Dict avec les statistiques
    """
    indexer = ProjectIndexer(project_name)
    return indexer.get_index_stats()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.indexer <nom_projet> [--full|--update|--stats]")
        print("Exemples:")
        print("  python -m src.indexer anomalie2084          # Incrémental")
        print("  python -m src.indexer anomalie2084 --full   # Reconstruction complète")
        print("  python -m src.indexer anomalie2084 --stats  # Afficher les stats")
        sys.exit(1)
    
    project = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "--update"
    
    try:
        if mode == "--full":
            build_index(project)
        elif mode == "--stats":
            stats = get_index_stats(project)
            print(f"\n📊 Statistiques de l'index '{project}':")
            print(f"   Fichiers: {stats.get('file_count', 0)}")
            print(f"   Chunks: {stats.get('total_chunks', 0)}")
            print(f"   Taille totale: {stats.get('total_size', 0) / 1024:.1f} KB")
            print(f"   Chunk size: {stats.get('chunk_size', 'N/A')}")
            print(f"   Dernière indexation: {stats.get('last_indexed', 'N/A')}")
        else:  # --update par défaut
            update_index(project)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
