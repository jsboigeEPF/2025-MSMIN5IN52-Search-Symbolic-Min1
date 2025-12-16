"""
Script de démonstration des différents solveurs avec visualisation interactive.

Permet de:
- Lancer un solveur avec visualisation en temps réel
- Comparer les solveurs côte à côte
- Voir les probabilités, heatmaps, et composantes en overlay
"""

import argparse
import os
from game.board import Board
from game.interactive_visualizer import InteractiveVisualizer
from solvers.simple_solver import SimpleSolver
from solvers.ortools_solver import ORToolsSolver
from solvers.optimized_solver import OptimizedSolver
from solvers.supervised_solver import SupervisedSolver, HybridSolver


def get_available_solvers():
    """
    Retourne les solveurs disponibles.
    
    Returns:
        Dict des solveurs disponibles
    """
    solvers = {
        'simple': {
            'class': SimpleSolver,
            'name': 'Simple (AFN/AMN)',
            'kwargs': {}
        },
        'csp': {
            'class': ORToolsSolver,
            'name': 'CSP (OR-Tools)',
            'kwargs': {}
        },
        'optimized': {
            'class': OptimizedSolver,
            'name': 'CSP Optimisé',
            'kwargs': {}
        },
    }
    
    # Ajouter solveurs ML si modèles disponibles
    model_path_easy = "training/models/easy_cnn/best_model.pth"
    model_path_medium = "training/models/medium_cnn/best_model.pth"
    model_path_hard = "training/models/hard_cnn/best_model.pth"
    
    # Chercher un modèle disponible
    model_path = None
    for path in [model_path_medium, model_path_easy, model_path_hard]:
        if os.path.exists(path):
            model_path = path
            break
    
    if model_path:
        solvers['supervised'] = {
            'class': SupervisedSolver,
            'name': 'Supervisé (CNN)',
            'kwargs': {'model_path': model_path}
        }
        
        solvers['hybrid'] = {
            'class': HybridSolver,
            'name': 'Hybride (CSP + CNN)',
            'kwargs': {'model_path': model_path}
        }
    
    return solvers


def run_interactive_demo(
    solver_type: str = 'optimized',
    width: int = 16,
    height: int = 16,
    num_mines: int = 40,
    seed: int = None,
    cell_size: int = 40
):
    """
    Lance une démo interactive.
    
    Args:
        solver_type: Type de solveur à utiliser
        width: Largeur de la grille
        height: Hauteur de la grille
        num_mines: Nombre de mines
        seed: Seed pour la génération (None = aléatoire)
        cell_size: Taille des cellules en pixels
    """
    # Créer le board
    board = Board(width, height, num_mines, seed=seed)
    
    # Obtenir le solveur
    available_solvers = get_available_solvers()
    
    if solver_type not in available_solvers:
        print(f"❌ Solveur '{solver_type}' non disponible.")
        print(f"   Solveurs disponibles: {', '.join(available_solvers.keys())}")
        return
    
    solver_config = available_solvers[solver_type]
    solver = solver_config['class'](board, **solver_config['kwargs'])
    
    print(f"\n🎮 Lancement de la démo interactive")
    print(f"   Solveur: {solver_config['name']}")
    print(f"   Grille: {width}x{height} avec {num_mines} mines")
    if seed is not None:
        print(f"   Seed: {seed}")
    
    print(f"\n⌨️  Contrôles:")
    print(f"   ESPACE  - Pause/Reprendre")
    print(f"   S       - Un coup à la fois (step)")
    print(f"   P       - Toggle probabilités")
    print(f"   H       - Toggle heatmap")
    print(f"   C       - Toggle composantes connexes")
    print(f"   +/-     - Vitesse")
    print(f"   R       - Reset")
    print(f"   ESC     - Quitter")
    
    # Créer et lancer le visualiseur
    visualizer = InteractiveVisualizer(
        board,
        solver,
        cell_size=cell_size
    )
    
    visualizer.run()


def list_solvers():
    """Affiche les solveurs disponibles."""
    solvers = get_available_solvers()
    
    print("\n🤖 Solveurs disponibles:\n")
    
    for key, config in solvers.items():
        print(f"  • {key:<12} - {config['name']}")
    
    print()


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description='Démo interactive du solveur de démineur',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Lancer avec le solveur optimisé (par défaut)
  python demo.py
  
  # Lancer avec le solveur simple
  python demo.py --solver simple
  
  # Débutant (9x9, 10 mines)
  python demo.py --width 9 --height 9 --mines 10
  
  # Expert (30x16, 99 mines)
  python demo.py --width 30 --height 16 --mines 99
  
  # Avec un seed spécifique pour reproductibilité
  python demo.py --seed 42
  
  # Lister les solveurs disponibles
  python demo.py --list
        """
    )
    
    parser.add_argument(
        '--solver',
        type=str,
        default='optimized',
        help='Type de solveur (simple, csp, optimized, supervised, hybrid)'
    )
    
    parser.add_argument(
        '--width',
        type=int,
        default=16,
        help='Largeur de la grille (défaut: 16)'
    )
    
    parser.add_argument(
        '--height',
        type=int,
        default=16,
        help='Hauteur de la grille (défaut: 16)'
    )
    
    parser.add_argument(
        '--mines',
        type=int,
        default=40,
        help='Nombre de mines (défaut: 40)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Seed pour la génération (défaut: aléatoire)'
    )
    
    parser.add_argument(
        '--cell-size',
        type=int,
        default=40,
        help='Taille des cellules en pixels (défaut: 40)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='Lister les solveurs disponibles'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_solvers()
        return
    
    run_interactive_demo(
        solver_type=args.solver,
        width=args.width,
        height=args.height,
        num_mines=args.mines,
        seed=args.seed,
        cell_size=args.cell_size
    )


if __name__ == "__main__":
    main()
