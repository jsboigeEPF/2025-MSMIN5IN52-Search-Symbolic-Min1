"""
Visualiseur Pygame pour le démineur.

Interface graphique interactive avec affichage des probabilités
et mode pas-à-pas pour le solveur.
"""

import pygame
import sys
from typing import Optional, Dict, Tuple
from game.board import Board, CellState, GameState


class Visualizer:
    """Visualiseur graphique pour le démineur."""
    
    # Couleurs
    COLOR_BG = (189, 189, 189)
    COLOR_HIDDEN = (128, 128, 128)
    COLOR_REVEALED = (220, 220, 220)
    COLOR_MINE = (255, 0, 0)
    COLOR_FLAG = (255, 165, 0)
    COLOR_SELECTED = (0, 255, 0)
    COLOR_TEXT = (0, 0, 0)
    COLOR_GRID = (100, 100, 100)
    COLOR_PROB_LOW = (200, 255, 200)
    COLOR_PROB_MED = (255, 255, 150)
    COLOR_PROB_HIGH = (255, 150, 150)
    
    # Couleurs pour les chiffres
    NUMBER_COLORS = {
        1: (0, 0, 255),
        2: (0, 128, 0),
        3: (255, 0, 0),
        4: (0, 0, 128),
        5: (128, 0, 0),
        6: (0, 128, 128),
        7: (0, 0, 0),
        8: (128, 128, 128)
    }
    
    def __init__(self, board: Board, cell_size: int = 40):
        """
        Initialise le visualiseur.
        
        Args:
            board: Grille de démineur à afficher
            cell_size: Taille d'une case en pixels
        """
        self.board = board
        self.cell_size = cell_size
        
        # Dimensions de la fenêtre
        self.info_height = 80  # Hauteur de la zone d'info
        self.width = board.width * cell_size
        self.height = board.height * cell_size + self.info_height
        
        # Initialisation de Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Solveur de Démineur CSP")
        
        # Polices
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 36)
        
        # État de visualisation
        self.probabilities: Dict[Tuple[int, int], float] = {}
        self.selected_cell: Optional[Tuple[int, int]] = None
        self.show_probabilities = True
        self.paused = False
        
        # FPS
        self.clock = pygame.time.Clock()
        self.fps = 60
    
    def set_probabilities(self, probabilities: Dict[Tuple[int, int], float]):
        """
        Définit les probabilités à afficher sur les cases.
        
        Args:
            probabilities: Dictionnaire {(row, col): probability}
        """
        self.probabilities = probabilities
    
    def set_selected_cell(self, row: int, col: int):
        """
        Définit la case sélectionnée par le solveur.
        
        Args:
            row: Ligne de la case
            col: Colonne de la case
        """
        self.selected_cell = (row, col)
    
    def draw(self):
        """Dessine la grille complète."""
        self.screen.fill(self.COLOR_BG)
        
        # Dessiner la grille
        self._draw_grid()
        
        # Dessiner les informations
        self._draw_info()
        
        pygame.display.flip()
    
    def _draw_grid(self):
        """Dessine la grille de jeu."""
        for row in range(self.board.height):
            for col in range(self.board.width):
                x = col * self.cell_size
                y = row * self.cell_size + self.info_height
                
                self._draw_cell(row, col, x, y)
        
        # Dessiner les lignes de la grille
        for i in range(self.board.height + 1):
            y = i * self.cell_size + self.info_height
            pygame.draw.line(self.screen, self.COLOR_GRID, (0, y), (self.width, y), 1)
        
        for i in range(self.board.width + 1):
            x = i * self.cell_size
            pygame.draw.line(self.screen, self.COLOR_GRID, (x, self.info_height), (x, self.height), 1)
    
    def _draw_cell(self, row: int, col: int, x: int, y: int):
        """Dessine une case individuelle."""
        state = self.board.cell_states[row, col]
        rect = pygame.Rect(x + 1, y + 1, self.cell_size - 2, self.cell_size - 2)
        
        # Case révélée
        if state == CellState.REVEALED:
            if self.board.mines[row, col]:
                # Mine révélée (défaite)
                pygame.draw.rect(self.screen, self.COLOR_MINE, rect)
                self._draw_text('💣', x, y, self.font_large, (0, 0, 0))
            else:
                # Case révélée normale
                pygame.draw.rect(self.screen, self.COLOR_REVEALED, rect)
                value = self.board.values[row, col]
                if value > 0:
                    color = self.NUMBER_COLORS.get(value, self.COLOR_TEXT)
                    self._draw_text(str(value), x, y, self.font_large, color)
        
        # Case cachée
        elif state == CellState.HIDDEN:
            # Couleur de fond selon probabilité
            if self.show_probabilities and (row, col) in self.probabilities:
                prob = self.probabilities[(row, col)]
                color = self._get_probability_color(prob)
                pygame.draw.rect(self.screen, color, rect)
                
                # Afficher le pourcentage
                text = f"{int(prob * 100)}%"
                self._draw_text(text, x, y, self.font_small, self.COLOR_TEXT)
            else:
                pygame.draw.rect(self.screen, self.COLOR_HIDDEN, rect)
            
            # Highlight si sélectionnée
            if self.selected_cell == (row, col):
                pygame.draw.rect(self.screen, self.COLOR_SELECTED, rect, 3)
        
        # Case marquée
        elif state == CellState.FLAGGED:
            pygame.draw.rect(self.screen, self.COLOR_FLAG, rect)
            self._draw_text('🚩', x, y, self.font_large, (0, 0, 0))
    
    def _get_probability_color(self, prob: float) -> Tuple[int, int, int]:
        """Retourne une couleur en fonction de la probabilité."""
        if prob < 0.2:
            return self.COLOR_PROB_LOW
        elif prob < 0.5:
            return self.COLOR_PROB_MED
        else:
            return self.COLOR_PROB_HIGH
    
    def _draw_text(self, text: str, x: int, y: int, font: pygame.font.Font, color: Tuple[int, int, int]):
        """Dessine du texte centré dans une case."""
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(x + self.cell_size // 2, y + self.cell_size // 2))
        self.screen.blit(surface, rect)
    
    def _draw_info(self):
        """Dessine la zone d'information en haut."""
        info_rect = pygame.Rect(0, 0, self.width, self.info_height)
        pygame.draw.rect(self.screen, (240, 240, 240), info_rect)
        pygame.draw.line(self.screen, self.COLOR_GRID, (0, self.info_height), (self.width, self.info_height), 2)
        
        # État du jeu
        if self.board.game_state == GameState.WON:
            status_text = "🎉 VICTOIRE ! 🎉"
            color = (0, 150, 0)
        elif self.board.game_state == GameState.LOST:
            status_text = "💥 DÉFAITE 💥"
            color = (200, 0, 0)
        else:
            status_text = "En cours..."
            color = (0, 0, 0)
        
        status_surface = self.font_large.render(status_text, True, color)
        self.screen.blit(status_surface, (10, 10))
        
        # Statistiques
        revealed = self.board.num_revealed
        total = self.board.width * self.board.height - self.board.num_mines
        stats_text = f"Révélées: {revealed}/{total} | Mines: {self.board.num_mines}"
        stats_surface = self.font_small.render(stats_text, True, (0, 0, 0))
        self.screen.blit(stats_surface, (10, 50))
        
        # Contrôles
        controls_text = "ESPACE: Coup suivant | A: Auto | P: Proba ON/OFF | R: Restart | Q: Quitter"
        controls_surface = self.font_small.render(controls_text, True, (100, 100, 100))
        controls_rect = controls_surface.get_rect(right=self.width - 10, top=50)
        self.screen.blit(controls_surface, controls_rect)
    
    def handle_events(self) -> bool:
        """
        Gère les événements Pygame.
        
        Returns:
            False si l'utilisateur veut quitter, True sinon
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return False
                elif event.key == pygame.K_p:
                    self.show_probabilities = not self.show_probabilities
        
        return True
    
    def wait_for_next_step(self) -> bool:
        """
        Attend une action de l'utilisateur pour passer au coup suivant.
        
        Returns:
            False si l'utilisateur veut quitter, True sinon
        """
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        return False
                    elif event.key == pygame.K_SPACE:
                        return True
                    elif event.key == pygame.K_p:
                        self.show_probabilities = not self.show_probabilities
                        self.draw()
            
            self.clock.tick(30)
        
        return True
    
    def update(self):
        """Met à jour l'affichage."""
        self.draw()
        self.clock.tick(self.fps)
    
    def close(self):
        """Ferme Pygame."""
        pygame.quit()
