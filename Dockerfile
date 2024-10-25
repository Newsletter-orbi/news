# Étape 1 : Construction avec une image légère Python 3.10
FROM python:3.10-slim AS builder

# Mettre à jour apt et installer les dépendances nécessaires pour le build
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    libpq-dev \
    cmake \
    bash \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Mettre à jour pip et installer Cython, numpy, hatchling (souvent nécessaires pour des paquets scientifiques et builds)
RUN pip install --upgrade pip && pip install Cython numpy hatchling

# Créer un répertoire de travail
WORKDIR /app

# Copier uniquement le fichier requirements.txt pour installer les dépendances
COPY requirements.txt /app/

# Installer les dépendances Python depuis le fichier requirements.txt sans isolation de build pour éviter les conflits de version
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

# Étape 2 : Étape de production avec une image Python légère
FROM python:3.10-slim

# Installer le client PostgreSQL et bash, puis nettoyer pour réduire la taille de l'image
RUN apt-get update && apt-get install -y postgresql-client bash \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Créer un répertoire de travail
WORKDIR /app

# Copier les fichiers de l'application dans le conteneur
COPY . /app

# Copier les paquets Python installés depuis l'étape de build
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Mettre à jour le PATH pour inclure les paquets Python installés
ENV PATH="/usr/local/bin:$PATH"

# Exposer le port 8000 (optionnel, selon votre configuration Docker)
EXPOSE 8000

# Lancer l'application avec gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "newsletter_project.wsgi:application"]
