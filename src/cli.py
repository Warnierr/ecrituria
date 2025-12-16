"""
Interface en ligne de commande pour l'assistant fiction RAG.
"""
import sys
from pathlib import Path
from src.rag import ask, get_relevant_passages


def print_banner(project_name: str):
    """Affiche la bannière de bienvenue."""
    print("\n" + "="*60)
    print("✨ ASSISTANT FICTION RAG ✨")
    print("="*60)
    print(f"📖 Projet actif: {project_name}")
    print("="*60)
    print("\nCommandes disponibles:")
    print("  • Posez une question directement")
    print("  • /sources <question> - Afficher les passages sources")
    print("  • /search <mots-clés> - Rechercher dans l'univers")
    print("  • /help - Afficher l'aide")
    print("  • /quit ou /exit - Quitter")
    print("\n" + "-"*60 + "\n")


def print_help():
    """Affiche l'aide."""
    print("\n📚 GUIDE D'UTILISATION")
    print("-" * 60)
    print("""
Exemples de questions que vous pouvez poser:

🔍 Recherche d'informations:
  • "Quelle est la relation entre Alex et Maya?"
  • "Résume-moi l'arc narratif de la saison 1"
  • "Quels sont les points clés de l'univers?"

💡 Génération créative:
  • "Propose 3 idées de scènes pour le chapitre suivant"
  • "Continue ce passage: [votre texte]"
  • "Imagine un dialogue entre X et Y sur le thème de..."

✍️ Aide à l'écriture:
  • "Comment décrire cette scène en restant cohérent?"
  • "Quels détails manquent dans ma description de..."
  • "Suggère des améliorations pour ce passage"

🔧 Commandes spéciales:
  • /sources <question> - Voir les passages utilisés pour répondre
  • /search <mots-clés> - Chercher dans vos documents
    """)
    print("-" * 60 + "\n")


def handle_command(command: str, project_name: str):
    """
    Gère les commandes spéciales.
    
    Returns:
        True si c'est une commande, False sinon
    """
    if not command.startswith("/"):
        return False
    
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    
    if cmd in ["/quit", "/exit"]:
        print("\n👋 Au revoir ! Bonne écriture !\n")
        sys.exit(0)
    
    elif cmd == "/help":
        print_help()
        return True
    
    elif cmd == "/sources":
        if len(parts) < 2:
            print("❌ Usage: /sources <votre question>")
            return True
        
        question = parts[1]
        print(f"\n🔍 Recherche des sources pour: '{question}'...")
        
        try:
            result = ask(project_name, question, show_sources=True)
            print(f"\n💬 Réponse:\n{result['answer']}\n")
            print("📚 Sources utilisées:")
            print("-" * 60)
            for i, doc in enumerate(result['sources'], 1):
                source = doc.metadata.get('relative_path', 'source inconnue')
                content = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                print(f"\n{i}. {source}")
                print(f"   {content}\n")
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        return True
    
    elif cmd == "/search":
        if len(parts) < 2:
            print("❌ Usage: /search <mots-clés>")
            return True
        
        query = parts[1]
        print(f"\n🔍 Recherche de: '{query}'...\n")
        
        try:
            docs = get_relevant_passages(project_name, query, k=5)
            if not docs:
                print("Aucun résultat trouvé.")
            else:
                print(f"📊 {len(docs)} passages trouvés:\n")
                for i, doc in enumerate(docs, 1):
                    source = doc.metadata.get('relative_path', 'source inconnue')
                    content = doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                    print(f"{i}. 📄 {source}")
                    print(f"   {content}")
                    print("-" * 60)
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        return True
    
    else:
        print(f"❌ Commande inconnue: {cmd}")
        print("   Tapez /help pour voir les commandes disponibles")
        return True


def chat_loop(project_name: str):
    """
    Boucle principale de chat.
    
    Args:
        project_name: Nom du projet à charger
    """
    # Vérifier que le projet existe
    db_path = Path("db") / project_name
    if not db_path.exists():
        print(f"\n❌ L'index pour le projet '{project_name}' n'existe pas.")
        print(f"   Lancez d'abord: python -m src.indexer {project_name}\n")
        sys.exit(1)
    
    print_banner(project_name)
    
    while True:
        try:
            question = input("💭 Vous: ").strip()
            
            if not question:
                continue
            
            # Gérer les commandes spéciales
            if handle_command(question, project_name):
                continue
            
            # Poser la question au RAG
            print("\n🤔 Réflexion...\n")
            try:
                answer = ask(project_name, question)
                print(f"✨ Assistant: {answer}\n")
            except Exception as e:
                print(f"❌ Erreur: {e}\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir ! Bonne écriture !\n")
            break
        except EOFError:
            print("\n\n👋 Au revoir ! Bonne écriture !\n")
            break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python -m src.cli <nom_projet>")
        print("Exemple: python -m src.cli anomalie2084\n")
        sys.exit(1)
    
    project = sys.argv[1]
    chat_loop(project)

