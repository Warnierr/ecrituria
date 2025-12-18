# Écrituria v2.0 - Dockerfile
# Image Python officielle avec support multi-architectures
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Warnierr"
LABEL description="Écrituria - Assistant d'écriture IA avec RAG, GraphRAG et Agents"
LABEL version="2.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copier le code source
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p data db logs

# Exposer le port 8000 (FastAPI)
EXPOSE 8000

# Commande par défaut (peut être surchargée par docker-compose)
CMD ["python", "-m", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]

