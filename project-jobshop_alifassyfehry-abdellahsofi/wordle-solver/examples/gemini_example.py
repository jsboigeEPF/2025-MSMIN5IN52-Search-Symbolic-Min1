"""
Exemple simple d'utilisation de l'API Gemini.
Ce script montre comment obtenir une définition de mot.
"""

from google import genai
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

def main():
    print("=" * 60)
    print("🤖 EXEMPLE D'UTILISATION DE GEMINI")
    print("=" * 60)
    print()
    
    # Vérifier la clé API
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY non trouvée dans le fichier .env")
        print("\n📝 Solution:")
        print("1. Créez un fichier .env dans le dossier wordle-solver/")
        print("2. Ajoutez: GEMINI_API_KEY=votre_clé_api_ici")
        print("3. Obtenez une clé gratuite sur https://ai.google.dev/")
        return
    
    print(f"✅ Clé API chargée (longueur: {len(api_key)} caractères)")
    print()
    
    # Créer le client Gemini
    try:
        client = genai.Client()
        print("✅ Client Gemini initialisé")
        print()
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return
    
    # Exemples de mots à définir
    exemples = [
        ("ordinateur", "fr"),
        ("house", "en"),
        ("python", "en"),
        ("intelligence", "fr")
    ]
    
    for word, lang in exemples:
        print("-" * 60)
        print(f"📖 Définition de '{word.upper()}' ({lang})")
        print("-" * 60)
        
        # Construire le prompt
        if lang == "fr":
            prompt = f'Donne une définition simple et concise (maximum 2-3 phrases) du mot "{word}" en français.'
        else:
            prompt = f'Give a simple and concise definition (maximum 2-3 sentences) of the word "{word}" in English.'
        
        try:
            # Appel à l'API Gemini
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            
            definition = response.text.strip()
            print(f"\n{definition}\n")
            
        except Exception as e:
            print(f"\n❌ Erreur: {e}\n")
    
    print("=" * 60)
    print("✅ Exemples terminés !")
    print("=" * 60)


if __name__ == "__main__":
    main()
