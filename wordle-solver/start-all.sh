#!/bin/bash

# Script de démarrage complet Wordle Solver
# Lance le backend et le frontend en parallèle
# Usage: ./start-all.sh

set -e

echo "🎮 Démarrage complet de Wordle Solver..."
echo "========================================="

# Obtenir le chemin du script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Fonction pour arrêter proprement les processus
cleanup() {
    echo ""
    echo "🛑 Arrêt des serveurs..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Capturer Ctrl+C pour arrêter proprement
trap cleanup SIGINT SIGTERM

# Démarrer le backend en arrière-plan
echo ""
echo "🔧 Lancement du backend..."
"$SCRIPT_DIR/start-backend.sh" &
BACKEND_PID=$!

# Attendre un peu pour que le backend démarre
sleep 3

# Démarrer le frontend en arrière-plan
echo ""
echo "🎨 Lancement du frontend..."
"$SCRIPT_DIR/start-frontend.sh" &
FRONTEND_PID=$!

echo ""
echo "✨ Les deux serveurs sont en cours de démarrage..."
echo ""
echo "📍 Backend: http://localhost:8000 (PID: $BACKEND_PID)"
echo "📍 Frontend: http://localhost:5173 (PID: $FRONTEND_PID)"
echo ""
echo "👉 Appuyez sur Ctrl+C pour arrêter les serveurs"
echo ""

# Attendre que les processus se terminent
wait
