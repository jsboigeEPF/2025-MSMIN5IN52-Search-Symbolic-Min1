"""
Script de benchmarking complet pour comparer tous les solveurs.

Compare les performances des différentes approches (simple, CSP, optimisé, supervisé, hybride).
"""

import time
import numpy as np
from typing import List, Dict
from tqdm import tqdm
import matplotlib.pyplot as plt
from game.board import Board, GameState
from solvers.simple_solver import SimpleSolver
from solvers.ortools_solver import ORToolsSolver
from solvers.optimized_solver import OptimizedSolver
from solvers.supervised_solver import SupervisedSolver, HybridSolver


class SolverBenchmark:
    """Classe pour benchmarker les solveurs."""
    
    def __init__(self, width: int, height: int, num_mines: int):
        """
        Initialise le benchmark.
        
        Args:
            width: Largeur des grilles
            height: Hauteur des grilles
            num_mines: Nombre de mines
        """
        self.width = width
        self.height = height
        self.num_mines = num_mines
    
    def run_single_game(self, solver_class, seed: int, **solver_kwargs) -> Dict:
        """
        Joue une partie avec un solveur.
        
        Args:
            solver_class: Classe du solveur
            seed: Seed pour la génération
            **solver_kwargs: Arguments du solveur
            
        Returns:
            Dictionnaire de résultats
        """
        board = Board(self.width, self.height, self.num_mines, seed=seed)
        solver = solver_class(board, **solver_kwargs)
        
        start_time = time.time()
        move_times = []
        
        while board.game_state == GameState.ONGOING:
            move_start = time.time()
            move = solver.get_next_move()
            move_time = time.time() - move_start
            move_times.append(move_time)
            
            if move is None:
                break
            
            success = board.reveal(move[0], move[1])
            
            if not success:
                break  # Mine touchée
        
        total_time = time.time() - start_time
        
        # Résultats
        stats = solver.get_stats()
        
        result = {
            'won': board.game_state == GameState.WON,
            'num_moves': stats['num_moves'],
            'num_logical': stats['num_logical_deductions'],
            'num_probabilistic': stats['num_probability_guesses'],
            'total_time': total_time,
            'avg_move_time': np.mean(move_times) if move_times else 0,
            'max_move_time': np.max(move_times) if move_times else 0,
        }
        
        # Statistiques additionnelles selon le solveur
        if hasattr(solver, 'get_component_stats'):
            comp_stats = solver.get_component_stats()
            if comp_stats:
                result['num_components'] = comp_stats.get('num_components', 0)
                result['avg_component_size'] = comp_stats.get('avg_size', 0)
        
        return result
    
    def benchmark_solver(
        self,
        solver_class,
        num_games: int = 100,
        seed_start: int = 0,
        **solver_kwargs
    ) -> Dict:
        """
        Benchmark un solveur sur plusieurs parties.
        
        Args:
            solver_class: Classe du solveur
            num_games: Nombre de parties
            seed_start: Seed de départ
            **solver_kwargs: Arguments du solveur
            
        Returns:
            Statistiques agrégées
        """
        results = []
        
        for i in tqdm(range(num_games), desc=f"Testing {solver_class.__name__}"):
            try:
                result = self.run_single_game(solver_class, seed_start + i, **solver_kwargs)
                results.append(result)
            except Exception as e:
                print(f"Erreur game {i}: {e}")
                continue
        
        # Agréger les résultats
        num_wins = sum(1 for r in results if r['won'])
        
        aggregate = {
            'solver_name': solver_class.__name__,
            'num_games': len(results),
            'win_rate': 100 * num_wins / len(results) if results else 0,
            'avg_moves': np.mean([r['num_moves'] for r in results]),
            'avg_logical': np.mean([r['num_logical'] for r in results]),
            'avg_probabilistic': np.mean([r['num_probabilistic'] for r in results]),
            'avg_total_time': np.mean([r['total_time'] for r in results]),
            'avg_move_time': np.mean([r['avg_move_time'] for r in results]) * 1000,  # ms
            'max_move_time': np.max([r['max_move_time'] for r in results]) * 1000,  # ms
        }
        
        # Composantes si disponibles
        if any('num_components' in r for r in results):
            comp_results = [r for r in results if 'num_components' in r]
            aggregate['avg_components'] = np.mean([r['num_components'] for r in comp_results])
            aggregate['avg_component_size'] = np.mean([r['avg_component_size'] for r in comp_results])
        
        return aggregate
    
    def compare_solvers(
        self,
        solvers: List[Dict],
        num_games: int = 100,
        seed_start: int = 0
    ) -> List[Dict]:
        """
        Compare plusieurs solveurs.
        
        Args:
            solvers: Liste de dict {
                'class': SolverClass,
                'name': 'Display Name',
                'kwargs': {...}
            }
            num_games: Nombre de parties par solveur
            seed_start: Seed de départ
            
        Returns:
            Liste des résultats agrégés
        """
        all_results = []
        
        print(f"\n{'='*60}")
        print(f"BENCHMARK: {self.width}x{self.height} avec {self.num_mines} mines")
        print(f"Parties par solveur: {num_games}")
        print(f"{'='*60}\n")
        
        for solver_config in solvers:
            solver_class = solver_config['class']
            solver_name = solver_config.get('name', solver_class.__name__)
            solver_kwargs = solver_config.get('kwargs', {})
            
            print(f"\n🤖 Testing {solver_name}...")
            
            try:
                result = self.benchmark_solver(
                    solver_class,
                    num_games,
                    seed_start,
                    **solver_kwargs
                )
                result['display_name'] = solver_name
                all_results.append(result)
            except Exception as e:
                print(f"❌ Erreur avec {solver_name}: {e}")
                continue
        
        return all_results
    
    def print_results(self, results: List[Dict]):
        """
        Affiche les résultats de manière formatée.
        
        Args:
            results: Liste des résultats
        """
        print(f"\n{'='*80}")
        print("RÉSULTATS COMPARATIFS")
        print(f"{'='*80}\n")
        
        # Trier par taux de victoire
        results_sorted = sorted(results, key=lambda x: x['win_rate'], reverse=True)
        
        # En-tête
        print(f"{'Solveur':<25} {'Win%':<10} {'Moves':<10} {'Logical%':<12} {'Time/Move':<12}")
        print("-" * 80)
        
        for r in results_sorted:
            logical_pct = 100 * r['avg_logical'] / r['avg_moves'] if r['avg_moves'] > 0 else 0
            
            print(
                f"{r['display_name']:<25} "
                f"{r['win_rate']:>6.1f}%   "
                f"{r['avg_moves']:>7.1f}   "
                f"{logical_pct:>8.1f}%     "
                f"{r['avg_move_time']:>8.1f}ms"
            )
        
        print("\n" + "="*80)
        print("Détails:")
        
        for r in results_sorted:
            print(f"\n🤖 {r['display_name']}")
            print(f"   Win Rate: {r['win_rate']:.1f}%")
            print(f"   Avg Moves: {r['avg_moves']:.1f}")
            print(f"   Logical: {r['avg_logical']:.1f} ({100*r['avg_logical']/r['avg_moves'] if r['avg_moves']>0 else 0:.1f}%)")
            print(f"   Probabilistic: {r['avg_probabilistic']:.1f}")
            print(f"   Avg Time per Move: {r['avg_move_time']:.1f}ms")
            print(f"   Max Time per Move: {r['max_move_time']:.1f}ms")
            print(f"   Total Time per Game: {r['avg_total_time']:.2f}s")
            
            if 'avg_components' in r:
                print(f"   Avg Components: {r['avg_components']:.1f}")
                print(f"   Avg Component Size: {r['avg_component_size']:.1f}")
    
    def plot_results(self, results: List[Dict], save_path: str = None):
        """
        Trace des graphiques comparatifs.
        
        Args:
            results: Liste des résultats
            save_path: Chemin de sauvegarde optionnel
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        names = [r['display_name'] for r in results]
        
        # 1. Taux de victoire
        ax = axes[0, 0]
        win_rates = [r['win_rate'] for r in results]
        bars = ax.bar(names, win_rates, color='#2ecc71')
        ax.set_ylabel('Win Rate (%)')
        ax.set_title('Taux de Victoire par Solveur')
        ax.set_ylim(0, 100)
        ax.grid(axis='y', alpha=0.3)
        
        # Rotation labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Valeurs sur les barres
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%', ha='center', va='bottom')
        
        # 2. Temps par coup
        ax = axes[0, 1]
        move_times = [r['avg_move_time'] for r in results]
        ax.bar(names, move_times, color='#3498db')
        ax.set_ylabel('Temps moyen (ms)')
        ax.set_title('Temps par Coup')
        ax.grid(axis='y', alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 3. Proportion déductions logiques
        ax = axes[1, 0]
        logical_pcts = [
            100 * r['avg_logical'] / r['avg_moves'] if r['avg_moves'] > 0 else 0
            for r in results
        ]
        ax.bar(names, logical_pcts, color='#9b59b6')
        ax.set_ylabel('Déductions Logiques (%)')
        ax.set_title('Proportion de Déductions Logiques')
        ax.set_ylim(0, 100)
        ax.grid(axis='y', alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 4. Nombre de coups
        ax = axes[1, 1]
        avg_moves = [r['avg_moves'] for r in results]
        ax.bar(names, avg_moves, color='#e74c3c')
        ax.set_ylabel('Nombre de coups')
        ax.set_title('Nombre Moyen de Coups')
        ax.grid(axis='y', alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"\n📊 Graphiques sauvegardés: {save_path}")
        
        plt.show()


def run_full_benchmark():
    """Lance un benchmark complet sur toutes les difficultés."""
    
    # Configurations
    difficulties = {
        'Débutant (9x9, 10 mines)': {
            'width': 9,
            'height': 9,
            'num_mines': 10,
            'num_games': 100
        },
        'Intermédiaire (16x16, 40 mines)': {
            'width': 16,
            'height': 16,
            'num_mines': 40,
            'num_games': 100
        },
        'Expert (30x16, 99 mines)': {
            'width': 30,
            'height': 16,
            'num_mines': 99,
            'num_games': 50  # Moins de parties (plus long)
        }
    }
    
    # Solveurs à tester
    solvers = [
        {
            'class': SimpleSolver,
            'name': 'Simple (Règles AFN/AMN)',
            'kwargs': {}
        },
        {
            'class': ORToolsSolver,
            'name': 'CSP (OR-Tools)',
            'kwargs': {}
        },
        {
            'class': OptimizedSolver,
            'name': 'CSP Optimisé (Composantes)',
            'kwargs': {}
        },
    ]
    
    # Ajouter solveurs ML si modèles disponibles
    import os
    model_path_medium = "training/models/medium_cnn/best_model.pth"
    
    if os.path.exists(model_path_medium):
        solvers.append({
            'class': SupervisedSolver,
            'name': 'Supervisé (CNN)',
            'kwargs': {'model_path': model_path_medium}
        })
        
        solvers.append({
            'class': HybridSolver,
            'name': 'Hybride (CSP + CNN)',
            'kwargs': {'model_path': model_path_medium}
        })
    else:
        print(f"⚠️  Modèle CNN non trouvé: {model_path_medium}")
        print("   Entraînez d'abord le modèle avec training/train.py")
    
    # Benchmarker chaque difficulté
    all_difficulty_results = {}
    
    for difficulty_name, config in difficulties.items():
        print(f"\n\n{'#'*80}")
        print(f"# {difficulty_name}")
        print(f"{'#'*80}")
        
        benchmark = SolverBenchmark(
            config['width'],
            config['height'],
            config['num_mines']
        )
        
        results = benchmark.compare_solvers(
            solvers,
            num_games=config['num_games'],
            seed_start=0
        )
        
        benchmark.print_results(results)
        benchmark.plot_results(
            results,
            save_path=f"benchmark_{config['width']}x{config['height']}.png"
        )
        
        all_difficulty_results[difficulty_name] = results
    
    print(f"\n\n{'='*80}")
    print("BENCHMARK TERMINÉ")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    run_full_benchmark()
