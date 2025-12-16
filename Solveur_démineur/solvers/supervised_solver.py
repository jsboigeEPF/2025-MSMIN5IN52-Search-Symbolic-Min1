"""
Solveur utilisant l'apprentissage supervisé (CNN).

Utilise un modèle CNN entraîné pour prédire les meilleurs coups.
"""

import torch
import numpy as np
from typing import Optional, Tuple, Dict
from game.board import Board, CellState
from solvers.base_solver import BaseSolver
from training.model import MinesweeperCNN, MinesweeperResNet
import os


class SupervisedSolver(BaseSolver):
    """Solveur basé sur l'apprentissage supervisé."""
    
    def __init__(
        self,
        board: Board,
        model_path: str,
        model_type: str = 'cnn',
        device: str = 'cuda'
    ):
        """
        Initialise le solveur supervisé.
        
        Args:
            board: Grille de démineur
            model_path: Chemin vers le modèle entraîné (.pth)
            model_type: 'cnn' ou 'resnet'
            device: 'cuda' ou 'cpu'
        """
        super().__init__(board)
        
        # Device
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        # Charger le modèle
        self.model_type = model_type
        self.model = self._load_model(model_path)
        self.model.eval()
        
        # Cache des prédictions
        self.last_scores = {}
        self.last_probabilities = {}
    
    def _load_model(self, model_path: str) -> torch.nn.Module:
        """
        Charge le modèle entraîné.
        
        Args:
            model_path: Chemin du checkpoint
            
        Returns:
            Modèle chargé
        """
        # Créer l'architecture
        if self.model_type == 'resnet':
            model = MinesweeperResNet(self.board.height, self.board.width)
        else:
            model = MinesweeperCNN(self.board.height, self.board.width)
        
        # Charger les poids
        if os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            model.load_state_dict(checkpoint['model_state_dict'])
            print(f"✅ Modèle chargé: {model_path}")
            print(f"   Epoch: {checkpoint.get('epoch', '?')}")
            print(f"   Val Loss: {checkpoint.get('val_loss', '?'):.4f}")
            print(f"   Val Acc: {checkpoint.get('val_acc', '?'):.2f}%")
        else:
            print(f"⚠️  Modèle non trouvé: {model_path}")
            print(f"   Utilisation d'un modèle non entraîné")
        
        return model.to(self.device)
    
    def get_next_move(self) -> Optional[Tuple[int, int]]:
        """
        Calcule le prochain coup avec le CNN.
        
        Returns:
            Position (row, col) à révéler
        """
        # Encoder l'état actuel
        state = self._encode_state()
        
        # Masque des coups valides (cases cachées)
        valid_mask = self._get_valid_mask()
        
        if valid_mask.sum() == 0:
            return None  # Aucun coup valide
        
        # Prédiction du modèle
        with torch.no_grad():
            # Forward
            state_tensor = torch.from_numpy(state).unsqueeze(0).to(self.device)
            valid_tensor = torch.from_numpy(valid_mask).to(self.device)
            
            scores = self.model(state_tensor).squeeze(0)  # (H*W,)
            
            # Appliquer le masque
            scores_flat = scores.cpu().numpy()
            valid_flat = valid_mask.flatten()
            
            # Masquer les cases invalides
            scores_masked = np.where(valid_flat, scores_flat, -1e9)
            
            # Trouver le meilleur coup
            best_idx = scores_masked.argmax()
            row = best_idx // self.board.width
            col = best_idx % self.board.width
            
            # Sauvegarder pour visualisation
            self._save_scores(scores_flat, valid_flat)
        
        self.num_moves += 1
        return (row, col)
    
    def get_probabilities(self) -> Dict[Tuple[int, int], float]:
        """
        Retourne les probabilités/scores du dernier calcul.
        
        Returns:
            Dictionnaire {(row, col): probability}
        """
        return self.last_probabilities.copy()
    
    def get_scores_map(self) -> np.ndarray:
        """
        Retourne la carte des scores pour visualisation.
        
        Returns:
            Array (H, W) avec les scores
        """
        if not self.last_scores:
            return np.zeros((self.board.height, self.board.width))
        
        scores_map = np.zeros((self.board.height, self.board.width))
        for (r, c), score in self.last_scores.items():
            scores_map[r, c] = score
        
        return scores_map
    
    def _encode_state(self) -> np.ndarray:
        """
        Encode l'état actuel de la grille.
        
        Returns:
            Array (4, H, W)
        """
        h, w = self.board.height, self.board.width
        state = np.zeros((4, h, w), dtype=np.float32)
        
        # Channel 0: Valeurs normalisées
        for r in range(h):
            for c in range(w):
                if self.board.cell_states[r, c] == CellState.REVEALED:
                    state[0, r, c] = self.board.values[r, c] / 8.0
        
        # Channel 1: Masque révélé
        for r in range(h):
            for c in range(w):
                if self.board.cell_states[r, c] == CellState.REVEALED:
                    state[1, r, c] = 1.0
        
        # Channel 2: Drapeaux
        for r in range(h):
            for c in range(w):
                if self.board.cell_states[r, c] == CellState.FLAGGED:
                    state[2, r, c] = 1.0
        
        # Channel 3: Frontière
        for r in range(h):
            for c in range(w):
                if self.board.cell_states[r, c] == CellState.HIDDEN:
                    # Vérifier voisins révélés
                    has_revealed = False
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < h and 0 <= nc < w:
                                if self.board.cell_states[nr, nc] == CellState.REVEALED:
                                    has_revealed = True
                                    break
                        if has_revealed:
                            break
                    
                    if has_revealed:
                        state[3, r, c] = 1.0
        
        return state
    
    def _get_valid_mask(self) -> np.ndarray:
        """
        Crée un masque des cases valides (cachées).
        
        Returns:
            Array (H, W) binaire
        """
        h, w = self.board.height, self.board.width
        mask = np.zeros((h, w), dtype=np.float32)
        
        for r in range(h):
            for c in range(w):
                if self.board.cell_states[r, c] == CellState.HIDDEN:
                    mask[r, c] = 1.0
        
        return mask
    
    def _save_scores(self, scores_flat: np.ndarray, valid_flat: np.ndarray):
        """
        Sauvegarde les scores pour visualisation.
        
        Args:
            scores_flat: Scores linéarisés
            valid_flat: Masque valide linéarisé
        """
        self.last_scores = {}
        self.last_probabilities = {}
        
        # Convertir scores en probabilités (softmax sur cases valides)
        valid_scores = scores_flat[valid_flat.astype(bool)]
        
        if len(valid_scores) > 0:
            # Softmax
            exp_scores = np.exp(valid_scores - valid_scores.max())
            probabilities = exp_scores / exp_scores.sum()
            
            # Reconstruire
            prob_idx = 0
            for idx in range(len(scores_flat)):
                row = idx // self.board.width
                col = idx % self.board.width
                
                if valid_flat[idx] > 0:
                    self.last_scores[(row, col)] = float(scores_flat[idx])
                    self.last_probabilities[(row, col)] = float(probabilities[prob_idx])
                    prob_idx += 1


class HybridSolver(BaseSolver):
    """
    Solveur hybride combinant CSP et CNN.
    
    Utilise d'abord les déductions logiques CSP, puis le CNN pour
    les situations ambiguës.
    """
    
    def __init__(
        self,
        board: Board,
        model_path: str,
        model_type: str = 'cnn',
        certainty_threshold: float = 0.1
    ):
        """
        Initialise le solveur hybride.
        
        Args:
            board: Grille de démineur
            model_path: Chemin du modèle CNN
            model_type: Type de modèle
            certainty_threshold: Seuil pour utiliser CSP vs CNN
        """
        super().__init__(board)
        
        # Importer ici pour éviter dépendance circulaire
        from solvers.ortools_solver import ORToolsSolver
        
        self.csp_solver = ORToolsSolver(board)
        self.cnn_solver = SupervisedSolver(board, model_path, model_type)
        self.threshold = certainty_threshold
        self.last_solver_used = None
    
    def get_next_move(self) -> Optional[Tuple[int, int]]:
        """
        Choisit entre CSP et CNN selon la situation.
        
        Returns:
            Position (row, col) à révéler
        """
        # Essayer d'abord le CSP
        move = self.csp_solver.get_next_move()
        probs = self.csp_solver.get_probabilities()
        
        if move and probs:
            prob = probs.get(move, 1.0)
            
            # Si probabilité faible (case quasi-certaine), utiliser CSP
            if prob <= self.threshold:
                self.last_solver_used = 'csp'
                self.num_logical_deductions += 1
                return move
        
        # Sinon, utiliser le CNN pour les situations ambiguës
        self.last_solver_used = 'cnn'
        self.num_probability_guesses += 1
        return self.cnn_solver.get_next_move()
    
    def get_probabilities(self) -> Dict[Tuple[int, int], float]:
        """Retourne les probabilités du dernier solveur utilisé."""
        if self.last_solver_used == 'csp':
            return self.csp_solver.get_probabilities()
        else:
            return self.cnn_solver.get_probabilities()
    
    def get_last_solver(self) -> str:
        """Retourne le dernier solveur utilisé."""
        return self.last_solver_used or 'none'


def create_solver(
    board: Board,
    solver_type: str = 'supervised',
    model_path: str = None,
    **kwargs
) -> BaseSolver:
    """
    Factory pour créer un solveur.
    
    Args:
        board: Grille de jeu
        solver_type: 'supervised' ou 'hybrid'
        model_path: Chemin du modèle
        **kwargs: Arguments additionnels
        
    Returns:
        Solveur créé
    """
    if solver_type == 'hybrid':
        return HybridSolver(board, model_path, **kwargs)
    else:
        return SupervisedSolver(board, model_path, **kwargs)
