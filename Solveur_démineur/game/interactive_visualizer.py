"""
Visualiseur interactif amélioré pour le démineur.

Affiche les probabilités, heatmaps, et processus de pensée des solveurs
en temps réel avec mode pas-à-pas.
"""

import pygame
import numpy as np
import sys
from typing import Optional, Dict, Tuple, List
from game.board import Board, CellState, GameState
from solvers.base_solver import BaseSolver


class InteractiveVisualizer:
    """Visualiseur interactif avec overlay des probabilités et heatmaps."""
    
    # Couleurs
    COLOR_BG = (40, 44, 52)
    COLOR_PANEL = (33, 37, 43)
    COLOR_HIDDEN = (97, 108, 130)
    COLOR_REVEALED = (220, 220, 220)
    COLOR_MINE = (231, 76, 60)
    COLOR_FLAG = (241, 196, 15)
    COLOR_SELECTED = (46, 204, 113)
    COLOR_TEXT = (236, 240, 241)
    COLOR_GRID = (60, 64, 72)
    COLOR_PROB_SAFE = (46, 204, 113, 180)
    COLOR_PROB_DANGER = (231, 76, 60, 180)
    
    # Couleurs chiffres
    NUMBER_COLORS = {
        1: (52, 152, 219),
        2: (46, 204, 113),
        3: (231, 76, 60),
        4: (142, 68, 173),
        5: (243, 156, 18),
        6: (26, 188, 156),
        7: (0, 0, 0),
        8: (149, 165, 166)
    }
    
    def __init__(
        self,
        board: Board,
        solver: Optional[BaseSolver] = None,
        cell_size: int = 40
    ):
        """
        Initialise le visualiseur.
        
        Args:
            board: Grille de démineur
            solver: Solveur optionnel
            cell_size: Taille d'une case en pixels
        """
        pygame.init()
        
        self.board = board
        self.solver = solver
        self.cell_size = cell_size
        
        # Dimensions
        self.grid_width = board.width * cell_size
        self.grid_height = board.height * cell_size
        self.panel_width = 300
        self.window_width = self.grid_width + self.panel_width
        self.window_height = max(self.grid_height, 600)
        
        # Créer la fenêtre
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Minesweeper AI Visualizer")
        
        # Fonts
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 36)
        self.font_cell = pygame.font.Font(None, int(cell_size * 0.7))
        
        # État
        self.running = True
        self.paused = True
        self.selected_cell = None
        self.show_probabilities = True
        self.show_heatmap = True
        self.show_components = False
        self.auto_play_speed = 500  # ms entre coups
        self.last_auto_play = 0
        
        # Statistiques
        self.move_history = []
        self.probability_history = []
        
        # Clock
        self.clock = pygame.time.Clock()
    
    def run(self):
        """Boucle principale du visualiseur."""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
        
        pygame.quit()
    
    def handle_events(self):
        """Gère les événements clavier/souris."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Pause/Resume
                    self.paused = not self.paused
                
                elif event.key == pygame.K_s:
                    # Step: un coup
                    if self.solver and self.paused:
                        self.play_one_move()
                
                elif event.key == pygame.K_p:
                    # Toggle probabilités
                    self.show_probabilities = not self.show_probabilities
                
                elif event.key == pygame.K_h:
                    # Toggle heatmap
                    self.show_heatmap = not self.show_heatmap
                
                elif event.key == pygame.K_c:
                    # Toggle composantes
                    self.show_components = not self.show_components
                
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    # Accélérer
                    self.auto_play_speed = max(100, self.auto_play_speed - 100)
                
                elif event.key == pygame.K_MINUS:
                    # Ralentir
                    self.auto_play_speed = min(2000, self.auto_play_speed + 100)
                
                elif event.key == pygame.K_r:
                    # Reset
                    self.reset_game()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_click(event.pos, event.button)
    
    def handle_click(self, pos: Tuple[int, int], button: int):
        """Gère les clics souris."""
        x, y = pos
        
        # Clic dans la grille
        if x < self.grid_width and y < self.grid_height:
            col = x // self.cell_size
            row = y // self.cell_size
            
            if button == 1:  # Clic gauche
                self.board.reveal(row, col)
            elif button == 3:  # Clic droit
                self.board.flag(row, col)
            
            self.selected_cell = (row, col)
    
    def update(self):
        """Met à jour l'état du jeu."""
        if not self.paused and self.solver:
            current_time = pygame.time.get_ticks()
            
            if current_time - self.last_auto_play >= self.auto_play_speed:
                self.play_one_move()
                self.last_auto_play = current_time
    
    def play_one_move(self):
        """Joue un coup avec le solveur."""
        if self.board.game_state == GameState.ONGOING and self.solver:
            move = self.solver.get_next_move()
            
            if move:
                self.selected_cell = move
                success = self.board.reveal(move[0], move[1])
                
                # Enregistrer dans l'historique
                probs = self.solver.get_probabilities()
                prob = probs.get(move, 0.0) if probs else 0.0
                
                self.move_history.append({
                    'move': move,
                    'success': success,
                    'probability': prob
                })
            else:
                self.paused = True  # Arrêter si plus de coup
    
    def reset_game(self):
        """Réinitialise le jeu."""
        # Créer une nouvelle grille avec le même seed +1
        new_seed = (self.board.seed + 1) if self.board.seed is not None else None
        self.board = Board(
            self.board.width,
            self.board.height,
            self.board.num_mines,
            seed=new_seed
        )
        
        # Réinitialiser le solveur
        if self.solver:
            self.solver.board = self.board
            self.solver.reset_stats()
        
        # Réinitialiser l'historique
        self.move_history = []
        self.probability_history = []
        self.selected_cell = None
        self.paused = True
    
    def render(self):
        """Affiche tout."""
        self.screen.fill(self.COLOR_BG)
        
        # Grille
        self.render_grid()
        
        # Overlay probabilités/heatmap
        if self.solver and (self.show_probabilities or self.show_heatmap):
            self.render_probability_overlay()
        
        # Overlay composantes
        if self.show_components and hasattr(self.solver, 'get_component_stats'):
            self.render_components_overlay()
        
        # Panel de contrôle
        self.render_control_panel()
        
        pygame.display.flip()
    
    def render_grid(self):
        """Affiche la grille de jeu."""
        for r in range(self.board.height):
            for c in range(self.board.width):
                x = c * self.cell_size
                y = r * self.cell_size
                
                # Couleur de fond
                state = self.board.cell_states[r, c]
                
                if (r, c) == self.selected_cell:
                    color = self.COLOR_SELECTED
                elif state == CellState.HIDDEN:
                    color = self.COLOR_HIDDEN
                elif state == CellState.FLAGGED:
                    color = self.COLOR_FLAG
                else:  # REVEALED
                    color = self.COLOR_REVEALED
                
                # Dessiner la case
                pygame.draw.rect(self.screen, color, (x, y, self.cell_size, self.cell_size))
                pygame.draw.rect(self.screen, self.COLOR_GRID, (x, y, self.cell_size, self.cell_size), 1)
                
                # Contenu
                if state == CellState.REVEALED:
                    if self.board.mines[r, c]:
                        # Mine
                        pygame.draw.circle(
                            self.screen,
                            self.COLOR_MINE,
                            (x + self.cell_size // 2, y + self.cell_size // 2),
                            self.cell_size // 4
                        )
                    elif self.board.values[r, c] > 0:
                        # Numéro
                        value = self.board.values[r, c]
                        text = self.font_cell.render(str(value), True, self.NUMBER_COLORS[value])
                        text_rect = text.get_rect(center=(x + self.cell_size // 2, y + self.cell_size // 2))
                        self.screen.blit(text, text_rect)
                
                elif state == CellState.FLAGGED:
                    # Drapeau (triangle)
                    points = [
                        (x + self.cell_size // 4, y + self.cell_size // 4),
                        (x + 3 * self.cell_size // 4, y + self.cell_size // 2),
                        (x + self.cell_size // 4, y + 3 * self.cell_size // 4)
                    ]
                    pygame.draw.polygon(self.screen, self.COLOR_MINE, points)
    
    def render_probability_overlay(self):
        """Affiche l'overlay des probabilités."""
        if not self.solver:
            return
        
        probs = self.solver.get_probabilities()
        
        if not probs:
            return
        
        # Surface transparente
        overlay = pygame.Surface((self.grid_width, self.grid_height), pygame.SRCALPHA)
        
        for (r, c), prob in probs.items():
            x = c * self.cell_size
            y = r * self.cell_size
            
            if self.show_heatmap:
                # Heatmap: interpoler couleur selon probabilité
                if prob < 0.5:
                    # Vert -> Jaune
                    t = prob * 2  # 0 -> 1
                    color = (
                        int(46 + (255 - 46) * t),
                        int(204 + (255 - 204) * t),
                        int(113 + (150 - 113) * t),
                        150
                    )
                else:
                    # Jaune -> Rouge
                    t = (prob - 0.5) * 2  # 0 -> 1
                    color = (
                        255,
                        int(255 - (255 - 76) * t),
                        int(150 - 150 * t),
                        150
                    )
                
                pygame.draw.rect(overlay, color, (x, y, self.cell_size, self.cell_size))
            
            if self.show_probabilities:
                # Texte probabilité
                prob_text = f"{prob*100:.0f}"
                text = self.font_small.render(prob_text, True, (255, 255, 255))
                text_rect = text.get_rect(center=(x + self.cell_size // 2, y + self.cell_size // 2))
                
                # Ombre
                shadow = self.font_small.render(prob_text, True, (0, 0, 0))
                shadow_rect = shadow.get_rect(center=(x + self.cell_size // 2 + 1, y + self.cell_size // 2 + 1))
                overlay.blit(shadow, shadow_rect)
                overlay.blit(text, text_rect)
        
        self.screen.blit(overlay, (0, 0))
    
    def render_components_overlay(self):
        """Affiche les composantes connexes."""
        if not hasattr(self.solver, 'component_detector'):
            return
        
        components = self.solver.component_detector.components
        
        if not components:
            return
        
        # Couleurs aléatoires par composante
        colors = [
            (255, 100, 100, 100),
            (100, 255, 100, 100),
            (100, 100, 255, 100),
            (255, 255, 100, 100),
            (255, 100, 255, 100),
            (100, 255, 255, 100)
        ]
        
        overlay = pygame.Surface((self.grid_width, self.grid_height), pygame.SRCALPHA)
        
        for idx, comp in enumerate(components):
            color = colors[idx % len(colors)]
            
            for (r, c) in comp['variables']:
                x = c * self.cell_size
                y = r * self.cell_size
                pygame.draw.rect(overlay, color, (x, y, self.cell_size, self.cell_size))
        
        self.screen.blit(overlay, (0, 0))
    
    def render_control_panel(self):
        """Affiche le panneau de contrôle à droite."""
        panel_x = self.grid_width
        y_offset = 20
        
        # Fond du panel
        pygame.draw.rect(
            self.screen,
            self.COLOR_PANEL,
            (panel_x, 0, self.panel_width, self.window_height)
        )
        
        # Titre
        title = self.font_large.render("Controls", True, self.COLOR_TEXT)
        self.screen.blit(title, (panel_x + 20, y_offset))
        y_offset += 50
        
        # État du jeu
        state_text = {
            GameState.ONGOING: "🎮 En cours",
            GameState.WON: "✅ Gagné!",
            GameState.LOST: "💥 Perdu"
        }[self.board.game_state]
        
        state = self.font_medium.render(state_text, True, self.COLOR_TEXT)
        self.screen.blit(state, (panel_x + 20, y_offset))
        y_offset += 40
        
        # Statistiques
        stats = [
            f"Cases révélées: {self.board.num_revealed}/{self.board.width * self.board.height - self.board.num_mines}",
            f"Mines: {self.board.num_mines}",
            f"",
            f"Mode: {'▶️ Auto' if not self.paused else '⏸️ Pause'}",
            f"Vitesse: {1000/self.auto_play_speed:.1f} coups/s",
            f"",
            "Affichage:",
            f"  [P] Probabilités: {'✓' if self.show_probabilities else '✗'}",
            f"  [H] Heatmap: {'✓' if self.show_heatmap else '✗'}",
            f"  [C] Composantes: {'✓' if self.show_components else '✗'}",
        ]
        
        for line in stats:
            text = self.font_small.render(line, True, self.COLOR_TEXT)
            self.screen.blit(text, (panel_x + 20, y_offset))
            y_offset += 25
        
        # Statistiques solveur
        if self.solver:
            y_offset += 10
            solver_stats = self.solver.get_stats()
            
            solver_info = [
                "Statistiques solveur:",
                f"  Coups: {solver_stats['num_moves']}",
                f"  Logiques: {solver_stats['num_logical_deductions']}",
                f"  Probabilistes: {solver_stats['num_probability_guesses']}",
            ]
            
            if hasattr(self.solver, 'get_component_stats'):
                comp_stats = self.solver.get_component_stats()
                if comp_stats:
                    solver_info.extend([
                        f"",
                        f"Composantes: {comp_stats.get('num_components', 0)}",
                        f"Taille max: {comp_stats.get('max_size', 0)}",
                    ])
            
            for line in solver_info:
                text = self.font_small.render(line, True, self.COLOR_TEXT)
                self.screen.blit(text, (panel_x + 20, y_offset))
                y_offset += 25
        
        # Contrôles
        y_offset = self.window_height - 200
        
        controls = [
            "Contrôles:",
            "[SPACE] Play/Pause",
            "[S] Step (1 coup)",
            "[R] Reset",
            "[+/-] Vitesse",
            "[P] Probabilités",
            "[H] Heatmap",
            "[C] Composantes",
        ]
        
        for line in controls:
            text = self.font_small.render(line, True, self.COLOR_TEXT)
            self.screen.blit(text, (panel_x + 20, y_offset))
            y_offset += 25


def visualize_solver(
    board: Board,
    solver: BaseSolver,
    cell_size: int = 40
):
    """
    Fonction utilitaire pour visualiser un solveur.
    
    Args:
        board: Grille de jeu
        solver: Solveur à visualiser
        cell_size: Taille des cases
    """
    viz = InteractiveVisualizer(board, solver, cell_size)
    viz.run()


if __name__ == "__main__":
    # Test du visualiseur
    from game.board import Board
    from solvers.ortools_solver import ORToolsSolver
    
    # Créer une grille
    board = Board(16, 16, 40, seed=42)
    
    # Créer un solveur
    solver = ORToolsSolver(board)
    
    # Lancer le visualiseur
    visualize_solver(board, solver)
