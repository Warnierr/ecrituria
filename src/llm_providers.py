"""
Gestion multi-provider pour les LLMs et embeddings.
Phase 4 du plan d'évolution Ecrituria v2.0

Supporte:
- OpenRouter (cloud, multi-modèles)
- OpenAI (cloud, direct)
- Ollama (local)
- Embeddings locaux (sentence-transformers)
"""
import os
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()


class ProviderType(Enum):
    """Types de providers disponibles."""
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    OLLAMA = "ollama"
    LOCAL = "local"


@dataclass
class ModelConfig:
    """Configuration d'un modèle."""
    name: str
    provider: ProviderType
    context_length: int = 4096
    supports_functions: bool = False
    description: str = ""


# Modèles préconfigurés
PRESET_MODELS = {
    # OpenRouter
    "gpt-4o-mini": ModelConfig(
        name="openai/gpt-4o-mini",
        provider=ProviderType.OPENROUTER,
        context_length=128000,
        supports_functions=True,
        description="GPT-4o Mini via OpenRouter - Bon rapport qualité/prix"
    ),
    "gpt-4o": ModelConfig(
        name="openai/gpt-4o",
        provider=ProviderType.OPENROUTER,
        context_length=128000,
        supports_functions=True,
        description="GPT-4o via OpenRouter - Plus puissant"
    ),
    "claude-3.5-sonnet": ModelConfig(
        name="anthropic/claude-3.5-sonnet",
        provider=ProviderType.OPENROUTER,
        context_length=200000,
        supports_functions=True,
        description="Claude 3.5 Sonnet - Excellent pour la créativité"
    ),
    "claude-3-opus": ModelConfig(
        name="anthropic/claude-3-opus",
        provider=ProviderType.OPENROUTER,
        context_length=200000,
        supports_functions=True,
        description="Claude 3 Opus - Le meilleur pour l'écriture"
    ),
    
    # Ollama (local)
    "llama3": ModelConfig(
        name="llama3",
        provider=ProviderType.OLLAMA,
        context_length=8192,
        description="Llama 3 8B - Local, rapide"
    ),
    "llama3:70b": ModelConfig(
        name="llama3:70b",
        provider=ProviderType.OLLAMA,
        context_length=8192,
        description="Llama 3 70B - Local, très performant"
    ),
    "mistral": ModelConfig(
        name="mistral",
        provider=ProviderType.OLLAMA,
        context_length=8192,
        description="Mistral 7B - Local, efficace"
    ),
    "mixtral": ModelConfig(
        name="mixtral",
        provider=ProviderType.OLLAMA,
        context_length=32768,
        description="Mixtral 8x7B - Local, MoE performant"
    ),
    "codellama": ModelConfig(
        name="codellama",
        provider=ProviderType.OLLAMA,
        context_length=16384,
        description="Code Llama - Optimisé pour le code"
    ),
}


class LLMProvider(ABC):
    """Interface abstraite pour les providers LLM."""
    
    @abstractmethod
    def create_llm(self, model: str, temperature: float = 0.7, **kwargs):
        """Crée un client LLM."""
        pass
    
    @abstractmethod
    def create_embeddings(self, model: str = None, **kwargs):
        """Crée un client d'embeddings."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Vérifie si le provider est disponible."""
        pass


class OpenRouterProvider(LLMProvider):
    """Provider pour OpenRouter."""
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    
    def create_llm(self, model: str, temperature: float = 0.7, **kwargs):
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            base_url=self.BASE_URL,
            default_headers={
                "HTTP-Referer": "https://github.com/fiction-assistant",
                "X-Title": "Ecrituria Fiction Assistant"
            },
            **kwargs
        )
    
    def create_embeddings(self, model: str = None, **kwargs):
        from langchain_openai import OpenAIEmbeddings
        
        return OpenAIEmbeddings(
            model=model or "text-embedding-3-small",
            base_url=self.BASE_URL,
            default_headers={
                "HTTP-Referer": "https://github.com/fiction-assistant",
                "X-Title": "Ecrituria Fiction Assistant"
            },
            **kwargs
        )
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class OpenAIProvider(LLMProvider):
    """Provider pour OpenAI direct."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
    
    def create_llm(self, model: str, temperature: float = 0.7, **kwargs):
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            **kwargs
        )
    
    def create_embeddings(self, model: str = None, **kwargs):
        from langchain_openai import OpenAIEmbeddings
        
        return OpenAIEmbeddings(
            model=model or "text-embedding-3-small",
            **kwargs
        )
    
    def is_available(self) -> bool:
        return bool(self.api_key) and not os.getenv("OPENROUTER_API_KEY")


class OllamaProvider(LLMProvider):
    """Provider pour Ollama (local)."""
    
    BASE_URL = "http://localhost:11434"
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", self.BASE_URL)
    
    def create_llm(self, model: str, temperature: float = 0.7, **kwargs):
        try:
            from langchain_community.llms import Ollama
            
            return Ollama(
                model=model,
                temperature=temperature,
                base_url=self.base_url,
                **kwargs
            )
        except ImportError:
            # Fallback sur ChatOpenAI avec URL Ollama
            from langchain_openai import ChatOpenAI
            
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                base_url=f"{self.base_url}/v1",
                api_key="ollama",  # Ollama n'a pas besoin de clé
                **kwargs
            )
    
    def create_embeddings(self, model: str = None, **kwargs):
        try:
            from langchain_community.embeddings import OllamaEmbeddings
            
            return OllamaEmbeddings(
                model=model or "nomic-embed-text",
                base_url=self.base_url,
                **kwargs
            )
        except ImportError:
            # Fallback sur embeddings locaux
            return LocalEmbeddingsProvider().create_embeddings()
    
    def is_available(self) -> bool:
        """Vérifie si Ollama est en cours d'exécution."""
        try:
            import urllib.request
            import json
            
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False
    
    def list_models(self) -> List[str]:
        """Liste les modèles disponibles dans Ollama."""
        try:
            import urllib.request
            import json
            
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []


class LocalEmbeddingsProvider(LLMProvider):
    """Provider pour embeddings locaux avec sentence-transformers."""
    
    DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    
    def create_llm(self, model: str, temperature: float = 0.7, **kwargs):
        raise NotImplementedError(
            "LocalEmbeddingsProvider ne supporte pas les LLMs. "
            "Utilisez OllamaProvider pour les LLMs locaux."
        )
    
    def create_embeddings(self, model: str = None, **kwargs):
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
            return HuggingFaceEmbeddings(
                model_name=model or self.DEFAULT_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
                **kwargs
            )
        except ImportError:
            raise ImportError(
                "sentence-transformers n'est pas installé.\n"
                "Installez-le avec: pip install sentence-transformers"
            )
    
    def is_available(self) -> bool:
        try:
            import sentence_transformers
            return True
        except ImportError:
            return False


class LLMFactory:
    """
    Factory pour créer des LLMs et embeddings selon la configuration.
    
    Détecte automatiquement le meilleur provider disponible.
    """
    
    def __init__(self):
        self.providers = {
            ProviderType.OPENROUTER: OpenRouterProvider(),
            ProviderType.OPENAI: OpenAIProvider(),
            ProviderType.OLLAMA: OllamaProvider(),
            ProviderType.LOCAL: LocalEmbeddingsProvider(),
        }
    
    def get_available_providers(self) -> List[ProviderType]:
        """Retourne la liste des providers disponibles."""
        return [
            provider_type
            for provider_type, provider in self.providers.items()
            if provider.is_available()
        ]
    
    def get_best_provider(self, prefer_local: bool = False) -> ProviderType:
        """
        Retourne le meilleur provider disponible.
        
        Args:
            prefer_local: Préférer les providers locaux
            
        Returns:
            Type de provider recommandé
        """
        available = self.get_available_providers()
        
        if not available:
            raise RuntimeError("Aucun provider LLM disponible!")
        
        if prefer_local:
            # Ordre de préférence local
            priority = [
                ProviderType.OLLAMA,
                ProviderType.LOCAL,
                ProviderType.OPENROUTER,
                ProviderType.OPENAI
            ]
        else:
            # Ordre de préférence cloud
            priority = [
                ProviderType.OPENROUTER,
                ProviderType.OPENAI,
                ProviderType.OLLAMA,
                ProviderType.LOCAL
            ]
        
        for provider_type in priority:
            if provider_type in available:
                return provider_type
        
        return available[0]
    
    def create_llm(
        self,
        model: str = None,
        provider: ProviderType = None,
        temperature: float = 0.7,
        prefer_local: bool = False,
        **kwargs
    ):
        """
        Crée un client LLM.
        
        Args:
            model: Nom du modèle (ou preset)
            provider: Type de provider (auto-détecté si None)
            temperature: Température de génération
            prefer_local: Préférer les providers locaux
            **kwargs: Arguments supplémentaires
            
        Returns:
            Client LLM configuré
        """
        # Résoudre le preset si c'est un alias
        if model in PRESET_MODELS:
            preset = PRESET_MODELS[model]
            model = preset.name
            if provider is None:
                provider = preset.provider
        
        # Déterminer le provider
        if provider is None:
            provider = self.get_best_provider(prefer_local=prefer_local)
        
        # Créer le LLM
        llm_provider = self.providers[provider]
        
        if not llm_provider.is_available():
            raise RuntimeError(f"Provider {provider.value} non disponible")
        
        return llm_provider.create_llm(model, temperature=temperature, **kwargs)
    
    def create_embeddings(
        self,
        model: str = None,
        provider: ProviderType = None,
        prefer_local: bool = False,
        **kwargs
    ):
        """
        Crée un client d'embeddings.
        
        Args:
            model: Modèle d'embeddings
            provider: Type de provider
            prefer_local: Préférer les embeddings locaux
            **kwargs: Arguments supplémentaires
            
        Returns:
            Client d'embeddings configuré
        """
        if provider is None:
            if prefer_local and self.providers[ProviderType.LOCAL].is_available():
                provider = ProviderType.LOCAL
            else:
                provider = self.get_best_provider(prefer_local=prefer_local)
        
        emb_provider = self.providers[provider]
        return emb_provider.create_embeddings(model, **kwargs)


# Instance globale de la factory
_factory: Optional[LLMFactory] = None


def get_llm_factory() -> LLMFactory:
    """Retourne l'instance globale de la factory."""
    global _factory
    if _factory is None:
        _factory = LLMFactory()
    return _factory


def create_llm(model: str = "gpt-4o-mini", **kwargs):
    """Fonction utilitaire pour créer un LLM rapidement."""
    return get_llm_factory().create_llm(model, **kwargs)


def create_embeddings(prefer_local: bool = False, **kwargs):
    """Fonction utilitaire pour créer des embeddings rapidement."""
    return get_llm_factory().create_embeddings(prefer_local=prefer_local, **kwargs)


def list_available_models() -> Dict[str, List[str]]:
    """
    Liste tous les modèles disponibles par provider.
    
    Returns:
        Dict provider -> liste de modèles
    """
    factory = get_llm_factory()
    models = {}
    
    for provider_type in factory.get_available_providers():
        if provider_type == ProviderType.OLLAMA:
            ollama = factory.providers[provider_type]
            models["ollama"] = ollama.list_models()
        elif provider_type == ProviderType.OPENROUTER:
            models["openrouter"] = [
                name for name, config in PRESET_MODELS.items()
                if config.provider == ProviderType.OPENROUTER
            ]
        elif provider_type == ProviderType.LOCAL:
            models["local_embeddings"] = [
                "paraphrase-multilingual-MiniLM-L12-v2",
                "all-MiniLM-L6-v2"
            ]
    
    return models


# Test du module
if __name__ == "__main__":
    print("\n🔧 Test du module LLM Providers")
    print("=" * 50)
    
    factory = get_llm_factory()
    
    # Afficher les providers disponibles
    available = factory.get_available_providers()
    print(f"\n📦 Providers disponibles: {[p.value for p in available]}")
    
    # Afficher les modèles
    models = list_available_models()
    print("\n📋 Modèles disponibles:")
    for provider, model_list in models.items():
        print(f"   {provider}:")
        for m in model_list[:5]:  # Limiter l'affichage
            print(f"      - {m}")
        if len(model_list) > 5:
            print(f"      ... et {len(model_list) - 5} autres")
    
    # Test de création
    print("\n🔨 Test de création LLM...")
    try:
        best = factory.get_best_provider()
        print(f"   Meilleur provider: {best.value}")
        
        llm = factory.create_llm("gpt-4o-mini")
        print(f"   ✓ LLM créé: {type(llm).__name__}")
    except Exception as e:
        print(f"   ⚠️ Erreur: {e}")
    
    # Test embeddings locaux
    print("\n🔨 Test d'embeddings locaux...")
    try:
        local_available = factory.providers[ProviderType.LOCAL].is_available()
        print(f"   Embeddings locaux disponibles: {local_available}")
        
        if local_available:
            embeddings = factory.create_embeddings(prefer_local=True)
            print(f"   ✓ Embeddings créés: {type(embeddings).__name__}")
    except Exception as e:
        print(f"   ⚠️ Erreur: {e}")
    
    print("\n✅ Test terminé!")

