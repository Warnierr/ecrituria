"""
Script de test pour vérifier que le RAG fonctionne correctement
"""
from src.rag import ask, get_relevant_passages

print("="*60)
print("🧪 TEST DE L'ASSISTANT FICTION RAG")
print("="*60)

# Test 1: Question factuelle simple
print("\n📝 TEST 1: Question factuelle simple")
print("-" * 60)
print("Question: Quel âge a Alex Chen ?")
result = ask('anomalie2084', 'Quel âge a Alex Chen ?', model='openai/gpt-4o-mini')
print(f"\n✨ Réponse: {result}")

# Test 2: Question avec sources
print("\n" + "="*60)
print("📝 TEST 2: Question avec affichage des sources")
print("-" * 60)
print("Question: Quelles sont les capacités d'Anomalie d'Alex ?")
result = ask('anomalie2084', 'Quelles sont les capacités d Anomalie d Alex ?', 
             model='openai/gpt-4o-mini', show_sources=True)
print(f"\n✨ Réponse:\n{result['answer']}")
print(f"\n📚 SOURCES UTILISÉES ({len(result['sources'])} passages):")
for i, doc in enumerate(result['sources'], 1):
    source_file = doc.metadata.get('relative_path', 'source inconnue')
    preview = doc.page_content[:200].replace('\n', ' ')
    print(f"\n{i}. 📄 {source_file}")
    print(f"   Extrait: {preview}...")

# Test 3: Recherche directe
print("\n" + "="*60)
print("📝 TEST 3: Recherche de passages pertinents")
print("-" * 60)
print("Recherche: Maya")
passages = get_relevant_passages('anomalie2084', 'Maya', k=3)
print(f"\n🔍 {len(passages)} passages trouvés:")
for i, doc in enumerate(passages, 1):
    source_file = doc.metadata.get('relative_path', 'source inconnue')
    preview = doc.page_content[:150].replace('\n', ' ')
    print(f"\n{i}. 📄 {source_file}")
    print(f"   {preview}...")

# Test 4: Génération créative
print("\n" + "="*60)
print("📝 TEST 4: Génération créative cohérente")
print("-" * 60)
print("Question: Propose un titre de chapitre cohérent avec l'univers")
result = ask('anomalie2084', 'Propose un titre de chapitre 2 qui suit le chapitre 1', 
             model='openai/gpt-4o-mini', show_sources=True)
print(f"\n✨ Réponse: {result['answer']}")
print(f"\n📚 Basé sur {len(result['sources'])} passages de l'univers")

print("\n" + "="*60)
print("✅ TOUS LES TESTS TERMINÉS")
print("="*60)

