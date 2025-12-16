"""
Script principal - Solveur de Démineur avec visualisation.

Lance le jeu avec le solveur CSP OR-Tools et l'interface Pygame.
"""

import sys
import time
from game.board import Board, GameState
from game.visualizer import Visualizer
from solvers.ortools_solver import ORToolsSolver
from solvers.simple_solver import SimpleSolver


def main():
    """Fonction principale."""
    print("=== Solveur de Démineur CSP ===")
    print()
    
    # Choix du solveur
    print("Choisissez le solveur :")
    print("  1. Solveur CSP Complet (OR-Tools) - Plus intelligent, plus lent")
    print("  2. Solveur Simple (AFN/AMN) - Rapide, baseline")
    print()
    
    choice = input("Votre choix (1 ou 2, défaut=1) : ").strip()
    
    if choice == "2":
        SOLVER_CLASS = SimpleSolver
        SOLVER_NAME = "Simple (AFN/AMN)"
    else:
        SOLVER_CLASS = ORToolsSolver
        SOLVER_NAME = "CSP OR-Tools"
    
    print(f"\n✅ Solveur sélectionné : {SOLVER_NAME}\n")
    
    # Configuration de la partie
    # Débutant : 9x9, 10 mines
    # Intermédiaire : 16x16, 40 mines
    # Expert : 30x16, 99 mines
    
    WIDTH = 9
    HEIGHT = 9
    NUM_MINES = 10
    DIFFICULTY = "Débutant"
    
    print(f"Difficulté : {DIFFICULTY}")
    print(f"Grille : {WIDTH}x{HEIGHT}")
    print(f"Mines : {NUM_MINES}")
    print()
    print("Contrôles :")
    print("  ESPACE : Prochain coup (mode pas-à-pas)")
    print("  A : Mode automatique (à implémenter)")
    print("  P : Activer/désactiver les probabilités")
    print("  R : Redémarrer (à implémenter)")
    print("  Q : Quitter")
    print()
    
    # Créer la grille et le solveur
    board = Board(WIDTH, HEIGHT, NUM_MINES, seed=42)
    
    if SOLVER_CLASS == ORToolsSolver:
        solver = ORToolsSolver(board, max_solutions=1000)
    else:
        solver = SimpleSolver(board)
    
    # Créer le visualiseur
    visualizer = Visualizer(board, cell_size=50)
    
    # Boucle de jeu
    running = True
    auto_mode = False
    
    visualizer.draw()
    
    while running:
        # Gérer les événements
        if not visualizer.handle_events():
            running = False
            break
        
        # Attendre l'action de l'utilisateur (mode pas-à-pas)
        if not auto_mode:
            if not visualizer.wait_for_next_step():
                running = False
                break
        
        # Vérifier si le jeu est terminé
        if board.is_game_over():
            visualizer.draw()
            
            if board.game_state == GameState.WON:
                print("\n🎉 VICTOIRE ! 🎉")
            else:
                print("\n💥 DÉFAITE 💥")
            
            stats = solver.get_stats()
            print(f"\nStatistiques :")
            print(f"  Coups joués : {stats['num_moves']}")
            print(f"  Déductions logiques : {stats['num_logical_deductions']}")
            print(f"  Paris probabilistes : {stats['num_probability_guesses']}")
            print(f"  Ratio logique/paris : {stats['num_logical_deductions']}/{stats['num_probability_guesses']}")
            
            # Attendre avant de fermer
            print("\nAppuyez sur Q pour quitter...")
            waiting = True
            while waiting:
                if not visualizer.handle_events():
                    waiting = False
                time.sleep(0.1)
            
            break
        
        # Obtenir le prochain coup du solveur
        print(f"\nCoup {solver.num_moves + 1}...")
        
        try:
            next_move = solver.get_next_move()
            
            if next_move is None:
                print("Aucun coup disponible (erreur).")
                break
            
            row, col = next_move
            probabilities = solver.get_probabilities()
            
            # Afficher les probabilités
            visualizer.set_probabilities(probabilities)
            visualizer.set_selected_cell(row, col)
            visualizer.draw()
            
            if (row, col) in probabilities:
                prob = probabilities[(row, col)]
                print(f"Choix : ({row}, {col}) - Probabilité de mine : {prob:.2%}")
            else:
                print(f"Choix : ({row}, {col}) - Première case")
            
            # Petit délai pour voir la sélection
            time.sleep(0.3)
            
            # Jouer le coup
            success = solver.make_move(row, col)
            
            if not success:
                print(f"💥 Mine touchée en ({row}, {col}) !")
            
            # Mettre à jour l'affichage
            visualizer.selected_cell = None
            visualizer.draw()
            
        except Exception as e:
            print(f"Erreur lors du calcul : {e}")
            import traceback
            traceback.print_exc()
            break
        
        # Petit délai en mode automatique
        if auto_mode:
            time.sleep(0.5)
    
    # Fermer proprement
    visualizer.close()
    print("\nAu revoir !")


if __name__ == "__main__":
    main()
