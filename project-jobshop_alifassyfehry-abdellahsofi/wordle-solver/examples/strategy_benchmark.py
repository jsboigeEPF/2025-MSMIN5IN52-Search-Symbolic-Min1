"""
Exemple de benchmark et comparaison de stratégies Wordle.

Ce script compare les performances de différentes stratégies
sur un ensemble de mots représentatifs.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wordle_solver.strategies import (
    SimpleStrategy,
    FrequencyStrategy,
    PositionalFrequencyStrategy,
    FastEntropyStrategy,
    MinimaxStrategy,
    ExpectedSizeStrategy,
    quick_benchmark
)


def benchmark_all_strategies(n_words: int = 30, language: str = "en"):
    """
    Benchmark de toutes les stratégies disponibles.
    
    Args:
        n_words: Nombre de mots à tester
        language: Langue ('en' ou 'fr')
    """
    print("\n" + "="*80)
    print(f"BENCHMARK DES STRATÉGIES WORDLE".center(80))
    print(f"Langue: {language.upper()} | Mots testés: {n_words}".center(80))
    print("="*80 + "\n")
    
    # Définir les stratégies à tester
    strategies = [
        SimpleStrategy(),
        FrequencyStrategy(),
        PositionalFrequencyStrategy(),
        FastEntropyStrategy(evaluation_limit=30),
        MinimaxStrategy(tie_breaker="entropy"),
        ExpectedSizeStrategy(),
    ]
    
    print("📋 Stratégies testées:")
    for i, strategy in enumerate(strategies, 1):
        print(f"  {i}. {strategy.name}")
    print()
    
    # Lancer le benchmark
    stats = quick_benchmark(
        strategies=strategies,
        n_words=n_words,
        language=language,
        verbose=True
    )
    
    # Afficher le gagnant
    best_strategy = max(
        stats.values(),
        key=lambda s: (s.win_rate, -s.average_attempts)
    )
    
    print("\n" + "="*80)
    print("🏆 STRATÉGIE GAGNANTE".center(80))
    print("="*80)
    print(f"\n  {best_strategy.strategy_name}")
    print(f"  Taux de victoire: {best_strategy.win_rate:.1f}%")
    print(f"  Moyenne: {best_strategy.average_attempts:.2f} tentatives")
    print(f"  Temps: {best_strategy.average_time:.3f}s par partie")
    print("\n" + "="*80 + "\n")


def compare_two_strategies():
    """Compare deux stratégies en détail."""
    print("\n" + "="*80)
    print("COMPARAISON DÉTAILLÉE: Fréquence vs Entropie".center(80))
    print("="*80 + "\n")
    
    from wordle_solver.dictionaries import DictionaryLoader
    from wordle_solver.strategies import StrategyComparator
    
    # Charger dictionnaire
    dictionary = DictionaryLoader.load_english()
    
    # Sélectionner 50 mots représentatifs
    words_list = sorted(dictionary)
    step = len(words_list) // 50
    test_words = words_list[::step][:50]
    
    # Créer les stratégies
    freq_strategy = FrequencyStrategy()
    entropy_strategy = FastEntropyStrategy(evaluation_limit=50)
    
    # Comparer
    comparator = StrategyComparator(dictionary, language="en")
    stats = comparator.compare_strategies(
        [freq_strategy, entropy_strategy],
        test_words,
        verbose=True
    )
    
    # Rapport détaillé
    print("\n" + comparator.generate_report(detailed=True))
    
    # Analyse des différences
    print("\n" + "="*80)
    print("ANALYSE DES DIFFÉRENCES".center(80))
    print("="*80 + "\n")
    
    freq_stats = stats[freq_strategy.name]
    entropy_stats = stats[entropy_strategy.name]
    
    # Comparaison des métriques
    print(f"📊 Taux de victoire:")
    print(f"  Fréquence: {freq_stats.win_rate:.1f}%")
    print(f"  Entropie:  {entropy_stats.win_rate:.1f}%")
    diff_win = entropy_stats.win_rate - freq_stats.win_rate
    print(f"  → Différence: {diff_win:+.1f}%\n")
    
    print(f"📊 Moyenne de tentatives:")
    print(f"  Fréquence: {freq_stats.average_attempts:.2f}")
    print(f"  Entropie:  {entropy_stats.average_attempts:.2f}")
    diff_avg = entropy_stats.average_attempts - freq_stats.average_attempts
    print(f"  → Différence: {diff_avg:+.2f} tentatives\n")
    
    print(f"⏱️  Temps moyen:")
    print(f"  Fréquence: {freq_stats.average_time:.3f}s")
    print(f"  Entropie:  {entropy_stats.average_time:.3f}s")
    ratio = entropy_stats.average_time / freq_stats.average_time if freq_stats.average_time > 0 else 0
    print(f"  → Entropie est {ratio:.1f}x plus lente\n")
    
    print("="*80 + "\n")


def demonstrate_strategy(strategy_name: str = "frequency"):
    """
    Démontre une stratégie sur quelques exemples.
    
    Args:
        strategy_name: 'frequency', 'entropy', ou 'minimax'
    """
    from wordle_solver import (
        WordleGame,
        HybridSolver,
        ConstraintManager,
        DictionaryLoader
    )
    from wordle_solver.strategies import (
        FrequencyStrategy,
        FastEntropyStrategy,
        MinimaxStrategy
    )
    
    # Choisir la stratégie
    strategies_map = {
        'frequency': FrequencyStrategy(),
        'entropy': FastEntropyStrategy(evaluation_limit=30),
        'minimax': MinimaxStrategy()
    }
    
    strategy = strategies_map.get(strategy_name, FrequencyStrategy())
    
    print("\n" + "="*80)
    print(f"DÉMONSTRATION: {strategy.name}".center(80))
    print("="*80 + "\n")
    
    # Charger dictionnaire
    dictionary = DictionaryLoader.load_english()
    solver = HybridSolver(dictionary)
    
    # Mots de test
    test_words = ["ROBOT", "AUDIO", "PIANO", "TIGER"]
    
    for target in test_words:
        print(f"\n🎯 Résolution de: {target}")
        print("-" * 60)
        
        game = WordleGame(target)
        cm = ConstraintManager()
        
        attempt = 0
        while not game.is_over and attempt < 6:
            attempt += 1
            
            # Obtenir mots possibles
            possible = solver.get_possible_words(cm)
            
            # Choisir selon la stratégie
            if attempt == 1:
                guess = strategy.get_first_guess("en")
                if guess not in dictionary:
                    guess = sorted(possible)[0]
            else:
                guess = strategy.choose_word(
                    possible, cm, attempt,
                    full_dictionary=dictionary
                )
            
            # Jouer
            feedback = game.make_guess(guess)
            cm.apply_feedback(feedback)
            
            # Afficher
            print(f"  Tentative {attempt}: {feedback.to_string()}")
            if len(possible) <= 10:
                print(f"    Possibles avant: {sorted(possible)}")
        
        if game.is_won:
            print(f"  ✅ Résolu en {len(game.attempts)} tentatives")
        else:
            print(f"  ❌ Échec")
        
        print()
    
    print("="*80 + "\n")


def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark des stratégies Wordle")
    parser.add_argument(
        '--mode',
        choices=['benchmark', 'compare', 'demo'],
        default='benchmark',
        help='Mode de test'
    )
    parser.add_argument(
        '--n-words',
        type=int,
        default=30,
        help='Nombre de mots à tester (benchmark)'
    )
    parser.add_argument(
        '--language',
        choices=['en', 'fr'],
        default='en',
        help='Langue'
    )
    parser.add_argument(
        '--strategy',
        choices=['frequency', 'entropy', 'minimax'],
        default='frequency',
        help='Stratégie à démontrer (mode demo)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'benchmark':
            benchmark_all_strategies(args.n_words, args.language)
        
        elif args.mode == 'compare':
            compare_two_strategies()
        
        elif args.mode == 'demo':
            demonstrate_strategy(args.strategy)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur\n")
    except Exception as e:
        print(f"\n❌ Erreur: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Si pas d'arguments, lancer le benchmark par défaut
    if len(sys.argv) == 1:
        print("\n💡 Usage:")
        print("  python strategy_benchmark.py --mode benchmark --n-words 30")
        print("  python strategy_benchmark.py --mode compare")
        print("  python strategy_benchmark.py --mode demo --strategy entropy\n")
        
        print("Lancement du benchmark par défaut...\n")
        benchmark_all_strategies(n_words=20, language="en")
    else:
        main()
