"""
Test de modification de personnage
"""
from src.rag import ask

print("="*70)
print("🎨 TEST: Modification et variation de personnages")
print("="*70)

# Test 1: Proposer une variation de nom
print("\n📝 TEST 1: Variation du nom d'Alex")
print("-" * 70)
question = "Si Alex Chen devait avoir un nom de code dans la résistance, lequel serait cohérent avec son personnage ?"
print(f"Question: {question}")
result = ask('anomalie2084', question, model='openai/gpt-4o-mini')
print(f"\n✨ Réponse:\n{result}")

# Test 2: Proposer une description alternative
print("\n" + "="*70)
print("📝 TEST 2: Variation de l'apparence")
print("-" * 70)
question = "Comment décrirais-tu Alex Chen s'il avait grandi en Zone Gamma au lieu de Zone Beta ?"
print(f"Question: {question}")
result = ask('anomalie2084', question, model='openai/gpt-4o-mini')
print(f"\n✨ Réponse:\n{result}")

# Test 3: Créer un personnage similaire
print("\n" + "="*70)
print("📝 TEST 3: Créer un personnage variant")
print("-" * 70)
question = "Crée un personnage similaire à Alex mais qui serait son rival: même type de pouvoirs mais personnalité opposée. Reste cohérent avec l'univers."
print(f"Question: {question}")
result = ask('anomalie2084', question, model='openai/gpt-4o-mini', show_sources=True)
print(f"\n✨ Réponse:\n{result['answer']}")
print(f"\n📚 Basé sur {len(result['sources'])} passages de l'univers")

# Test 4: Modifier une relation
print("\n" + "="*70)
print("📝 TEST 4: Modifier une relation entre personnages")
print("-" * 70)
question = "Et si Maya était la sœur d'Alex au lieu d'être son amie ? Comment cela changerait leur dynamique ?"
print(f"Question: {question}")
result = ask('anomalie2084', question, model='openai/gpt-4o-mini')
print(f"\n✨ Réponse:\n{result}")

print("\n" + "="*70)
print("✅ TESTS DE VARIATION TERMINÉS")
print("="*70)

