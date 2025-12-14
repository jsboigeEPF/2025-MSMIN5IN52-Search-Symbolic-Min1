
import os

def fix_word_lists():
    """
    This script ensures that all words in possible_words_fr.txt are also present in allowed_words_fr.txt.
    It reads both files, finds the missing words, adds them to the allowed words list,
    sorts the list, and writes it back to the file.
    """
    try:
        with open('data/wordle/possible_words_fr.txt', 'r', encoding='utf-8') as f:
            possible_words = set(line.strip() for line in f)
    except FileNotFoundError:
        print("Error: data/wordle/possible_words_fr.txt not found.")
        return

    try:
        with open('data/wordle/allowed_words_fr.txt', 'r', encoding='utf-8') as f:
            allowed_words = set(line.strip() for line in f)
    except FileNotFoundError:
        print("Error: data/wordle/allowed_words_fr.txt not found. Creating a new one.")
        allowed_words = set()

    missing_words = possible_words - allowed_words

    if not missing_words:
        print("No missing words found. The allowed_words_fr.txt file is already up to date.")
        return

    print(f"Found {len(missing_words)} missing words: {', '.join(sorted(list(missing_words)))}")

    new_allowed_words = sorted(list(allowed_words | missing_words))

    try:
        with open('data/wordle/allowed_words_fr.txt', 'w', encoding='utf-8') as f:
            f.write("\n".join(new_allowed_words))
        print("Successfully updated data/wordle/allowed_words_fr.txt")
    except IOError as e:
        print(f"Error writing to data/wordle/allowed_words_fr.txt: {e}")

if __name__ == "__main__":
    fix_word_lists()
