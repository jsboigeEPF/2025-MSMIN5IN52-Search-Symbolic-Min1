#!/bin/bash

# Script de démarrage du frontend Wordle Solver
# Usage: ./start-frontend.sh

set -e  # Arrêter en cas d'erreur

echo "🚀 Démarrage du frontend Wordle Solver..."

# Se déplacer dans le répertoire frontend
cd "$(dirname "$0")/frontend"

# Vérifier si node_modules existe
if [ ! -d "node_modules" ]; then
    echo "📦 Installation des dépendances npm..."
    npm install
else
    echo "✅ Dépendances déjà installées"
fi

# Démarrer le serveur de développement
echo "🎯 Démarrage du serveur de développement..."
npm run dev