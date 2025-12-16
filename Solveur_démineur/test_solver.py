"""
Test simple pour vérifier le fonctionnement du solveur sans GUI.
"""

from game.board import Board, GameState
from solvers.ortools_solver import ORToolsSolver


def test_simple_game():
    """Test une partie simple en mode console."""
    print("=== Test du Solveur CSP ===\n")
    
    # Créer une petite grille
    board = Board(width=5, height=5, num_mines=3, seed=42)
    solver = ORToolsSolver(board, max_solutions=100)
    
    print("Grille : 5x5 avec 3 mines")
    print()
    
    move_count = 0
    max_moves = 30  # Limite pour éviter les boucles infinies
    
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
        print(f"Coup {move_count}: ({row}, {col}) - Probabilité: {prob:.1%}")
        
        # Jouer le coup
        success = solver.make_move(row, col)
        
        if not success:
            print("  💥 Mine touchée!")
            break
        
        print(f"  ✓ Cases révélées: {board.num_revealed}/{board.width * board.height - board.num_mines}")
    
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
    print(f"\nStatistiques:")
    print(f"  Coups joués: {stats['num_moves']}")
    print(f"  Déductions logiques: {stats['num_logical_deductions']}")
    print(f"  Paris probabilistes: {stats['num_probability_guesses']}")
    
    if stats['num_probability_guesses'] > 0:
        ratio = stats['num_logical_deductions'] / stats['num_probability_guesses']
        print(f"  Ratio logique/paris: {ratio:.2f}")
    
    print("\n✅ Test terminé avec succès!")
    return board.game_state == GameState.WON


if __name__ == "__main__":
    test_simple_game()
