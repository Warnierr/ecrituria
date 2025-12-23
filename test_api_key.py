"""
Test direct de la clé API OpenRouter
"""
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Charger .env
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")

print("="*70)
print("🔑 TEST DE LA CLÉ API OPENROUTER")
print("="*70)
print(f"\nClé trouvée: {api_key[:20]}...{api_key[-10:] if api_key else 'AUCUNE'}")
print(f"Longueur: {len(api_key) if api_key else 0} caractères")

if not api_key:
    print("\n❌ ERREUR: Aucune clé API trouvée!")
    print(f"   Cherché dans: {ENV_PATH}")
    exit(1)

# Test 1: Vérifier le format
print("\n📋 Test 1: Format de la clé")
if api_key.startswith("sk-or-v1-"):
    print("   ✅ Format OpenRouter correct (sk-or-v1-...)")
else:
    print(f"   ⚠️  Format inattendu: commence par '{api_key[:10]}'")

# Test 2: Appel API simple
print("\n🌐 Test 2: Appel à l'API OpenRouter...")
try:
    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/fiction-assistant",
        "X-Title": "Fiction Assistant Test"
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ API accessible - Clé valide!")
        data = response.json()
        if 'data' in data:
            print(f"   Nombre de modèles disponibles: {len(data['data'])}")
    elif response.status_code == 401:
        print("   ❌ ERREUR 401: Clé API INVALIDE ou EXPIRÉE")
        print(f"   Réponse: {response.text[:200]}")
        print("\n🔧 SOLUTION:")
        print("   1. Allez sur https://openrouter.ai/keys")
        print("   2. Vérifiez que votre clé est active")
        print("   3. Vérifiez vos crédits (il faut > $0)")
        print("   4. Si nécessaire, créez une NOUVELLE clé")
        print("   5. Mettez à jour le fichier .env avec la nouvelle clé")
    elif response.status_code == 429:
        print("   ⚠️  ERREUR 429: Quota dépassé ou rate limit")
    else:
        print(f"   ⚠️  Code inattendu: {response.status_code}")
        print(f"   Réponse: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("   ❌ Timeout: L'API ne répond pas")
except requests.exceptions.ConnectionError:
    print("   ❌ Erreur de connexion: Vérifiez votre internet")
except Exception as e:
    print(f"   ❌ Erreur: {type(e).__name__}: {e}")

# Test 3: Test d'embedding simple
print("\n🧮 Test 3: Test d'embedding...")
try:
    url = "https://openrouter.ai/api/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/fiction-assistant",
        "X-Title": "Fiction Assistant Test"
    }
    payload = {
        "model": "text-embedding-3-small",
        "input": "Test"
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Embeddings fonctionnent!")
    elif response.status_code == 401:
        print("   ❌ ERREUR 401: Authentification échouée")
    else:
        print(f"   ⚠️  Erreur: {response.status_code}")
        print(f"   Réponse: {response.text[:300]}")
        
except Exception as e:
    print(f"   ❌ Erreur: {type(e).__name__}: {e}")

print("\n" + "="*70)
print("FIN DU TEST")
print("="*70)
