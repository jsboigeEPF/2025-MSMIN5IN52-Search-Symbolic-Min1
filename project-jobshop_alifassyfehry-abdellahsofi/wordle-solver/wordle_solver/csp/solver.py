"""
Module de résolution CSP avec OR-Tools CP-SAT.

Utilise Google OR-Tools pour modéliser et résoudre le problème Wordle
comme un problème de satisfaction de contraintes.
"""

from typing import Set, List, Optional
from ortools.sat.python import cp_model
from .constraint_manager import ConstraintManager
from .word_filter import WordFilter


class WordleCSPSolver:
    """
    Solveur CSP pour Wordle utilisant OR-Tools CP-SAT.
    
    Modélise chaque position du mot comme une variable de domaine
    et applique les contraintes pour trouver les mots valides.
    """
    
    def __init__(self, dictionary: Set[str]):
        """
        Initialise le solveur CSP.
        
        Args:
            dictionary: Ensemble de mots valides (5 lettres)
        """
        self.dictionary = {word.upper() for word in dictionary}
        self.word_filter = WordFilter(self.dictionary)
        
        # Créer un mapping lettre <-> entier pour OR-Tools
        all_letters = set()
        for word in self.dictionary:
            all_letters.update(word)
        
        self.letter_to_int = {letter: i for i, letter in enumerate(sorted(all_letters))}
        self.int_to_letter = {i: letter for letter, i in self.letter_to_int.items()}
    
    def solve(self, constraint_manager: ConstraintManager, max_solutions: int = 100) -> List[str]:
        """
        Résout le CSP et retourne les mots possibles.
        
        Note: Pour Wordle, le filtrage direct est souvent plus efficace que CP-SAT
        pour ce type de contraintes. Cette méthode est fournie pour démonstration.
        
        Args:
            constraint_manager: Gestionnaire de contraintes
            max_solutions: Nombre maximum de solutions à retourner
            
        Returns:
            Liste de mots valides
        """
        # Pour Wordle, le filtrage direct est plus efficace
        # On utilise donc WordFilter plutôt que de modéliser tout dans CP-SAT
        valid_words = self.word_filter.filter_by_constraints(constraint_manager)
        return sorted(list(valid_words))[:max_solutions]
    
    def solve_with_cpsat(self, constraint_manager: ConstraintManager, max_solutions: int = 100) -> List[str]:
        """
        Résout en utilisant vraiment CP-SAT (pour démonstration).
        
        Cette approche est plus lente que le filtrage direct mais montre
        comment modéliser le problème avec OR-Tools.
        
        Args:
            constraint_manager: Gestionnaire de contraintes
            max_solutions: Nombre maximum de solutions
            
        Returns:
            Liste de mots valides
        """
        model = cp_model.CpModel()
        
        # Variables : une pour chaque position (0-4)
        positions = []
        for i in range(5):
            # Domaine = toutes les lettres possibles à cette position
            possible_letters = self._get_possible_letters_at_position(i, constraint_manager)
            if not possible_letters:
                return []  # Aucune solution possible
            
            letter_values = [self.letter_to_int[letter] for letter in possible_letters]
            var = model.NewIntVarFromDomain(
                cp_model.Domain.FromValues(letter_values),
                f'pos_{i}'
            )
            positions.append(var)
        
        # Contrainte : positions correctes (vertes)
        for pos, letter in constraint_manager.correct_positions.items():
            model.Add(positions[pos] == self.letter_to_int[letter])
        
        # Contraintes : lettres présentes (jaunes)
        for letter, forbidden_positions in constraint_manager.present_letters.items():
            letter_int = self.letter_to_int[letter]
            
            # La lettre doit apparaître au moins une fois
            at_least_one = []
            for i in range(5):
                at_least_one.append(positions[i] == letter_int)
            model.AddBoolOr(at_least_one)
            
            # Mais pas aux positions interdites
            for forbidden_pos in forbidden_positions:
                model.Add(positions[forbidden_pos] != letter_int)
        
        # Contrainte : lettres absentes (grises)
        for letter in constraint_manager.absent_letters:
            if letter in self.letter_to_int:
                letter_int = self.letter_to_int[letter]
                for pos in range(5):
                    model.Add(positions[pos] != letter_int)
        
        # Résoudre et collecter les solutions
        solver = cp_model.CpSolver()
        solution_collector = WordSolutionCollector(
            positions, 
            self.int_to_letter,
            self.dictionary,
            max_solutions
        )
        
        solver.parameters.enumerate_all_solutions = True
        solver.parameters.max_time_in_seconds = 10.0
        
        status = solver.Solve(model, solution_collector)
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return solution_collector.solutions
        else:
            return []
    
    def _get_possible_letters_at_position(
        self, 
        position: int, 
        constraint_manager: ConstraintManager
    ) -> Set[str]:
        """
        Détermine les lettres possibles à une position donnée.
        
        Args:
            position: Position (0-4)
            constraint_manager: Gestionnaire de contraintes
            
        Returns:
            Ensemble de lettres possibles
        """
        # Si position déjà connue
        if position in constraint_manager.correct_positions:
            return {constraint_manager.correct_positions[position]}
        
        # Sinon, toutes les lettres sauf celles interdites
        all_letters = set(self.letter_to_int.keys())
        
        # Retirer les lettres absentes
        all_letters -= constraint_manager.absent_letters
        
        # Retirer les lettres jaunes à cette position
        for letter, forbidden_positions in constraint_manager.present_letters.items():
            if position in forbidden_positions:
                all_letters.discard(letter)
        
        return all_letters
    
    def get_statistics(self) -> dict:
        """
        Retourne des statistiques sur le dictionnaire.
        
        Returns:
            Dictionnaire avec stats
        """
        return {
            'total_words': len(self.dictionary),
            'current_candidates': len(self.word_filter.current_candidates),
            'letters': len(self.letter_to_int),
            'average_word_length': 5,  # Fixe pour Wordle
        }


class WordSolutionCollector(cp_model.CpSolverSolutionCallback):
    """
    Callback pour collecter les solutions trouvées par CP-SAT.
    """
    
    def __init__(
        self, 
        position_vars: List[cp_model.IntVar],
        int_to_letter: dict[int, str],
        dictionary: Set[str],
        max_solutions: int
    ):
        """
        Initialise le collecteur.
        
        Args:
            position_vars: Variables CP-SAT pour chaque position
            int_to_letter: Mapping entier -> lettre
            dictionary: Dictionnaire pour valider les mots
            max_solutions: Nombre max de solutions à collecter
        """
        super().__init__()
        self.position_vars = position_vars
        self.int_to_letter = int_to_letter
        self.dictionary = dictionary
        self.max_solutions = max_solutions
        self.solutions: List[str] = []
    
    def on_solution_callback(self):
        """Appelé quand une solution est trouvée."""
        # Reconstruire le mot
        word = ''.join([
            self.int_to_letter[self.Value(var)]
            for var in self.position_vars
        ])
        
        # Vérifier que c'est un mot valide du dictionnaire
        if word in self.dictionary:
            self.solutions.append(word)
        
        # Arrêter si on a assez de solutions
        if len(self.solutions) >= self.max_solutions:
            self.StopSearch()


class HybridSolver:
    """
    Solveur hybride combinant filtrage efficace et CP-SAT si nécessaire.
    
    Utilise le filtrage direct pour la majorité des cas,
    et CP-SAT uniquement pour des contraintes complexes.
    """
    
    def __init__(self, dictionary: Set[str]):
        """
        Initialise le solveur hybride.
        
        Args:
            dictionary: Ensemble de mots valides
        """
        self.word_filter = WordFilter(dictionary)
        self.csp_solver = WordleCSPSolver(dictionary)
    
    def solve(
        self, 
        constraint_manager: ConstraintManager, 
        use_cpsat: bool = False
    ) -> Set[str]:
        """
        Résout le problème en choisissant la meilleure approche.
        
        Args:
            constraint_manager: Gestionnaire de contraintes
            use_cpsat: Forcer l'utilisation de CP-SAT
            
        Returns:
            Ensemble de mots valides
        """
        if use_cpsat:
            solutions = self.csp_solver.solve_with_cpsat(constraint_manager)
            return set(solutions)
        else:
            # Le filtrage est généralement plus rapide pour Wordle
            return self.word_filter.filter_by_constraints(constraint_manager)
    
    def get_possible_words(
        self, 
        constraint_manager: ConstraintManager,
        limit: Optional[int] = None
    ) -> List[str]:
        """
        Retourne les mots possibles triés alphabétiquement.
        
        Args:
            constraint_manager: Gestionnaire de contraintes
            limit: Nombre maximum de mots à retourner (None = tous)
            
        Returns:
            Liste de mots possibles
        """
        words = self.solve(constraint_manager, use_cpsat=False)
        sorted_words = sorted(list(words))
        
        if limit:
            return sorted_words[:limit]
        return sorted_words
    
    def count_possible_words(self, constraint_manager: ConstraintManager) -> int:
        """Retourne le nombre de mots possibles."""
        return len(self.solve(constraint_manager, use_cpsat=False))
