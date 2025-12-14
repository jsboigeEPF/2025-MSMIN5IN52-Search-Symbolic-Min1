#!/usr/bin/env python3
"""
Script de test pour l'intégration Gemini.
Vérifie que tout est correctement configuré.
"""

import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_environment():
    """Teste la configuration de l'environnement."""
    print("🔍 Vérification de l'environnement...\n")
    
    # Test 1: Charger python-dotenv
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv installé")
    except ImportError:
        print("❌ python-dotenv non installé")
        print("   → pip install python-dotenv")
        return False
    
    # Test 2: Charger google-genai
    try:
        from google import genai
        print("✅ google-genai installé")
    except ImportError:
        print("❌ google-genai non installé")
        print("   → pip install google-genai")
        return False
    
    # Test 3: Charger le fichier .env
    import os
    env_path = Path(__file__).parent.parent / 'wordle-solver/backend/.env'
    
    if env_path.exists():
        print(f"✅ Fichier .env trouvé: {env_path}")
        load_dotenv(env_path)
    else:
        print(f"❌ Fichier .env non trouvé: {env_path}")
        print("   → Créez un fichier .env dans wordle-solver/")
        return False
    
    # Test 4: Vérifier la clé API
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print(f"✅ GEMINI_API_KEY configurée (longueur: {len(api_key)} caractères)")
        if len(api_key) < 20:
            print("⚠️  La clé semble trop courte, vérifiez qu'elle est correcte")
    else:
        print("❌ GEMINI_API_KEY non trouvée dans .env")
        print("   → Ajoutez: GEMINI_API_KEY=votre_clé_ici")
        return False
    
    return True


def test_gemini_service():
    """Teste le service Gemini."""
    print("\n🧪 Test du service Gemini...\n")
    
    try:
        from backend.gemini_service import get_gemini_service
        
        service = get_gemini_service()
        if service is None:
            print("❌ Impossible de créer le service Gemini")
            return False
        
        print("✅ Service Gemini initialisé")
        
        # Test d'une définition
        print("\n📖 Test d'une définition...")
        test_word = "ordinateur"
        definition = service.get_word_definition(test_word, "fr")
        
        if definition:
            print(f"✅ Définition obtenue pour '{test_word}':")
            print(f"\n{definition}\n")
            return True
        else:
            print("❌ Impossible d'obtenir la définition")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoint():
    """Teste l'endpoint API."""
    print("\n🌐 Test de l'endpoint API...\n")
    
    try:
        import requests
        
        # Vérifier si le backend est en cours d'exécution
        try:
            response = requests.get('http://localhost:8000/', timeout=2)
            print("✅ Backend accessible sur http://localhost:8000")
        except requests.exceptions.ConnectionError:
            print("⚠️  Backend non accessible")
            print("   → Démarrez le backend: cd backend && python main.py")
            return False
        
        # Tester l'endpoint de définition
        test_data = {
            "word": "test",
            "language": "en"
        }
        
        response = requests.post(
            'http://localhost:8000/api/word/definition',
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Endpoint /api/word/definition fonctionne")
                print(f"   Définition de '{test_data['word']}':")
                print(f"   {data.get('definition', 'N/A')[:100]}...")
                return True
            else:
                print(f"⚠️  Endpoint répond mais avec une erreur: {data.get('error')}")
                return False
        else:
            print(f"❌ Endpoint répond avec le code {response.status_code}")
            return False
            
    except ImportError:
        print("⚠️  requests non installé (optionnel pour ce test)")
        print("   → pip install requests")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test API: {e}")
        return False


def main():
    """Fonction principale."""
    print("=" * 60)
    print("🤖 TEST D'INTÉGRATION GEMINI - WORDLE SOLVER")
    print("=" * 60)
    print()
    
    # Test 1: Environnement
    env_ok = test_environment()
    
    if not env_ok:
        print("\n" + "=" * 60)
        print("❌ Configuration incomplète")
        print("=" * 60)
        print("\n📚 Consultez GEMINI_SETUP.md pour les instructions complètes")
        sys.exit(1)
    
    # Test 2: Service Gemini
    service_ok = test_gemini_service()
    
    # Test 3: API Endpoint (optionnel)
    api_ok = test_api_endpoint()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"Environnement:     {'✅' if env_ok else '❌'}")
    print(f"Service Gemini:    {'✅' if service_ok else '❌'}")
    print(f"Endpoint API:      {'✅' if api_ok else '⚠️  (backend non démarré)'}")
    print("=" * 60)
    
    if env_ok and service_ok:
        print("\n🎉 Configuration réussie !")
        print("Vous pouvez maintenant utiliser l'intégration Gemini.")
        print("\n📖 Pour démarrer:")
        print("   1. cd backend")
        print("   2. python main.py")
        print("   3. Ouvrez http://localhost:3000")
        sys.exit(0)
    else:
        print("\n❌ Certains tests ont échoué")
        print("📚 Consultez GEMINI_SETUP.md pour plus d'aide")
        sys.exit(1)


if __name__ == "__main__":
    main()
