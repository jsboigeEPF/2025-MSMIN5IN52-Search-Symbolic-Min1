# backend/app/data/load_en_words.py

import os

def load_en_words(file_path: str = None) -> list[str]:
    """
    Charge tous les mots anglais depuis un fichier txt.
    Chaque mot doit être sur une ligne séparée dans le fichier.
    
    Args:
        file_path (str, optional): Chemin vers le fichier txt contenant les mots.
                                   Par défaut, cherche 'en_words.txt' dans le même dossier.

    Returns:
        list[str]: Liste de mots anglais en majuscules.
    """
    if file_path is None:
        # Chemin par défaut relatif à ce script
        file_path = os.path.join(os.path.dirname(__file__), "en_words.txt")
    
    words = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if word:  # Ignorer les lignes vides
                    words.append(word.upper())
    except FileNotFoundError:
        print(f"Fichier introuvable : {file_path}")
    except Exception as e:
        print(f"Erreur lors du chargement des mots : {e}")
    
    return words

# Test rapide
if __name__ == "__main__":
    words = load_en_words()
    print(f"{len(words)} mots chargés.")
    print("Exemples :", words[:10])
