"""
Génération de dataset d'entraînement pour l'apprentissage supervisé.

Utilise le solveur CSP expert pour générer des exemples (état, meilleur coup).
"""

import numpy as np
import pickle
import os
import sys

# Ajouter le dossier racine au path pour permettre les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Tuple, Dict
from tqdm import tqdm
from game.board import Board, CellState, GameState
from solvers.optimized_solver import OptimizedSolver


class DatasetGenerator:
    """Génère des données d'entraînement depuis un solveur expert."""
    
    def __init__(
        self,
        width: int = 16,
        height: int = 16,
        num_mines: int = 40,
        save_dir: str = "training/data"
    ):
        """
        Initialise le générateur.
        
        Args:
            width: Largeur des grilles
            height: Hauteur des grilles
            num_mines: Nombre de mines
            save_dir: Dossier de sauvegarde
        """
        self.width = width
        self.height = height
        self.num_mines = num_mines
        self.save_dir = save_dir
        
        os.makedirs(save_dir, exist_ok=True)
    
    def generate_dataset(
        self,
        num_games: int = 1000,
        seed_start: int = 0
    ) -> List[Dict]:
        """
        Génère un dataset en jouant des parties avec le solveur expert.
        
        Args:
            num_games: Nombre de parties à jouer
            seed_start: Seed de départ pour la génération
            
        Returns:
            Liste de tuples (état, coup_optimal, probabilités)
        """
        dataset = []
        
        print(f"🎮 Génération de {num_games} parties...")
        
        for game_idx in tqdm(range(num_games)):
            seed = seed_start + game_idx
            board = Board(self.width, self.height, self.num_mines, seed=seed)
            solver = OptimizedSolver(board)
            
            # Jouer la partie et enregistrer les exemples
            game_examples = self._play_and_record(board, solver)
            dataset.extend(game_examples)
        
        print(f"✅ {len(dataset)} exemples générés")
        return dataset
    
    def _play_and_record(
        self,
        board: Board,
        solver: OptimizedSolver
    ) -> List[Dict]:
        """
        Joue une partie et enregistre les décisions.
        
        Args:
            board: Grille de jeu
            solver: Solveur expert
            
        Returns:
            Liste d'exemples de la partie
        """
        examples = []
        
        while board.game_state == GameState.ONGOING:
            # Capturer l'état actuel
            state = self._encode_state(board)
            
            # Obtenir le coup optimal du solveur
            move = solver.get_next_move()
            
            if move is None:
                break
            
            # Obtenir les probabilités
            probabilities = solver.get_probabilities()
            
            # Enregistrer l'exemple si c'est une vraie décision
            # (pas le premier coup aléatoire)
            if probabilities:
                example = {
                    'state': state,
                    'move': move,
                    'probabilities': probabilities,
                    'is_certain': probabilities.get(move, 1.0) == 0.0
                }
                examples.append(example)
            
            # Jouer le coup
            success = board.reveal(move[0], move[1])
            
            if not success:
                # Mine touchée, partie perdue
                break
        
        return examples
    
    def _encode_state(self, board: Board) -> np.ndarray:
        """
        Encode l'état de la grille pour le réseau.
        
        Channels:
        0: Cases révélées (valeurs 0-8 normalisées)
        1: Masque binaire (révélé=1, caché=0)
        2: Mines marquées (drapeaux)
        3: Frontière (cases cachées adjacentes à cases révélées)
        
        Args:
            board: Grille de jeu
            
        Returns:
            Tensor numpy (4, height, width)
        """
        h, w = board.height, board.width
        state = np.zeros((4, h, w), dtype=np.float32)
        
        # Channel 0: Valeurs normalisées
        for r in range(h):
            for c in range(w):
                if board.cell_states[r, c] == CellState.REVEALED:
                    state[0, r, c] = board.values[r, c] / 8.0
        
        # Channel 1: Masque révélé
        for r in range(h):
            for c in range(w):
                if board.cell_states[r, c] == CellState.REVEALED:
                    state[1, r, c] = 1.0
        
        # Channel 2: Drapeaux
        for r in range(h):
            for c in range(w):
                if board.cell_states[r, c] == CellState.FLAGGED:
                    state[2, r, c] = 1.0
        
        # Channel 3: Frontière (cases cachées avec voisin révélé)
        for r in range(h):
            for c in range(w):
                if board.cell_states[r, c] == CellState.HIDDEN:
                    # Vérifier si adjacent à une case révélée
                    has_revealed_neighbor = False
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < h and 0 <= nc < w:
                                if board.cell_states[nr, nc] == CellState.REVEALED:
                                    has_revealed_neighbor = True
                                    break
                        if has_revealed_neighbor:
                            break
                    
                    if has_revealed_neighbor:
                        state[3, r, c] = 1.0
        
        return state
    
    def save_dataset(self, dataset: List[Dict], filename: str):
        """
        Sauvegarde le dataset sur disque.
        
        Args:
            dataset: Dataset à sauvegarder
            filename: Nom du fichier
        """
        filepath = os.path.join(self.save_dir, filename)
        with open(filepath, 'wb') as f:
            pickle.dump(dataset, f)
        print(f"💾 Dataset sauvegardé: {filepath}")
    
    def load_dataset(self, filename: str) -> List[Dict]:
        """
        Charge un dataset depuis le disque.
        
        Args:
            filename: Nom du fichier
            
        Returns:
            Dataset chargé
        """
        filepath = os.path.join(self.save_dir, filename)
        with open(filepath, 'rb') as f:
            dataset = pickle.load(f)
        print(f"📂 Dataset chargé: {filepath} ({len(dataset)} exemples)")
        return dataset
    
    def generate_and_save(
        self,
        num_games: int = 1000,
        filename: str = "minesweeper_dataset.pkl",
        seed_start: int = 0
    ):
        """
        Génère et sauvegarde un dataset.
        
        Args:
            num_games: Nombre de parties
            filename: Nom du fichier de sauvegarde
            seed_start: Seed de départ
        """
        dataset = self.generate_dataset(num_games, seed_start)
        self.save_dataset(dataset, filename)
        
        # Statistiques
        certain_moves = sum(1 for ex in dataset if ex['is_certain'])
        print(f"\n📊 Statistiques:")
        print(f"  - Total exemples: {len(dataset)}")
        print(f"  - Coups certains: {certain_moves} ({100*certain_moves/len(dataset):.1f}%)")
        print(f"  - Coups probabilistes: {len(dataset)-certain_moves} ({100*(len(dataset)-certain_moves)/len(dataset):.1f}%)")


def generate_multiple_datasets():
    """Génère des datasets pour différentes difficultés."""
    
    # Dataset débutant (9x9, 10 mines)
    print("\n" + "="*60)
    print("🔰 NIVEAU DÉBUTANT")
    print("="*60)
    gen_easy = DatasetGenerator(width=9, height=9, num_mines=10)
    gen_easy.generate_and_save(num_games=500, filename="dataset_easy.pkl", seed_start=0)
    
    # Dataset intermédiaire (16x16, 40 mines)
    print("\n" + "="*60)
    print("⚡ NIVEAU INTERMÉDIAIRE")
    print("="*60)
    gen_medium = DatasetGenerator(width=16, height=16, num_mines=40)
    gen_medium.generate_and_save(num_games=1000, filename="dataset_medium.pkl", seed_start=1000)
    
    # Dataset expert (30x16, 99 mines)
    print("\n" + "="*60)
    print("💀 NIVEAU EXPERT")
    print("="*60)
    gen_hard = DatasetGenerator(width=30, height=16, num_mines=99)
    gen_hard.generate_and_save(num_games=500, filename="dataset_hard.pkl", seed_start=2000)


if __name__ == "__main__":
    generate_multiple_datasets()
