"""
Diagnostic de performance pour Ecrituria
Identifie les sources de latence dans le pipeline RAG
"""
import time
from typing import Dict, Any
from pathlib import Path
import sys


def measure_time(func, *args, **kwargs):
    """Mesure le temps d'exécution d'une fonction"""
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    return result, elapsed


def diagnose_performance(project: str = "anomalie2084", query: str = "Qui est Alex Chen?"):
    """
    Diagnostique complet des performances du système RAG.
    
    Mesure:
    - Temps de chargement des index
    - Temps de recherche (vectorielle, BM25, hybride)
    - Temps de reranking
    - Temps LLM
    - Temps total
    """
    print("\n" + "="*70)
    print(f"🔍 DIAGNOSTIC DE PERFORMANCE - {project}")
    print("="*70)
    print(f"\nQuery: '{query}'")
    print()
    
    results = {}
    
    # 1. Test index loading
    print("📦 1. Chargement de l'index...")
    try:
        from langchain_community.vectorstores import Chroma
        from langchain_openai import OpenAIEmbeddings
        
        db_path = Path("db") / project
        
        def load_index():
            embeddings = OpenAIEmbeddings(
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/fiction-assistant",
                    "X-Title": "Fiction Assistant"
                }
            )
            return Chroma(
                embedding_function=embeddings,
                persist_directory=str(db_path),
                collection_name=project
            )
        
        vectordb, load_time = measure_time(load_index)
        results['index_load'] = load_time
        print(f"   ✓ Temps: {load_time:.3f}s")
        
    except Exception as e:
        print(f"   ✗ Erreur: {e}")
        return
    
    # 2. Test retrieval vectoriel pur
    print("\n🔍 2. Recherche vectorielle pure...")
    try:
        _, vector_time = measure_time(vectordb.similarity_search, query, k=5)
        results['vector_search'] = vector_time
        print(f"   ✓ Temps: {vector_time:.3f}s")
    except Exception as e:
        print(f"   ✗ Erreur: {e}")
    
    # 3. Test hybrid search
    print("\n🎯 3. Recherche hybride (BM25 + Vector)...")
    try:
        from src.hybrid_search import HybridSearcher
        
        searcher = HybridSearcher(project, use_openrouter=True)
        docs, hybrid_time = measure_time(searcher.search, query, k=5)
        results['hybrid_search'] = hybrid_time
        results['hybrid_overhead'] = hybrid_time - results.get('vector_search', 0)
        print(f"   ✓ Temps: {hybrid_time:.3f}s")
        print(f"   → Overhead vs vectoriel: +{results['hybrid_overhead']:.3f}s")
    except Exception as e:
        print(f"   ✗ Erreur: {e}")
        docs = vectordb.similarity_search(query, k=15)  # Fallback
    
    # 4. Test reranking
    print("\n⚡ 4. Reranking (Cross-Encoder)...")
    try:
        from src.reranker import Reranker
        
        reranker = Reranker(model_name="fast")
        
        # Premier appel (chargement du modèle)
        _, rerank_cold = measure_time(reranker.rerank, query, docs, top_k=5)
        results['rerank_cold_start'] = rerank_cold
        print(f"   ✓ Cold start (1er appel): {rerank_cold:.3f}s")
        
        # Appels suivants (modèle en cache)
        _, rerank_warm = measure_time(reranker.rerank, query, docs, top_k=5)
        results['rerank_warm'] = rerank_warm
        print(f"   ✓ Warm (appels suivants): {rerank_warm:.3f}s")
        print(f"   → Overhead modèle: {rerank_cold - rerank_warm:.3f}s")
        
    except Exception as e:
        print(f"   ✗ Erreur: {e}")
    
    # 5. Test LLM
    print("\n🤖 5. Génération LLM...")
    try:
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model="openai/gpt-4o-mini-2024-07-18",
            temperature=0.7,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/fiction-assistant",
                "X-Title": "Fiction Assistant"
            }
        )
        
        prompt = f"Réponds en 2 phrases: {query}"
        
        # Premier appel
        _, llm_time = measure_time(lambda: llm.invoke(prompt))
        results['llm_generation'] = llm_time
        print(f"   ✓ Temps génération: {llm_time:.3f}s")
        
    except Exception as e:
        print(f"   ✗ Erreur: {e}")
    
    # 6. Test pipeline complet
    print("\n🚀 6. Pipeline complet (hybrid + rerank + LLM)...")
    try:
        from src.rag import ask
        
        _, total_warm = measure_time(
            ask,
            project,
            query,
            use_hybrid=True,
            use_reranking=True,
            show_sources=False
        )
        results['total_pipeline_warm'] = total_warm
        print(f"   ✓ Temps total (warm): {total_warm:.3f}s")
        
    except Exception as e:
        print(f"   ✗ Erreur: {e}")
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES PERFORMANCES")
    print("="*70)
    
    if results:
        print("\n⏱️  Temps par composant:")
        
        # Ordre logique
        order = [
            ('index_load', "Chargement index"),
            ('vector_search', "Recherche vectorielle"),
            ('hybrid_search', "Recherche hybride"),
            ('hybrid_overhead', "  └─ Overhead BM25"),
            ('rerank_cold_start', "Reranking (cold)"),
            ('rerank_warm', "Reranking (warm)"),
            ('llm_generation', "Génération LLM"),
            ('total_pipeline_warm', "TOTAL (warm)")
        ]
        
        for key, label in order:
            if key in results:
                time_val = results[key]
                bar_len = int(time_val * 10)
                bar = "█" * min(bar_len, 50)
                
                if 'total' in key.lower():
                    print(f"\n{'─'*70}")
                
                print(f"  {label:25s} {time_val:6.3f}s  {bar}")
        
        # Analyse
        print("\n💡 ANALYSE:")
        
        total = results.get('total_pipeline_warm', 0)
        if total > 0:
            # Pourcentages
            if 'llm_generation' in results:
                llm_pct = (results['llm_generation'] / total) * 100
                print(f"  • LLM représente {llm_pct:.1f}% du temps total")
                
                if llm_pct > 60:
                    print("    └─ 🎯 BOTTLENECK: Le LLM est le principal goulot")
                    print("       → Recommandation: Essayer un modèle plus rapide")
            
            if 'rerank_cold_start' in results:
                rerank_pct = (results['rerank_cold_start'] / total) * 100
                print(f"  • Reranking (cold) représente {rerank_pct:.1f}% du temps")
                
                if rerank_pct > 30:
                    print("    └─ ⚠️  Reranking ajoute latence significative")
                    print("       → Option: Désactiver reranking pour plus de vitesse")
            
            if 'hybrid_overhead' in results and results['hybrid_overhead'] > 0.5:
                print(f"  • Hybrid search ajoute +{results['hybrid_overhead']:.3f}s")
                print("    └─ Considérer désactiver BM25 pour plus de vitesse")
        
        # Recommandations
        print("\n✨ RECOMMANDATIONS:")
        
        if total > 5:
            print("  🚨 Latence élevée (>5s) détectée!")
            print()
            print("  Options pour accélérer:")
            print("   1. Changer de modèle LLM (gpt-4o-mini → claude-instant)")
            print("   2. Désactiver reranking (use_reranking=False)")
            print("   3. Réduire k (nombre de documents: 5 → 3)")
            print("   4. Utiliser Ollama en local (0 latence réseau)")
        elif total > 3:
            print("  ⚠️  Latence moyenne (3-5s)")
            print("   → Acceptable mais optimisable")
        else:
            print("  ✅ Latence bonne (<3s)")
    
    # Modèles recommandés
    print("\n📋 MODÈLES DISPONIBLES (OpenRouter):")
    print()
    print("  Rapides (<2s):             Équilibre (2-4s):         Qualité (4-8s):")
    print("  ─────────────────         ──────────────────         ──────────────")
    print("  • gpt-4o-mini              • claude-3.5-sonnet        • claude-3-opus")
    print("  • llama-3.1-8b             • gpt-4o                   • gpt-4-turbo")
    print("  • mistral-7b               • gemini-pro")
    
    print("\n" + "="*70)
    
    return results


if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "anomalie2084"
    query = sys.argv[2] if len(sys.argv) > 2 else "Qui est Alex Chen?"
    
    diagnose_performance(project, query)
