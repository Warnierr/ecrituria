"""
Agent autonome qui détecte et sauvegarde automatiquement le contenu généré par l'IA.

Détecte les patterns dans la question utilisateur pour auto-sauvegarder :
- "sauvegarde dans notes/idees.md : ..."
- "ajoute à chapitres/chapitre_03.md : ..."
- "écris dans personnages/alex.md : ..."
"""
import re
import requests
from typing import Dict, Optional, Tuple


class AgentSaver:
    """Agent qui analyse les questions et auto-sauvegarde le contenu."""
    
    # Patterns pour détecter l'intention de sauvegarde
    SAVE_PATTERNS = [
        # "sauvegarde dans fichier.md : contenu"
        r"(?:sauvegarde|enregistre|save)\s+(?:dans|in|à|to)\s+([^\s:]+\.md)\s*[:\-]\s*(.+)",
        
        # "ajoute à fichier.md : contenu"
        r"(?:ajoute|add|append)\s+(?:dans|in|à|to)\s+([^\s:]+\.md)\s*[:\-]\s*(.+)",
        
        # "écris dans fichier.md : contenu"
        r"(?:écris|write|crée|create)\s+(?:dans|in|un fichier)\s+([^\s:]+\.md)\s*[:\-]\s*(.+)",
        
        # "utilise append pour fichier.md"
        r"(?:utilise|use)\s+(?:append|rewrite|create)\s+(?:pour|for)\s+([^\s:]+\.md)",
    ]
    
    def __init__(self, project: str, api_base_url: str = "http://localhost:8000"):
        self.project = project
        self.api_base_url = api_base_url
    
    def detect_save_intent(self, user_question: str) -> Optional[Tuple[str, str, str]]:
        """
        Détecte si l'utilisateur veut sauvegarder du contenu.
        
        Returns:
            Tuple (file_path, explicit_content, action) ou None
            - file_path: chemin du fichier (ex: "notes/idees.md")
            - explicit_content: contenu explicite dans la question (peut être None)
            - action: "append", "create", ou "rewrite"
        """
        for pattern in self.SAVE_PATTERNS:
            match = re.search(pattern, user_question, re.IGNORECASE | re.DOTALL)
            if match:
                file_path = match.group(1)
                explicit_content = match.group(2) if len(match.groups()) > 1 else None
                
                # Détecter l'action
                action = "append"  # Par défaut
                if re.search(r'\b(?:crée|create|nouveau|new)\b', user_question, re.IGNORECASE):
                    action = "create"
                elif re.search(r'\b(?:réécris|rewrite|remplace|replace)\b', user_question, re.IGNORECASE):
                    action = "rewrite"
                
                return (file_path, explicit_content, action)
        
        return None
    
    def auto_save(self, file_path: str, content: str, action: str = "append") -> Dict:
        """
        Sauvegarde automatiquement le contenu via l'API Writer Mode.
        
        Args:
            file_path: Chemin du fichier (ex: "notes/idees.md")
            content: Contenu à sauvegarder
            action: "append", "create", ou "rewrite"
        
        Returns:
            Dict avec status et infos
        """
        try:
            url = f"{self.api_base_url}/api/ai-write/{self.project}"
            
            payload = {
                "action": action,
                "file_path": file_path,
                "instruction": f"Ajoute exactement ce contenu sans le modifier :\n\n{content}",
                "preview_only": False,
                "context_files": []
            }
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "auto_saved": True,
                    "file_path": result.get("file_path"),
                    "mode": result.get("mode"),
                    "backup_created": result.get("backup_created", False)
                }
            else:
                return {
                    "success": False,
                    "auto_saved": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "auto_saved": False,
                "error": str(e)
            }
    
    def analyze_and_save(self, user_question: str, ai_response: str) -> Dict:
        """
        Analyse la question et sauvegarde automatiquement si détection.
        
        Args:
            user_question: Question de l'utilisateur
            ai_response: Réponse générée par l'IA
        
        Returns:
            Dict avec informations sur la sauvegarde
        """
        intent = self.detect_save_intent(user_question)
        
        if not intent:
            return {"auto_saved": False, "reason": "no_save_intent"}
        
        file_path, explicit_content, action = intent
        
        # Si contenu explicite dans la question, l'utiliser
        # Sinon utiliser la réponse de l'IA
        content_to_save = explicit_content if explicit_content else ai_response
        
        print(f"[AGENT] 🤖 Auto-save détecté !")
        print(f"[AGENT]    Fichier: {file_path}")
        print(f"[AGENT]    Action: {action}")
        print(f"[AGENT]    Contenu: {len(content_to_save)} caractères")
        
        result = self.auto_save(file_path, content_to_save, action)
        
        if result["success"]:
            print(f"[AGENT] ✅ Auto-sauvegardé avec succès !")
        else:
            print(f"[AGENT] ❌ Échec: {result.get('error')}")
        
        return result


# Test standalone
if __name__ == "__main__":
    agent = AgentSaver("anomalie2084")
    
    # Test 1: Détection simple
    test1 = "Sauvegarde dans notes/test.md : Ceci est un test"
    intent = agent.detect_save_intent(test1)
    print(f"Test 1: {intent}")
    
    # Test 2: Avec append
    test2 = "Ajoute à notes/idees.md : Une nouvelle idée sur la mémoire"
    intent = agent.detect_save_intent(test2)
    print(f"Test 2: {intent}")
    
    # Test 3: Sans intention
    test3 = "Qui est Alex Chen ?"
    intent = agent.detect_save_intent(test3)
    print(f"Test 3: {intent}")
