"""
Client Neo4j pour la gestion du graphe de connaissances.
Phase 2.1 du plan d'évolution Ecrituria v2.0

Schéma du graphe:
- Noeuds: Personnage, Lieu, Evenement, Chapitre, Theme, Objet
- Relations: CONNAIT, VIENT_DE, PARTICIPE_A, SE_DEROULE_A, CONTIENT, INCARNE, POSSEDE
"""
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Node:
    """Représente un nœud du graphe."""
    id: str
    label: str  # Type: Personnage, Lieu, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            **self.properties
        }


@dataclass
class Relationship:
    """Représente une relation entre deux nœuds."""
    source_id: str
    target_id: str
    type: str  # CONNAIT, VIENT_DE, etc.
    properties: Dict[str, Any] = field(default_factory=dict)


class Neo4jClient:
    """
    Client pour interagir avec Neo4j.
    
    Supporte:
    - Neo4j Desktop (local)
    - Neo4j Aura (cloud gratuit)
    - Mode simulation (sans Neo4j installé)
    """
    
    # Types de nœuds supportés
    NODE_TYPES = {
        "Personnage": ["nom", "role", "description", "traits", "age"],
        "Lieu": ["nom", "description", "type", "atmosphere"],
        "Evenement": ["nom", "date", "description", "importance"],
        "Chapitre": ["numero", "titre", "resume"],
        "Theme": ["nom", "description"],
        "Objet": ["nom", "description", "proprietaire"]
    }
    
    # Types de relations supportées
    RELATIONSHIP_TYPES = {
        "CONNAIT": {"type_relation": str, "depuis": str},
        "VIENT_DE": {},
        "PARTICIPE_A": {"role": str},
        "SE_DEROULE_A": {},
        "CONTIENT": {},
        "INCARNE": {},
        "POSSEDE": {},
        "ALLIE_DE": {},
        "ENNEMI_DE": {},
        "FAMILLE_DE": {"lien": str}
    }
    
    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None,
        database: str = "neo4j",
        simulation_mode: bool = False
    ):
        """
        Initialise le client Neo4j.
        
        Args:
            uri: URI de connexion (défaut: env NEO4J_URI ou bolt://localhost:7687)
            user: Utilisateur (défaut: env NEO4J_USER ou neo4j)
            password: Mot de passe (défaut: env NEO4J_PASSWORD)
            database: Nom de la base (défaut: neo4j)
            simulation_mode: Si True, simule Neo4j en mémoire
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "")
        self.database = database
        self.simulation_mode = simulation_mode
        
        self._driver = None
        self._memory_store: Dict[str, Any] = {
            "nodes": {},
            "relationships": []
        }
        
        if not simulation_mode:
            self._connect()
    
    def _connect(self):
        """Établit la connexion à Neo4j."""
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Tester la connexion
            with self._driver.session(database=self.database) as session:
                session.run("RETURN 1")
            print(f"✓ Connecté à Neo4j: {self.uri}")
        except ImportError:
            print("⚠️ neo4j non installé, passage en mode simulation")
            self.simulation_mode = True
        except Exception as e:
            print(f"⚠️ Connexion Neo4j échouée: {e}")
            print("   Passage en mode simulation (données en mémoire)")
            self.simulation_mode = True
    
    def close(self):
        """Ferme la connexion."""
        if self._driver:
            self._driver.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ============================================
    # Opérations sur les nœuds
    # ============================================
    
    def create_node(self, node: Node) -> str:
        """
        Crée un nœud dans le graphe.
        
        Args:
            node: Nœud à créer
            
        Returns:
            ID du nœud créé
        """
        if self.simulation_mode:
            self._memory_store["nodes"][node.id] = node.to_dict()
            return node.id
        
        with self._driver.session(database=self.database) as session:
            query = f"""
                MERGE (n:{node.label} {{id: $id}})
                SET n += $properties
                RETURN n.id as id
            """
            result = session.run(
                query,
                id=node.id,
                properties={**node.properties, "id": node.id}
            )
            return result.single()["id"]
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """Récupère un nœud par son ID."""
        if self.simulation_mode:
            return self._memory_store["nodes"].get(node_id)
        
        with self._driver.session(database=self.database) as session:
            result = session.run(
                "MATCH (n {id: $id}) RETURN n, labels(n) as labels",
                id=node_id
            )
            record = result.single()
            if record:
                return {
                    **dict(record["n"]),
                    "label": record["labels"][0] if record["labels"] else None
                }
        return None
    
    def find_nodes(
        self,
        label: str = None,
        properties: Dict[str, Any] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Recherche des nœuds selon des critères.
        
        Args:
            label: Type de nœud (optionnel)
            properties: Propriétés à matcher (optionnel)
            limit: Nombre max de résultats
            
        Returns:
            Liste de nœuds correspondants
        """
        if self.simulation_mode:
            results = []
            for node in self._memory_store["nodes"].values():
                if label and node.get("label") != label:
                    continue
                if properties:
                    match = all(
                        node.get(k) == v
                        for k, v in properties.items()
                    )
                    if not match:
                        continue
                results.append(node)
                if len(results) >= limit:
                    break
            return results
        
        # Construire la requête Cypher
        label_clause = f":{label}" if label else ""
        where_clauses = []
        params = {"limit": limit}
        
        if properties:
            for i, (key, value) in enumerate(properties.items()):
                where_clauses.append(f"n.{key} = $prop_{i}")
                params[f"prop_{i}"] = value
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
            MATCH (n{label_clause})
            WHERE {where_clause}
            RETURN n, labels(n) as labels
            LIMIT $limit
        """
        
        with self._driver.session(database=self.database) as session:
            result = session.run(query, **params)
            return [
                {**dict(r["n"]), "label": r["labels"][0] if r["labels"] else None}
                for r in result
            ]
    
    def delete_node(self, node_id: str):
        """Supprime un nœud et ses relations."""
        if self.simulation_mode:
            self._memory_store["nodes"].pop(node_id, None)
            self._memory_store["relationships"] = [
                r for r in self._memory_store["relationships"]
                if r["source_id"] != node_id and r["target_id"] != node_id
            ]
            return
        
        with self._driver.session(database=self.database) as session:
            session.run(
                "MATCH (n {id: $id}) DETACH DELETE n",
                id=node_id
            )
    
    # ============================================
    # Opérations sur les relations
    # ============================================
    
    def create_relationship(self, rel: Relationship) -> bool:
        """
        Crée une relation entre deux nœuds.
        
        Args:
            rel: Relation à créer
            
        Returns:
            True si créée avec succès
        """
        if self.simulation_mode:
            self._memory_store["relationships"].append({
                "source_id": rel.source_id,
                "target_id": rel.target_id,
                "type": rel.type,
                **rel.properties
            })
            return True
        
        query = f"""
            MATCH (a {{id: $source_id}})
            MATCH (b {{id: $target_id}})
            MERGE (a)-[r:{rel.type}]->(b)
            SET r += $properties
            RETURN type(r) as type
        """
        
        with self._driver.session(database=self.database) as session:
            result = session.run(
                query,
                source_id=rel.source_id,
                target_id=rel.target_id,
                properties=rel.properties
            )
            return result.single() is not None
    
    def get_relationships(
        self,
        node_id: str,
        direction: str = "both",
        rel_type: str = None
    ) -> List[Dict]:
        """
        Récupère les relations d'un nœud.
        
        Args:
            node_id: ID du nœud
            direction: "outgoing", "incoming", ou "both"
            rel_type: Filtrer par type de relation
            
        Returns:
            Liste des relations
        """
        if self.simulation_mode:
            results = []
            for rel in self._memory_store["relationships"]:
                if rel_type and rel["type"] != rel_type:
                    continue
                if direction == "outgoing" and rel["source_id"] == node_id:
                    results.append(rel)
                elif direction == "incoming" and rel["target_id"] == node_id:
                    results.append(rel)
                elif direction == "both" and (
                    rel["source_id"] == node_id or rel["target_id"] == node_id
                ):
                    results.append(rel)
            return results
        
        # Construire la requête Cypher
        rel_clause = f":{rel_type}" if rel_type else ""
        
        if direction == "outgoing":
            pattern = f"(n)-[r{rel_clause}]->(m)"
        elif direction == "incoming":
            pattern = f"(n)<-[r{rel_clause}]-(m)"
        else:
            pattern = f"(n)-[r{rel_clause}]-(m)"
        
        query = f"""
            MATCH {pattern}
            WHERE n.id = $node_id
            RETURN r, type(r) as type, m.id as other_id, m as other_node
        """
        
        with self._driver.session(database=self.database) as session:
            result = session.run(query, node_id=node_id)
            return [
                {
                    **dict(r["r"]),
                    "type": r["type"],
                    "other_id": r["other_id"],
                    "other_node": dict(r["other_node"])
                }
                for r in result
            ]
    
    # ============================================
    # Requêtes de graphe
    # ============================================
    
    def get_node_context(
        self,
        node_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Récupère le contexte d'un nœud (voisinage).
        
        Args:
            node_id: ID du nœud central
            depth: Profondeur de traversée
            
        Returns:
            Dict avec le nœud et ses voisins
        """
        node = self.get_node(node_id)
        if not node:
            return {"node": None, "neighbors": [], "relationships": []}
        
        if self.simulation_mode:
            # Version simplifiée en simulation
            relationships = self.get_relationships(node_id)
            neighbor_ids = set()
            for rel in relationships:
                neighbor_ids.add(rel.get("source_id"))
                neighbor_ids.add(rel.get("target_id"))
            neighbor_ids.discard(node_id)
            
            neighbors = [
                self._memory_store["nodes"].get(nid)
                for nid in neighbor_ids
                if nid in self._memory_store["nodes"]
            ]
            
            return {
                "node": node,
                "neighbors": neighbors,
                "relationships": relationships
            }
        
        # Requête Cypher pour le voisinage
        query = f"""
            MATCH path = (n {{id: $node_id}})-[*1..{depth}]-(m)
            WITH n, collect(distinct m) as neighbors,
                 collect(distinct relationships(path)) as all_rels
            UNWIND all_rels as rels
            UNWIND rels as r
            WITH n, neighbors, collect(distinct r) as relationships
            RETURN n as node, neighbors, relationships
        """
        
        with self._driver.session(database=self.database) as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            
            if record:
                return {
                    "node": dict(record["node"]),
                    "neighbors": [dict(n) for n in record["neighbors"]],
                    "relationships": [
                        {**dict(r), "type": type(r).__name__}
                        for r in record["relationships"]
                    ]
                }
        
        return {"node": node, "neighbors": [], "relationships": []}
    
    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5
    ) -> Optional[List[Dict]]:
        """
        Trouve le chemin le plus court entre deux nœuds.
        
        Args:
            start_id: ID du nœud de départ
            end_id: ID du nœud d'arrivée
            max_depth: Profondeur maximale
            
        Returns:
            Liste des nœuds sur le chemin, ou None si pas de chemin
        """
        if self.simulation_mode:
            # BFS simple en simulation
            from collections import deque
            
            visited = {start_id}
            queue = deque([(start_id, [start_id])])
            
            while queue:
                current, path = queue.popleft()
                
                if current == end_id:
                    return [
                        self._memory_store["nodes"].get(nid)
                        for nid in path
                    ]
                
                if len(path) >= max_depth:
                    continue
                
                for rel in self.get_relationships(current):
                    next_id = (
                        rel["target_id"]
                        if rel["source_id"] == current
                        else rel["source_id"]
                    )
                    if next_id not in visited:
                        visited.add(next_id)
                        queue.append((next_id, path + [next_id]))
            
            return None
        
        query = f"""
            MATCH path = shortestPath(
                (start {{id: $start_id}})-[*..{max_depth}]-(end {{id: $end_id}})
            )
            RETURN [n in nodes(path) | n] as nodes
        """
        
        with self._driver.session(database=self.database) as session:
            result = session.run(query, start_id=start_id, end_id=end_id)
            record = result.single()
            
            if record:
                return [dict(n) for n in record["nodes"]]
        
        return None
    
    # ============================================
    # Utilitaires
    # ============================================
    
    def clear_database(self):
        """Supprime toutes les données (ATTENTION!)."""
        if self.simulation_mode:
            self._memory_store = {"nodes": {}, "relationships": []}
            return
        
        with self._driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
    
    def get_schema(self) -> Dict[str, Any]:
        """Retourne le schéma du graphe."""
        if self.simulation_mode:
            labels = set()
            rel_types = set()
            for node in self._memory_store["nodes"].values():
                labels.add(node.get("label", "Unknown"))
            for rel in self._memory_store["relationships"]:
                rel_types.add(rel.get("type", "Unknown"))
            return {
                "labels": list(labels),
                "relationship_types": list(rel_types)
            }
        
        with self._driver.session(database=self.database) as session:
            labels_result = session.run("CALL db.labels()")
            labels = [r[0] for r in labels_result]
            
            rels_result = session.run("CALL db.relationshipTypes()")
            rel_types = [r[0] for r in rels_result]
            
            return {
                "labels": labels,
                "relationship_types": rel_types
            }
    
    def get_stats(self) -> Dict[str, int]:
        """Retourne des statistiques sur le graphe."""
        if self.simulation_mode:
            return {
                "node_count": len(self._memory_store["nodes"]),
                "relationship_count": len(self._memory_store["relationships"])
            }
        
        with self._driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (n) WITH count(n) as nodes
                MATCH ()-[r]->() WITH nodes, count(r) as rels
                RETURN nodes, rels
            """)
            record = result.single()
            return {
                "node_count": record["nodes"] if record else 0,
                "relationship_count": record["rels"] if record else 0
            }


# Singleton pour la connexion partagée
_client_instance: Optional[Neo4jClient] = None


def get_neo4j_client(force_new: bool = False, **kwargs) -> Neo4jClient:
    """
    Retourne une instance partagée du client Neo4j.
    
    Args:
        force_new: Force la création d'une nouvelle instance
        **kwargs: Arguments passés au constructeur
        
    Returns:
        Instance Neo4jClient
    """
    global _client_instance
    
    if _client_instance is None or force_new:
        _client_instance = Neo4jClient(**kwargs)
    
    return _client_instance


# Test du module
if __name__ == "__main__":
    print("\n🔗 Test du client Neo4j")
    print("=" * 50)
    
    # Utiliser le mode simulation pour le test
    client = Neo4jClient(simulation_mode=True)
    
    # Créer quelques nœuds
    print("\n📝 Création de nœuds...")
    
    alex = Node(
        id="alex_chen",
        label="Personnage",
        properties={
            "nom": "Alex Chen",
            "role": "Protagoniste",
            "description": "Technicien de maintenance du Nexus"
        }
    )
    client.create_node(alex)
    
    maya = Node(
        id="maya",
        label="Personnage",
        properties={
            "nom": "Maya",
            "role": "Alliée",
            "description": "Programmeuse talentueuse"
        }
    )
    client.create_node(maya)
    
    nexus = Node(
        id="nexus",
        label="Lieu",
        properties={
            "nom": "Le Nexus",
            "type": "Infrastructure",
            "description": "Cœur du réseau de données"
        }
    )
    client.create_node(nexus)
    
    # Créer des relations
    print("\n🔗 Création de relations...")
    
    client.create_relationship(Relationship(
        source_id="alex_chen",
        target_id="maya",
        type="CONNAIT",
        properties={"type_relation": "ami", "depuis": "enfance"}
    ))
    
    client.create_relationship(Relationship(
        source_id="alex_chen",
        target_id="nexus",
        type="VIENT_DE",
        properties={}
    ))
    
    # Afficher les stats
    stats = client.get_stats()
    print(f"\n📊 Stats: {stats['node_count']} nœuds, {stats['relationship_count']} relations")
    
    # Récupérer le contexte d'Alex
    context = client.get_node_context("alex_chen")
    print(f"\n👤 Contexte d'Alex Chen:")
    print(f"   Voisins: {len(context['neighbors'])}")
    print(f"   Relations: {len(context['relationships'])}")
    
    # Trouver le chemin entre Maya et Nexus
    path = client.find_path("maya", "nexus")
    if path:
        print(f"\n🛤️  Chemin Maya -> Nexus: {len(path)} nœuds")
    
    print("\n✅ Test réussi!")

