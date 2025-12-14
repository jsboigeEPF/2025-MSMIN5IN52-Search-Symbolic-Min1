"""
Exemple simple d'utilisation des stratégies.

Montre comment utiliser les différentes stratégies pour résoudre Wordle.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wordle_solver import (
    WordleGame,
    HybridSolver,
    ConstraintManager,
    DictionaryLoader
)
from wordle_solver.strategies import (
    SimpleStrategy,
    FrequencyStrategy,
    FastEntropyStrategy
)


def solve_with_strategy(target: str, strategy, language: str = "en"):
    """
    Résout un Wordle avec une stratégie donnée.
    
    Args:
        target: Mot cible
        strategy: Stratégie à utiliser
        language: Langue
    """
    print(f"\n🎯 Résolution de '{target}' avec {strategy.name}")
    print("=" * 60)
    
    # Charger dictionnaire
    dictionary = DictionaryLoader.load_language(language)
    solver = HybridSolver(dictionary)
    
    # Initialiser
    game = WordleGame(target)
    cm = ConstraintManager()
    
    attempt = 0
    
    while not game.is_over and attempt < 6:
        attempt += 1
        
        # Obtenir mots possibles
        possible_words = solver.get_possible_words(cm)
        
        print(f"\nTentative {attempt}:")
        print(f"  Mots possibles: {len(possible_words)}")
        
        if len(possible_words) <= 5:
            print(f"  Candidats: {sorted(possible_words)}")
        
        # Choisir un mot selon la stratégie
        if attempt == 1:
            guess = strategy.get_first_guess(language)
            # Vérifier que c'est dans le dictionnaire
            if guess not in dictionary:
                guess = sorted(possible_words)[0]
            print(f"  Premier mot optimal: {guess}")
        else:
            guess = strategy.choose_word(
                possible_words,
                cm,
                attempt,
                full_dictionary=dictionary
            )
            print(f"  Choix stratégique: {guess}")
        
        if not guess:
            print("  ❌ Aucun mot disponible!")
            break
        
        # Jouer le mot
        feedback = game.make_guess(guess)
        print(f"  Résultat: {feedback.to_string()}")
        
        # Appliquer les contraintes
        cm.apply_feedback(feedback)
    
    # Résultat final
    print("\n" + "=" * 60)
    if game.is_won:
        print(f"✅ GAGNÉ en {len(game.attempts)} tentatives!")
    else:
        print(f"❌ PERDU - Le mot était: {target}")
    
    print("\nHistorique:")
    for i, fb in enumerate(game.get_history(), 1):
        print(f"  {i}. {fb.to_string()}")
    print()


def compare_strategies_on_word(target: str, language: str = "en"):
    """
    Compare plusieurs stratégies sur le même mot.
    
    Args:
        target: Mot cible
        language: Langue
    """
    print("\n" + "=" * 70)
    print(f"COMPARAISON DES STRATÉGIES SUR '{target}'".center(70))
    print("=" * 70)
    
    strategies = [
        SimpleStrategy(),
        FrequencyStrategy(),
        FastEntropyStrategy(evaluation_limit=30)
    ]
    
    results = []
    
    for strategy in strategies:
        # Charger dictionnaire
        dictionary = DictionaryLoader.load_language(language)
        solver = HybridSolver(dictionary)
        
        # Résoudre
        game = WordleGame(target)
        cm = ConstraintManager()
        
        guesses = []
        attempt = 0
        
        while not game.is_over and attempt < 6:
            attempt += 1
            possible = solver.get_possible_words(cm)
            
            if attempt == 1:
                guess = strategy.get_first_guess(language)
                if guess not in dictionary:
                    guess = sorted(possible)[0]
            else:
                guess = strategy.choose_word(possible, cm, attempt, full_dictionary=dictionary)
            
            if not guess:
                break
            
            feedback = game.make_guess(guess)
            guesses.append(guess)
            cm.apply_feedback(feedback)
        
        results.append({
            'strategy': strategy.name,
            'attempts': len(guesses),
            'won': game.is_won,
            'guesses': guesses
        })
    
    # Afficher les résultats
    print("\n📊 Résultats:")
    print("-" * 70)
    print(f"{'Stratégie':<30} {'Tentatives':<12} {'Chemin'}")
    print("-" * 70)
    
    for result in results:
        status = "✅" if result['won'] else "❌"
        attempts = f"{result['attempts']}/6" if result['won'] else "ÉCHEC"
        path = " → ".join(result['guesses'])
        
        print(f"{result['strategy']:<30} {status} {attempts:<9} {path}")
    
    print("\n" + "=" * 70 + "\n")


def interactive_solver():
    """Mode interactif : l'utilisateur choisit la stratégie."""
    print("\n" + "=" * 70)
    print("MODE INTERACTIF - RÉSOLUTION WORDLE".center(70))
    print("=" * 70 + "\n")
    
    # Choisir la langue
    print("Langue:")
    print("  1. Anglais (EN)")
    print("  2. Français (FR)")
    
    lang_choice = input("\nChoix (1 ou 2): ").strip()
    language = "fr" if lang_choice == "2" else "en"
    
    # Choisir la stratégie
    print("\nStratégie:")
    print("  1. Simple (alphabétique)")
    print("  2. Fréquence des lettres")
    print("  3. Entropie (optimal)")
    
    strat_choice = input("\nChoix (1, 2 ou 3): ").strip()
    
    strategies = {
        "1": SimpleStrategy(),
        "2": FrequencyStrategy(),
        "3": FastEntropyStrategy(evaluation_limit=30)
    }
    
    strategy = strategies.get(strat_choice, FrequencyStrategy())
    
    # Entrer le mot cible
    target = input("\nMot cible (5 lettres): ").strip().upper()
    
    if len(target) != 5:
        print("❌ Le mot doit contenir exactement 5 lettres!")
        return
    
    # Résoudre
    solve_with_strategy(target, strategy, language)


def main():
    """Fonction principale."""
    print("\n" + "=" * 70)
    print("EXEMPLES D'UTILISATION DES STRATÉGIES".center(70))
    print("=" * 70)
    
    # Exemple 1: Résolution simple
    print("\n📝 EXEMPLE 1: Résolution avec la stratégie de fréquence")
    print("-" * 70)
    
    strategy = FrequencyStrategy()
    solve_with_strategy("ROBOT", strategy, "en")
    
    input("\nAppuyez sur Entrée pour continuer...")
    
    # Exemple 2: Comparaison
    print("\n📝 EXEMPLE 2: Comparaison de stratégies")
    print("-" * 70)
    
    compare_strategies_on_word("AUDIO", "en")
    
    input("\nAppuyez sur Entrée pour le mode interactif...")
    
    # Exemple 3: Mode interactif
    try:
        interactive_solver()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption\n")
    except Exception as e:
        print(f"\n❌ Erreur: {e}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur\n")
    except Exception as e:
        print(f"\n❌ Erreur: {e}\n")
        import traceback
        traceback.print_exc()
