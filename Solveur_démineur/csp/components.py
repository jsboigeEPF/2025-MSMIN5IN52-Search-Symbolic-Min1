"""
Module de détection de composantes connexes dans le graphe de contraintes.

Permet de décomposer le problème CSP en sous-problèmes indépendants
pour un gain de performance exponentiel.
"""

from typing import List, Tuple, Set, Dict
from collections import defaultdict


class ComponentDetector:
    """Détecte les composantes connexes dans le graphe de contraintes."""
    
    def __init__(self):
        """Initialise le détecteur de composantes."""
        self.components = []
    
    def find_components(
        self,
        variables: List[Tuple[int, int]],
        constraints: List[Dict]
    ) -> List[Dict]:
        """
        Détecte les composantes connexes du graphe de contraintes.
        
        Deux variables sont dans la même composante si elles partagent
        une contrainte commune (directement ou indirectement).
        
        Args:
            variables: Liste des positions des variables (row, col)
            constraints: Liste des contraintes
            
        Returns:
            Liste de dictionnaires, un par composante:
            {
                'variables': List[Tuple[int, int]],
                'constraints': List[Dict]
            }
        """
        if not variables:
            return []
        
        # Construire le graphe d'adjacence des variables
        adjacency = self._build_adjacency_graph(variables, constraints)
        
        # Trouver les composantes connexes avec DFS
        visited = set()
        components = []
        
        for var in variables:
            if var not in visited:
                component_vars = self._dfs(var, adjacency, visited)
                
                # Récupérer les contraintes de cette composante
                component_constraints = self._get_component_constraints(
                    component_vars, constraints
                )
                
                components.append({
                    'variables': list(component_vars),
                    'constraints': component_constraints
                })
        
        self.components = components
        return components
    
    def _build_adjacency_graph(
        self,
        variables: List[Tuple[int, int]],
        constraints: List[Dict]
    ) -> Dict[Tuple[int, int], Set[Tuple[int, int]]]:
        """
        Construit le graphe d'adjacence des variables.
        
        Deux variables sont adjacentes si elles apparaissent
        dans la même contrainte.
        
        Args:
            variables: Liste des variables
            constraints: Liste des contraintes
            
        Returns:
            Dictionnaire {variable: set(voisins)}
        """
        adjacency = defaultdict(set)
        
        # Initialiser avec toutes les variables
        for var in variables:
            adjacency[var] = set()
        
        # Ajouter les connexions via les contraintes
        for constraint in constraints:
            vars_in_constraint = constraint.variables
            
            # Chaque paire de variables dans la contrainte est connectée
            for i, var1 in enumerate(vars_in_constraint):
                for var2 in vars_in_constraint[i+1:]:
                    adjacency[var1].add(var2)
                    adjacency[var2].add(var1)
        
        return adjacency
    
    def _dfs(
        self,
        start: Tuple[int, int],
        adjacency: Dict[Tuple[int, int], Set[Tuple[int, int]]],
        visited: Set[Tuple[int, int]]
    ) -> Set[Tuple[int, int]]:
        """
        Parcours en profondeur (DFS) pour trouver une composante.
        
        Args:
            start: Variable de départ
            adjacency: Graphe d'adjacence
            visited: Ensemble des variables déjà visitées
            
        Returns:
            Ensemble des variables de la composante
        """
        stack = [start]
        component = set()
        
        while stack:
            var = stack.pop()
            
            if var in visited:
                continue
            
            visited.add(var)
            component.add(var)
            
            # Ajouter les voisins non visités à la pile
            for neighbor in adjacency[var]:
                if neighbor not in visited:
                    stack.append(neighbor)
        
        return component
    
    def _get_component_constraints(
        self,
        component_vars: Set[Tuple[int, int]],
        all_constraints: List[Dict]
    ) -> List[Dict]:
        """
        Récupère les contraintes appartenant à une composante.
        
        Une contrainte appartient à une composante si toutes ses
        variables sont dans la composante.
        
        Args:
            component_vars: Variables de la composante
            all_constraints: Toutes les contraintes
            
        Returns:
            Liste des contraintes de la composante
        """
        component_constraints = []
        
        for constraint in all_constraints:
            vars_in_constraint = set(constraint.variables)
            
            # Si toutes les variables de la contrainte sont dans la composante
            if vars_in_constraint.issubset(component_vars):
                component_constraints.append(constraint)
        
        return component_constraints
    
    def get_num_components(self) -> int:
        """
        Retourne le nombre de composantes détectées.
        
        Returns:
            Nombre de composantes
        """
        return len(self.components)
    
    def get_component_sizes(self) -> List[int]:
        """
        Retourne la taille de chaque composante.
        
        Returns:
            Liste des tailles (nombre de variables)
        """
        return [len(comp['variables']) for comp in self.components]
    
    def get_statistics(self) -> Dict:
        """
        Retourne des statistiques sur les composantes.
        
        Returns:
            Dictionnaire de statistiques
        """
        sizes = self.get_component_sizes()
        
        return {
            'num_components': len(self.components),
            'components': self.components,
            'sizes': sizes,
            'max_size': max(sizes) if sizes else 0,
            'min_size': min(sizes) if sizes else 0,
            'avg_size': sum(sizes) / len(sizes) if sizes else 0
        }
