"""
Comparaison entre le solveur simple et le solveur CSP.

Lance plusieurs parties avec chaque solveur et compare les performances.
"""

from game.board import Board, GameState
from solvers.simple_solver import SimpleSolver
from solvers.ortools_solver import ORToolsSolver
import time


def play_game(solver_class, width, height, num_mines, seed):
    """
    Joue une partie avec un solveur donné.
    
    Returns:
        Tuple (victoire, stats, temps_total)
    """
    board = Board(width, height, num_mines, seed)
    solver = solver_class(board)
    
    start_time = time.time()
    max_moves = 1000
    move_count = 0
    
    while not board.is_game_over() and move_count < max_moves:
        move_count += 1
        next_move = solver.get_next_move()
        
        if next_move is None:
            break
        
        row, col = next_move
        success = solver.make_move(row, col)
        
        if not success:
            break
    
    end_time = time.time()
    total_time = end_time - start_time
    
    won = board.game_state == GameState.WON
    stats = solver.get_stats()
    
    return won, stats, total_time


def compare_solvers(num_games=10, width=9, height=9, num_mines=10):
    """
    Compare les deux solveurs sur plusieurs parties.
    """
    print("=" * 70)
    print("🎯 COMPARAISON DES SOLVEURS")
    print("=" * 70)
    print(f"\nConfiguration : {width}×{height}, {num_mines} mines")
    print(f"Nombre de parties : {num_games}\n")
    
    solvers = [
        ("Simple (AFN/AMN)", SimpleSolver),
        ("CSP OR-Tools", ORToolsSolver)
    ]
    
    for solver_name, solver_class in solvers:
        print(f"\n{'─' * 70}")
        print(f"📊 Test de : {solver_name}")
        print('─' * 70)
        
        victories = 0
        total_moves = 0
        total_deductions = 0
        total_guesses = 0
        total_time = 0.0
        
        for seed in range(num_games):
            won, stats, game_time = play_game(solver_class, width, height, num_mines, seed)
            
            if won:
                victories += 1
                result = "✅ Victoire"
            else:
                result = "❌ Défaite"
            
            total_moves += stats['num_moves']
            total_deductions += stats['num_logical_deductions']
            total_guesses += stats['num_probability_guesses']
            total_time += game_time
            
            print(f"  Partie {seed+1:2d}: {result} | "
                  f"Coups: {stats['num_moves']:2d} | "
                  f"Déductions: {stats['num_logical_deductions']:2d} | "
                  f"Paris: {stats['num_probability_guesses']:2d} | "
                  f"Temps: {game_time*1000:.1f}ms")
        
        # Statistiques globales
        win_rate = (victories / num_games) * 100
        avg_moves = total_moves / num_games
        avg_deductions = total_deductions / num_games
        avg_guesses = total_guesses / num_games
        avg_time = (total_time / num_games) * 1000
        
        print(f"\n  📈 Résumé {solver_name}:")
        print(f"     Taux de victoire    : {win_rate:.1f}% ({victories}/{num_games})")
        print(f"     Coups moyens        : {avg_moves:.1f}")
        print(f"     Déductions moyennes : {avg_deductions:.1f}")
        print(f"     Paris moyens        : {avg_guesses:.1f}")
        print(f"     Temps moyen         : {avg_time:.1f}ms")
        
        if avg_guesses > 0:
            ratio = avg_deductions / avg_guesses
            print(f"     Ratio déd./paris    : {ratio:.2f}")
    
    print(f"\n{'=' * 70}")
    print("✅ Comparaison terminée !")
    print('=' * 70)


if __name__ == "__main__":
    print("\n🎮 Solveur de Démineur - Comparaison de Performances\n")
    
    # Test sur grilles débutant
    compare_solvers(num_games=20, width=9, height=9, num_mines=10)
    
    print("\n" + "="*70)
    print("💡 Observations attendues :")
    print("="*70)
    print("• Solveur Simple : Plus rapide (~1-5ms) mais taux victoire ~60-70%")
    print("• Solveur CSP    : Plus lent (~50-200ms) mais taux victoire ~85-95%")
    print("• Le CSP trouve plus de déductions logiques grâce aux contraintes croisées")
    print("="*70 + "\n")
