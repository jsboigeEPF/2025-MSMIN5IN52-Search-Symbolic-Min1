"""
Script de démarrage pour l'interface web VRP.
"""

import sys
import os

def check_dependencies():
    """vérifie que les dépendances sont installées"""
    try:
        import flask
        import flask_cors
        import ortools
        import folium
        import numpy
        return True
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("\nVeuillez installer les dépendances avec:")
        print("pip install -r requirements.txt")
        return False

def main():
    """lance l'application web"""
    # vérifier si on est dans le processus principal (évite les doublons avec le reloader)
    is_main_process = os.environ.get('WERKZEUG_RUN_MAIN') != 'true'
    
    if is_main_process:
        print("=" * 60)
        print("🚚 Interface Web pour l'Optimisation VRP")
        print("=" * 60)
        
        if not check_dependencies():
            sys.exit(1)
        
        print("\n✅ Toutes les dépendances sont installées")
        print("\n🌐 Démarrage du serveur web...")
        print("📱 Ouvrez votre navigateur à l'adresse: http://localhost:5000")
        print("\n⚠️  Appuyez sur Ctrl+C pour arrêter le serveur\n")
    
    # importer et lancer l'application
    from frontend.app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt du serveur")
        sys.exit(0)

