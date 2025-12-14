import random
import sys

from src.pattern import get_pattern, pattern_to_string
from src.prior import get_word_list

GAME_NAMES = ["wordle"]


def play_wordle_game(game_name="wordle", secret_word=None):
    all_words = get_word_list(game_name, short=False)
    short_word_list = get_word_list(game_name, short=True)

    if secret_word is None:
        secret_word = random.choice(short_word_list)
    elif secret_word not in all_words:
        print(f"Error: '{secret_word}' is not a valid word.", file=sys.stderr)
        return
    
    print("--- Welcome to Interactive Wordle! ---")
    print("I have picked a 5-letter word. You have 6 guesses to find it.")
    print("After each guess, I will show you the pattern:")
    print("  ⬛ (black/gray): Letter is not in the word.")
    print("  🟨 (yellow): Letter is in the word but in the wrong position.")
    print("  🟩 (green): Letter is in the word and in the correct position.")

    guesses_made = []

    for turn in range(1, 7):
        print(f"\n--- Turn {turn} ---")
        while True:
            user_guess = input("Enter your guess: ").lower().strip()
            if len(user_guess) != 5:
                print("Your guess must be a 5-letter word.")
            elif user_guess not in all_words:
                print("Your guess is not a valid word.")
            else:
                break
        
        guesses_made.append(user_guess)

        pattern_int = get_pattern(user_guess, secret_word, game_name)
        pattern_str = pattern_to_string(pattern_int)
        
        print(f"Your guess: {user_guess.upper()}")
        print(f"Pattern: {pattern_str}")

        if user_guess == secret_word:
            print(f"\nCongratulations! You guessed the word '{secret_word.upper()}' in {turn} tries!")
            return

    print("\nGame over! You ran out of guesses.")
    print(f"The word was '{secret_word.upper()}'.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Play Wordle interactively.")
    parser.add_argument("--word", type=str, default=None, help="A specific word to play with.")
    args = parser.parse_args()

    play_wordle_game(secret_word=args.word)
