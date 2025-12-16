"""
Test du solveur simple (AFN/AMN) en mode console.
"""

from game.board import Board, GameState
from solvers.simple_solver import SimpleSolver


def test_simple_solver():
    """Test une partie simple avec le solveur baseline."""
    print("=== Test du Solveur Simple (AFN/AMN) ===\n")
    
    # Créer une grille
    board = Board(width=9, height=9, num_mines=10, seed=42)
    solver = SimpleSolver(board)
    
    print("Grille : 9x9 avec 10 mines")
    print("Solveur : Règles simples AFN/AMN\n")
    
    move_count = 0
    max_moves = 100
    
    while not board.is_game_over() and move_count < max_moves:
        move_count += 1
        
        # Obtenir le prochain coup
        next_move = solver.get_next_move()
        
        if next_move is None:
            print("Aucun coup disponible.")
            break
        
        row, col = next_move
        probabilities = solver.get_probabilities()
        
        # Afficher le coup
        prob = probabilities.get((row, col), 0.0)
        print(f"Coup {move_count:2d}: ({row}, {col}) - Probabilité: {prob:.1%}", end="")
        
        # Jouer le coup
        success = solver.make_move(row, col)
        
        if not success:
            print(" 💥 Mine touchée!")
            break
        
        print(f" ✓ Cases révélées: {board.num_revealed}/{board.width * board.height - board.num_mines}")
    
    print()
    
    # Résultat
    if board.game_state == GameState.WON:
        print("🎉 VICTOIRE !")
    elif board.game_state == GameState.LOST:
        print("💥 DÉFAITE")
    else:
        print("⚠️ Limite de coups atteinte")
    
    # Statistiques
    stats = solver.get_stats()
    print(f"\n📊 Statistiques:")
    print(f"  Coups joués         : {stats['num_moves']}")
    print(f"  Déductions logiques : {stats['num_logical_deductions']}")
    print(f"  Paris probabilistes : {stats['num_probability_guesses']}")
    
    if stats['num_probability_guesses'] > 0:
        ratio = stats['num_logical_deductions'] / stats['num_probability_guesses']
        print(f"  Ratio logique/paris : {ratio:.2f}")
    
    print("\n✅ Test terminé !")
    return board.game_state == GameState.WON


if __name__ == "__main__":
    test_simple_solver()
