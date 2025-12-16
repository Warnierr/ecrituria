"""
Gestion des hash de fichiers pour l'indexation incrémentale.
Phase 1.3 du plan d'évolution Ecrituria v2.0
"""
import hashlib
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileInfo:
    """Information sur un fichier indexé."""
    path: str
    hash: str
    size: int
    modified: float
    indexed_at: str
    chunk_count: int = 0


def get_file_hash(file_path: Path) -> str:
    """
    Calcule le hash MD5 d'un fichier.
    
    Args:
        file_path: Chemin vers le fichier
        
    Returns:
        Hash MD5 hexadécimal
    """
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


class FileHashTracker:
    """
    Tracker pour suivre les fichiers indexés et détecter les changements.
    Utilise SQLite pour la persistance.
    """
    
    def __init__(self, project_name: str, db_dir: Path = None):
        """
        Initialise le tracker.
        
        Args:
            project_name: Nom du projet
            db_dir: Répertoire pour la base SQLite (défaut: db/)
        """
        self.project_name = project_name
        self.db_dir = db_dir or Path("db")
        self.db_path = self.db_dir / project_name / "file_index.db"
        
        # Créer le répertoire si nécessaire
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialiser la base de données
        self._init_db()
    
    def _init_db(self):
        """Crée les tables si elles n'existent pas."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    hash TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    modified REAL NOT NULL,
                    indexed_at TEXT NOT NULL,
                    chunk_count INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS index_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    def get_file_info(self, file_path: str) -> Optional[FileInfo]:
        """
        Récupère les informations d'un fichier indexé.
        
        Args:
            file_path: Chemin relatif du fichier
            
        Returns:
            FileInfo ou None si non trouvé
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT path, hash, size, modified, indexed_at, chunk_count FROM files WHERE path = ?",
                (file_path,)
            )
            row = cursor.fetchone()
            
            if row:
                return FileInfo(
                    path=row[0],
                    hash=row[1],
                    size=row[2],
                    modified=row[3],
                    indexed_at=row[4],
                    chunk_count=row[5]
                )
        return None
    
    def update_file(self, file_path: str, file_hash: str, size: int, modified: float, chunk_count: int = 0):
        """
        Met à jour ou ajoute un fichier dans le tracker.
        
        Args:
            file_path: Chemin relatif du fichier
            file_hash: Hash MD5 du fichier
            size: Taille en octets
            modified: Timestamp de modification
            chunk_count: Nombre de chunks créés
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO files (path, hash, size, modified, indexed_at, chunk_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                file_path,
                file_hash,
                size,
                modified,
                datetime.now().isoformat(),
                chunk_count
            ))
            conn.commit()
    
    def remove_file(self, file_path: str):
        """
        Supprime un fichier du tracker.
        
        Args:
            file_path: Chemin relatif du fichier
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM files WHERE path = ?", (file_path,))
            conn.commit()
    
    def get_all_files(self) -> Dict[str, FileInfo]:
        """
        Récupère tous les fichiers indexés.
        
        Returns:
            Dict path -> FileInfo
        """
        files = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT path, hash, size, modified, indexed_at, chunk_count FROM files"
            )
            for row in cursor:
                files[row[0]] = FileInfo(
                    path=row[0],
                    hash=row[1],
                    size=row[2],
                    modified=row[3],
                    indexed_at=row[4],
                    chunk_count=row[5]
                )
        return files
    
    def detect_changes(self, project_path: Path, extensions: List[str] = None) -> Tuple[List[Path], List[Path], List[str]]:
        """
        Détecte les fichiers ajoutés, modifiés et supprimés.
        
        Args:
            project_path: Chemin vers le dossier du projet
            extensions: Extensions à surveiller (défaut: .txt, .md)
            
        Returns:
            Tuple (fichiers_nouveaux, fichiers_modifiés, fichiers_supprimés)
        """
        if extensions is None:
            extensions = [".txt", ".md", ".pdf", ".docx"]
        
        # Récupérer l'état actuel de l'index
        indexed_files = self.get_all_files()
        indexed_paths = set(indexed_files.keys())
        
        # Scanner le système de fichiers
        current_paths = set()
        new_files = []
        modified_files = []
        
        for ext in extensions:
            for file_path in project_path.rglob(f"*{ext}"):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(project_path))
                    current_paths.add(rel_path)
                    
                    if rel_path not in indexed_paths:
                        # Nouveau fichier
                        new_files.append(file_path)
                    else:
                        # Vérifier si modifié
                        current_hash = get_file_hash(file_path)
                        if current_hash != indexed_files[rel_path].hash:
                            modified_files.append(file_path)
        
        # Fichiers supprimés
        deleted_files = list(indexed_paths - current_paths)
        
        return new_files, modified_files, deleted_files
    
    def set_metadata(self, key: str, value: any):
        """Stocke une métadonnée d'index."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO index_metadata (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
            conn.commit()
    
    def get_metadata(self, key: str, default: any = None) -> any:
        """Récupère une métadonnée d'index."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM index_metadata WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return default
    
    def get_stats(self) -> dict:
        """
        Retourne des statistiques sur l'index.
        
        Returns:
            Dict avec les statistiques
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as file_count,
                    SUM(size) as total_size,
                    SUM(chunk_count) as total_chunks,
                    MIN(indexed_at) as first_indexed,
                    MAX(indexed_at) as last_indexed
                FROM files
            """)
            row = cursor.fetchone()
            
            return {
                "file_count": row[0] or 0,
                "total_size": row[1] or 0,
                "total_chunks": row[2] or 0,
                "first_indexed": row[3],
                "last_indexed": row[4]
            }
    
    def clear(self):
        """Supprime toutes les données du tracker."""
        # Réinitialise les tables si le fichier SQLite vient d'être recréé
        self._init_db()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM files")
            conn.execute("DELETE FROM index_metadata")
            conn.commit()


# Test du module
if __name__ == "__main__":
    print("\n📊 Test du module file_hash")
    print("=" * 50)
    
    # Créer un tracker de test
    tracker = FileHashTracker("test_project", Path("db"))
    
    # Ajouter quelques fichiers fictifs
    tracker.update_file("test1.md", "abc123", 1024, 1234567890.0, 5)
    tracker.update_file("test2.md", "def456", 2048, 1234567891.0, 10)
    
    # Récupérer les stats
    stats = tracker.get_stats()
    print(f"\n📈 Statistiques:")
    print(f"   Fichiers: {stats['file_count']}")
    print(f"   Taille totale: {stats['total_size']} octets")
    print(f"   Chunks totaux: {stats['total_chunks']}")
    
    # Récupérer un fichier
    info = tracker.get_file_info("test1.md")
    if info:
        print(f"\n📄 Info test1.md:")
        print(f"   Hash: {info.hash}")
        print(f"   Chunks: {info.chunk_count}")
    
    # Nettoyer
    tracker.clear()
    print("\n✅ Test réussi!")

