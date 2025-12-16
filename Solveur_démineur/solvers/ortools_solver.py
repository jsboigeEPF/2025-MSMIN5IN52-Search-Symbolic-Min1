"""
Solveur CSP complet utilisant OR-Tools CP-SAT.

Utilise la propagation de contraintes et l'énumération de solutions
pour calculer des probabilités exactes et prendre les meilleures décisions.
"""

from typing import Optional, Tuple, Dict, List
from ortools.sat.python import cp_model
from game.board import Board, CellState
from solvers.base_solver import BaseSolver
from csp.constraint_builder import ConstraintBuilder
from csp.probability import ProbabilityCalculator


class ORToolsSolver(BaseSolver):
    """Solveur CSP avec OR-Tools CP-SAT."""
    
    def __init__(self, board: Board, max_solutions: int = 1000):
        """
        Initialise le solveur OR-Tools.
        
        Args:
            board: Grille de démineur
            max_solutions: Nombre maximum de solutions à énumérer
        """
        super().__init__(board)
        self.max_solutions = max_solutions
        self.constraint_builder = ConstraintBuilder(board)
        self.prob_calculator = ProbabilityCalculator()
        self.last_probabilities = {}
    
    def get_next_move(self) -> Optional[Tuple[int, int]]:
        """
        Calcule le prochain coup optimal.
        
        Returns:
            Position (row, col) à révéler, ou None si impossible
        """
        # Construire les contraintes
        variables, constraints = self.constraint_builder.build_constraints()
        
        if not variables:
            # Aucune case cachée, jeu terminé
            return None
        
        # Simplifier et trouver les cases évidentes
        variables, constraints, certain_mines, certain_safe = \
            self.constraint_builder.simplify_constraints(variables, constraints)
        
        # Si des cases sûres sont trouvées, en choisir une
        if certain_safe:
            self.num_logical_deductions += 1
            self.last_probabilities = {pos: 0.0 for pos in certain_safe}
            return list(certain_safe)[0]
        
        # Si des mines certaines sont trouvées, les marquer (mais pas de révélation)
        if certain_mines:
            for row, col in certain_mines:
                self.board.flag(row, col)
        
        # Cas particulier : première case (aucune contrainte)
        if not constraints:
            # Choisir une case au hasard (préférer les coins/bords)
            self.num_probability_guesses += 1
            return self._choose_first_cell()
        
        # Résoudre le CSP et énumérer les solutions
        solutions = self._solve_csp(variables, constraints)
        
        if not solutions:
            # Aucune solution trouvée, problème incohérent
            # Prendre une case au hasard parmi les restantes
            if variables:
                self.num_probability_guesses += 1
                return variables[0]
            return None
        
        # Calculer les probabilités
        probabilities = self.prob_calculator.calculate_probabilities(variables, solutions)
        self.last_probabilities = probabilities
        
        # Trouver la meilleure case (probabilité minimale)
        certain_safe, certain_mines = self.prob_calculator.get_certain_cells(probabilities)
        
        if certain_safe:
            self.num_logical_deductions += 1
            return list(certain_safe)[0]
        
        # Sinon, choisir la case avec la probabilité la plus faible
        self.num_probability_guesses += 1
        return self.prob_calculator.find_best_move(probabilities)
    
    def get_probabilities(self) -> Dict[Tuple[int, int], float]:
        """
        Retourne les probabilités calculées lors du dernier coup.
        
        Returns:
            Dictionnaire {(row, col): probability}
        """
        return self.last_probabilities
    
    def _solve_csp(self, variables: List[Tuple[int, int]], 
                   constraints: List) -> List[Dict[Tuple[int, int], int]]:
        """
        Résout le CSP et énumère toutes les solutions.
        
        Args:
            variables: Liste des positions des variables
            constraints: Liste des contraintes
            
        Returns:
            Liste des solutions (assignations)
        """
        if not variables:
            return []
        
        # Créer le modèle CP-SAT
        model = cp_model.CpModel()
        
        # Créer les variables booléennes
        var_dict = {}
        for pos in variables:
            var_dict[pos] = model.NewBoolVar(f'cell_{pos[0]}_{pos[1]}')
        
        # Ajouter les contraintes
        for constraint in constraints:
            constraint_vars = [var_dict[pos] for pos in constraint.variables if pos in var_dict]
            if constraint_vars:
                model.Add(sum(constraint_vars) == constraint.total)
        
        # Optionnel : ajouter la contrainte globale du nombre de mines
        # (peut ralentir, à activer si nécessaire)
        # global_constraint = self.constraint_builder.build_global_constraint(variables)
        # global_vars = [var_dict[pos] for pos in global_constraint.variables if pos in var_dict]
        # if global_vars:
        #     model.Add(sum(global_vars) == global_constraint.total)
        
        # Énumérer les solutions
        solver = cp_model.CpSolver()
        solution_collector = SolutionCollector(var_dict, self.max_solutions)
        solver.parameters.enumerate_all_solutions = True
        solver.parameters.max_time_in_seconds = 1.0  # Timeout de 1 seconde
        
        status = solver.Solve(model, solution_collector)
        
        return solution_collector.solutions
    
    def _choose_first_cell(self) -> Tuple[int, int]:
        """
        Choisit la première case à révéler (stratégie heuristique).
        
        Returns:
            Position (row, col)
        """
        hidden = self.board.get_hidden_cells()
        
        if not hidden:
            return None
        
        # Stratégie : choisir une case au centre ou un coin
        # (plus susceptible d'ouvrir de grandes zones)
        center_row = self.board.height // 2
        center_col = self.board.width // 2
        
        # Essayer le centre
        if (center_row, center_col) in hidden:
            return (center_row, center_col)
        
        # Sinon, choisir la première case disponible
        return hidden[0]


class SolutionCollector(cp_model.CpSolverSolutionCallback):
    """Callback pour collecter toutes les solutions du CSP."""
    
    def __init__(self, var_dict: Dict[Tuple[int, int], cp_model.IntVar], max_solutions: int):
        """
        Initialise le collecteur de solutions.
        
        Args:
            var_dict: Dictionnaire {position: variable CP-SAT}
            max_solutions: Nombre maximum de solutions à collecter
        """
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.var_dict = var_dict
        self.max_solutions = max_solutions
        self.solutions = []
    
    def on_solution_callback(self):
        """Appelé pour chaque solution trouvée."""
        if len(self.solutions) >= self.max_solutions:
            self.StopSearch()
            return
        
        solution = {}
        for pos, var in self.var_dict.items():
            solution[pos] = self.Value(var)
        
        self.solutions.append(solution)
