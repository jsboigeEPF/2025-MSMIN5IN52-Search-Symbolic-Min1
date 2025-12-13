# backend/app/data/word_generator.py
import random
from typing import List

def get_random_word(word_list: List[str]) -> str:
    """
    Retourne un mot aléatoire de la liste donnée.
    """
    if not word_list:
        raise ValueError("La liste de mots est vide.")
    return random.choice(word_list)


def generate_word(language: str, fr_words: List[str], en_words: List[str]) -> str:
    """
    Génère un mot aléatoire selon la langue choisie.
    language: "fr" ou "en"
    """
    language = language.lower()
    if language == "fr":
        return get_random_word(fr_words)
    elif language == "en":
        return get_random_word(en_words)
    else:
        raise ValueError("Langue invalide ! Choisir 'fr' ou 'en'.")


if __name__ == "__main__":
    # --- Exemple d'utilisation ---
    try:
        from load_fr_word import load_fr_words  # mots français
        from load_en_word import load_en_words  # mots anglais

        # Charger les listes de mots
        fr_words = load_fr_words()
        en_words = load_en_words()

        # Demander à l'utilisateur la langue
        user_lang = input("Choisissez la langue (fr/en) : ").strip().lower()
        mot_secret = generate_word(user_lang, fr_words, en_words)
        print(f"Mot secret généré ({user_lang}): {mot_secret}")

    except Exception as e:
        print(f"Erreur lors de la génération du mot : {e}")
