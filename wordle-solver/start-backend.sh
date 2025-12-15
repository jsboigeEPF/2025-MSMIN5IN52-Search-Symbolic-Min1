#!/bin/bash

# Script de démarrage du backend Wordle Solver
# Usage: ./start-backend.sh

set -e  # Arrêter en cas d'erreur

echo "🚀 Démarrage du backend Wordle Solver..."

# Se déplacer dans le répertoire backend
cd "$(dirname "$0")/backend"

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
echo "✅ Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer les dépendances si nécessaire
echo "📥 Vérification des dépendances..."
if [ -f "requirements.txt" ]; then
    pip3 install -q -r requirements.txt
fi
if [ -f "../requirements.txt" ]; then
    pip3 install -q -r ../requirements.txt
fi

# Démarrer le backend
echo "🎯 Démarrage du serveur backend..."
python3 main.py
