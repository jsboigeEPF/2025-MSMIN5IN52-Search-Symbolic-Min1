# backend/app/services/csp_solver.py
from typing import List, Dict, Set, Optional
from collections import defaultdict, Counter


class WordleConstraints:
    """Stocke les contraintes du jeu Wordle"""

    def __init__(self):
        self.green: Dict[int, str] = {}
        self.yellow: Dict[int, Set[str]] = defaultdict(set)
        self.grey: Set[str] = set()
        self.min_letter_counts: Dict[str, int] = {}
        self.max_letter_counts: Dict[str, int] = {}


    def update(self, feedback: Dict):
        green = feedback.get("green", {})
        yellow = feedback.get("yellow", {})
        grey = feedback.get("grey", [])

        # Lettres présentes
        present_letters = set(green.values())
        for letters in yellow.values():
            present_letters.update(letters)

        # Greens
        for pos, letter in green.items():
            pos = int(pos)
            self.green[pos] = letter

        # Yellows
        for pos, letters in yellow.items():
            pos = int(pos)
            self.yellow[pos].update(letters)

        # Comptage min
        unique_yellow_letters = set(l for letters in yellow.values() for l in letters)
        counts = Counter(list(green.values()) + list(unique_yellow_letters))

        for letter, count in counts.items():
            self.min_letter_counts[letter] = max(
                self.min_letter_counts.get(letter, 0),
                count
            )

        # Greys → max occurrences
        for letter in grey:
            if letter not in present_letters:
                # vraiment absent
                self.grey.add(letter)
                self.max_letter_counts[letter] = 0
            else:
                # lettre en trop → max = min
                self.max_letter_counts[letter] = self.min_letter_counts.get(letter, 0)


class CSPSolver:
    """Solveur CSP Wordle par filtrage de domaine"""

    def __init__(self, word_length: int = 5):
        self.word_length = word_length
        self.word_list: List[str] = []
        self.secret_word: Optional[str] = None 

    def set_valid_words(self, words: List[str]):
        self.word_list = [
            w.lower() for w in words if len(w) == self.word_length
        ]

    def filter_candidates(
        self,
        constraints: Optional[WordleConstraints] = None,
        max_solutions: int = 1000
    ) -> List[str]:
        candidates = []

        for word in self.word_list:
            if constraints is None or self._check_word(word, constraints):
                candidates.append(word)
                if len(candidates) >= max_solutions:
                    break

        return candidates

    def _check_word(self, word: str, constraints: WordleConstraints) -> bool:
        # Lettres vertes
        for pos, letter in constraints.green.items():
            if pos >= len(word) or word[pos] != letter:
                return False

        # Lettres jaunes
        for pos, letters in constraints.yellow.items():
            for letter in letters:
                if pos < len(word) and word[pos] == letter:
                    return False
                if letter not in word:
                    return False

        # Lettres grises
        for letter in constraints.grey:
            if letter in word:
                if letter not in constraints.green.values() and \
                   all(letter not in letters for letters in constraints.yellow.values()):
                    return False

        # Occurrences minimales
        for letter, min_count in constraints.min_letter_counts.items():
            if word.count(letter) < min_count:
                return False

        # Occurrences maximales
        for letter, max_count in constraints.max_letter_counts.items():
            if word.count(letter) > max_count:
                return False

        return True
