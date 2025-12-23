"""
Demonstration du systeme RAG pour l'utilisateur
"""
from src.rag import ask, get_relevant_passages

print("="*70)
print("DEMONSTRATION DU SYSTEME RAG - ANOMALIE 2084")
print("="*70)

# Test 1: Question sur les Dockers (nouveau contenu)
print("\n" + "="*70)
print("TEST 1: Les Dockers de Lutéris")
print("-"*70)
print("Question: Parle-moi des Dockers de Lutéris. Qu'est-ce que c'est?")
print("\nReponse du RAG:")
try:
    result = ask('anomalie2084', 'Parle-moi des Dockers de Lutéris. Qu\'est-ce que c\'est et comment sont-ils liés à Lutéris?', model='openai/gpt-4o-mini', use_reranking=False)
    print(result)
except Exception as e:
    print(f"ERREUR: {e}")

# Test 2: Question sur la Couronne
print("\n" + "="*70)
print("TEST 2: La Couronne de Lutéris")
print("-"*70)
print("Question: Qu'est-ce que la Couronne de Lutéris?")
print("\nReponse du RAG:")
try:
    result = ask('anomalie2084', 'Qu\'est-ce que la Couronne de Lutéris et quels sont les royaumes qui l\'entourent?', model='openai/gpt-4o-mini', use_reranking=False)
    print(result)
except Exception as e:
    print(f"ERREUR: {e}")

# Test 3: Recherche de passages
print("\n" + "="*70)
print("TEST 3: Recherche de passages sur le protagoniste")
print("-"*70)
print("Recherche: 'protagoniste' et 'Dockers'")
try:
    passages = get_relevant_passages('anomalie2084', 'protagoniste Dockers', k=2, use_reranking=False)
    print(f"\n{len(passages)} passages trouves:\n")
    for i, doc in enumerate(passages, 1):
        source_file = doc.metadata.get('relative_path', 'source inconnue')
        preview = doc.page_content[:200].replace('\n', ' ')
        print(f"{i}. FICHIER: {source_file}")
        print(f"   {preview}...\n")
except Exception as e:
    print(f"ERREUR: {e}")

# Test 4: Question sur la Bague
print("\n" + "="*70)
print("TEST 4: La Bague de Luméris")
print("-"*70)
print("Question: Qu'est-ce que la Bague de Luméris?")
print("\nReponse du RAG:")
try:
    result = ask('anomalie2084', 'Qu\'est-ce que la Bague de Luméris et pourquoi le protagoniste la cherche?', model='openai/gpt-4o-mini', use_reranking=False)
    print(result)
except Exception as e:
    print(f"ERREUR: {e}")

print("\n" + "="*70)
print("DEMONSTRATION TERMINEE")
print("="*70)
print("\nPour utiliser le systeme interactivement:")
print("   python -m src.cli anomalie2084")
print("   ou")
print("   start-openrouter.bat anomalie2084")
print("="*70)
