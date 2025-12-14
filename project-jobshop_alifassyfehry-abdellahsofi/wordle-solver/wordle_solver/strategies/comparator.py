"""
Système de benchmark et comparaison de stratégies.

Permet de tester et comparer les performances de différentes stratégies
sur un ensemble de mots cibles.
"""

from typing import List, Dict, Set, Any, Optional
from dataclasses import dataclass, field
import time
from collections import defaultdict
import statistics

from .base_strategy import BaseStrategy
from ..game import WordleGame, generate_feedback
from ..csp import ConstraintManager, HybridSolver
from ..dictionaries import DictionaryLoader


@dataclass
class GameResult:
    """Résultat d'une partie."""
    target_word: str
    strategy_name: str
    attempts: int
    won: bool
    guesses: List[str]
    time_taken: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'target': self.target_word,
            'strategy': self.strategy_name,
            'attempts': self.attempts,
            'won': self.won,
            'guesses': self.guesses,
            'time': round(self.time_taken, 3)
        }


@dataclass
class StrategyStats:
    """Statistiques d'une stratégie."""
    strategy_name: str
    games_played: int = 0
    games_won: int = 0
    total_attempts: int = 0
    total_time: float = 0.0
    attempt_distribution: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    failed_words: List[str] = field(default_factory=list)
    
    @property
    def win_rate(self) -> float:
        """Taux de victoire."""
        return (self.games_won / self.games_played * 100) if self.games_played > 0 else 0.0
    
    @property
    def average_attempts(self) -> float:
        """Nombre moyen de tentatives (pour les victoires)."""
        return (self.total_attempts / self.games_won) if self.games_won > 0 else 0.0
    
    @property
    def average_time(self) -> float:
        """Temps moyen par partie."""
        return (self.total_time / self.games_played) if self.games_played > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'strategy': self.strategy_name,
            'games_played': self.games_played,
            'games_won': self.games_won,
            'win_rate': round(self.win_rate, 2),
            'average_attempts': round(self.average_attempts, 2),
            'average_time': round(self.average_time, 3),
            'attempt_distribution': dict(self.attempt_distribution),
            'failed_words': self.failed_words
        }


class StrategyComparator:
    """
    Compare les performances de différentes stratégies.
    
    Permet de :
    - Tester plusieurs stratégies sur les mêmes mots
    - Collecter des statistiques détaillées
    - Générer des rapports comparatifs
    """
    
    def __init__(self, dictionary: Set[str], language: str = "en"):
        """
        Initialise le comparateur.
        
        Args:
            dictionary: Dictionnaire de mots valides
            language: Langue ('en' ou 'fr')
        """
        self.dictionary = dictionary
        self.language = language
        self.solver = HybridSolver(dictionary)
        self.results: List[GameResult] = []
        self.stats_by_strategy: Dict[str, StrategyStats] = {}
    
    def test_strategy(
        self,
        strategy: BaseStrategy,
        target_words: List[str],
        verbose: bool = False
    ) -> StrategyStats:
        """
        Teste une stratégie sur un ensemble de mots.
        
        Args:
            strategy: La stratégie à tester
            target_words: Liste de mots cibles
            verbose: Si True, affiche les progrès
            
        Returns:
            Statistiques de la stratégie
        """
        stats = StrategyStats(strategy_name=strategy.name)
        
        for i, target in enumerate(target_words):
            if verbose and (i + 1) % 10 == 0:
                print(f"  Progression: {i+1}/{len(target_words)} mots testés...")
            
            result = self._play_game(strategy, target)
            self.results.append(result)
            
            # Mettre à jour les stats
            stats.games_played += 1
            stats.total_time += result.time_taken
            
            if result.won:
                stats.games_won += 1
                stats.total_attempts += result.attempts
                stats.attempt_distribution[result.attempts] += 1
            else:
                stats.failed_words.append(target)
                stats.attempt_distribution[0] += 1  # 0 = échec
        
        self.stats_by_strategy[strategy.name] = stats
        return stats
    
    def _play_game(self, strategy: BaseStrategy, target_word: str) -> GameResult:
        """
        Joue une partie avec une stratégie donnée.
        
        Args:
            strategy: Stratégie à utiliser
            target_word: Mot cible
            
        Returns:
            Résultat de la partie
        """
        start_time = time.time()
        
        game = WordleGame(target_word)
        cm = ConstraintManager()
        guesses = []
        
        attempt = 0
        
        while not game.is_over and attempt < 6:
            attempt += 1
            
            # Obtenir les mots possibles
            possible_words = self.solver.get_possible_words(cm)
            
            if not possible_words:
                break
            
            # Choisir un mot selon la stratégie
            if attempt == 1:
                guess = strategy.get_first_guess(self.language)
                # S'assurer que le premier mot est dans le dictionnaire
                if guess not in self.dictionary:
                    guess = sorted(possible_words)[0]
            else:
                guess = strategy.choose_word(
                    possible_words, 
                    cm, 
                    attempt,
                    full_dictionary=self.dictionary
                )
            
            if not guess:
                break
            
            # Jouer le mot
            try:
                feedback = game.make_guess(guess)
                guesses.append(guess)
                cm.apply_feedback(feedback)
            except ValueError:
                # Mot invalide, prendre le premier possible
                guess = sorted(possible_words)[0]
                feedback = game.make_guess(guess)
                guesses.append(guess)
                cm.apply_feedback(feedback)
        
        elapsed = time.time() - start_time
        
        return GameResult(
            target_word=target_word,
            strategy_name=strategy.name,
            attempts=len(guesses),
            won=game.is_won,
            guesses=guesses,
            time_taken=elapsed
        )
    
    def compare_strategies(
        self,
        strategies: List[BaseStrategy],
        target_words: List[str],
        verbose: bool = True
    ) -> Dict[str, StrategyStats]:
        """
        Compare plusieurs stratégies sur les mêmes mots.
        
        Args:
            strategies: Liste de stratégies à comparer
            target_words: Mots cibles pour les tests
            verbose: Afficher les progrès
            
        Returns:
            Dictionnaire {nom_stratégie: stats}
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"COMPARAISON DE {len(strategies)} STRATÉGIES")
            print(f"Mots cibles: {len(target_words)}")
            print(f"{'='*70}\n")
        
        for i, strategy in enumerate(strategies, 1):
            if verbose:
                print(f"[{i}/{len(strategies)}] Test de : {strategy.name}")
            
            self.test_strategy(strategy, target_words, verbose=False)
            
            if verbose:
                stats = self.stats_by_strategy[strategy.name]
                print(f"  ✓ Taux de victoire: {stats.win_rate:.1f}%")
                print(f"  ✓ Moyenne tentatives: {stats.average_attempts:.2f}")
                print(f"  ✓ Temps moyen: {stats.average_time:.3f}s\n")
        
        return self.stats_by_strategy
    
    def generate_report(self, detailed: bool = False) -> str:
        """
        Génère un rapport textuel des résultats.
        
        Args:
            detailed: Si True, inclut plus de détails
            
        Returns:
            Rapport formaté
        """
        lines = []
        lines.append("=" * 80)
        lines.append("RAPPORT DE COMPARAISON DES STRATÉGIES".center(80))
        lines.append("=" * 80)
        lines.append("")
        
        # Trier par taux de victoire puis par moyenne
        sorted_stats = sorted(
            self.stats_by_strategy.values(),
            key=lambda s: (-s.win_rate, s.average_attempts)
        )
        
        # Résumé
        lines.append("📊 RÉSUMÉ")
        lines.append("-" * 80)
        lines.append(f"{'Stratégie':<30} {'Victoires':<12} {'Moy.':<8} {'Temps':<10}")
        lines.append("-" * 80)
        
        for stats in sorted_stats:
            lines.append(
                f"{stats.strategy_name:<30} "
                f"{stats.win_rate:>5.1f}% ({stats.games_won}/{stats.games_played})"
                f"    {stats.average_attempts:>4.2f}"
                f"    {stats.average_time:>6.3f}s"
            )
        
        lines.append("")
        
        # Distribution détaillée
        if detailed:
            lines.append("\n📈 DISTRIBUTION DES TENTATIVES")
            lines.append("-" * 80)
            
            for stats in sorted_stats:
                lines.append(f"\n{stats.strategy_name}:")
                dist = stats.attempt_distribution
                
                for attempts in range(1, 7):
                    count = dist.get(attempts, 0)
                    if count > 0:
                        pct = count / stats.games_played * 100
                        bar = "█" * int(pct / 2)
                        lines.append(f"  {attempts} tentatives: {count:>3} ({pct:>5.1f}%) {bar}")
                
                if dist.get(0, 0) > 0:
                    count = dist[0]
                    pct = count / stats.games_played * 100
                    lines.append(f"  Échecs:        {count:>3} ({pct:>5.1f}%)")
        
        lines.append("\n" + "=" * 80)
        
        return "\n".join(lines)
    
    def get_winner(self) -> Optional[str]:
        """
        Retourne le nom de la meilleure stratégie.
        
        Returns:
            Nom de la stratégie gagnante
        """
        if not self.stats_by_strategy:
            return None
        
        # Trier par taux de victoire puis par moyenne
        sorted_stats = sorted(
            self.stats_by_strategy.values(),
            key=lambda s: (-s.win_rate, s.average_attempts)
        )
        
        return sorted_stats[0].strategy_name if sorted_stats else None
    
    def reset(self):
        """Réinitialise toutes les statistiques."""
        self.results.clear()
        self.stats_by_strategy.clear()


def quick_benchmark(
    strategies: List[BaseStrategy],
    n_words: int = 20,
    language: str = "en",
    verbose: bool = True
) -> Dict[str, StrategyStats]:
    """
    Benchmark rapide de stratégies.
    
    Args:
        strategies: Liste de stratégies à tester
        n_words: Nombre de mots à tester
        language: Langue ('en' ou 'fr')
        verbose: Afficher les résultats
        
    Returns:
        Statistiques par stratégie
    """
    # Charger le dictionnaire
    dictionary = DictionaryLoader.load_language(language)
    
    # Sélectionner des mots représentatifs
    words_list = sorted(dictionary)
    step = max(1, len(words_list) // n_words)
    test_words = words_list[::step][:n_words]
    
    # Comparer
    comparator = StrategyComparator(dictionary, language)
    stats = comparator.compare_strategies(strategies, test_words, verbose=verbose)
    
    if verbose:
        print(comparator.generate_report(detailed=True))
    
    return stats
