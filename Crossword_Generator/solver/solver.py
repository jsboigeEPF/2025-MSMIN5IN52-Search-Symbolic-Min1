# -*- coding: utf-8 -*-
"""
Solveur CSP pour les mots-croisés utilisant OR-Tools CP-SAT.
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict
from ortools.sat.python import cp_model
import time
import random

from .models import Slot, Intersection
from .grid import CrosswordGrid
from .dictionary import WordDictionary
from .definitions import DefinitionService


class CrosswordSolver:
    """
    Solveur de mots-croisés utilisant OR-Tools CP-SAT.
    Modélisation CSP:
    - Variables: choix d'un mot pour chaque slot
    - Domaines: mots du dictionnaire de la bonne longueur
    - Contraintes: lettres identiques aux intersections
    
    Optimisations:
    - Pré-filtrage des mots selon les intersections (arc-consistency)
    - Limitation du nombre de mots par slot
    - Index par lettre/position pour filtrage rapide
    - Filtrage optionnel par définitions disponibles
    """
    
    # Limite de mots par slot pour accélérer la résolution
    MAX_WORDS_PER_SLOT = 500
    
    def __init__(self, grid: CrosswordGrid, dictionary: WordDictionary, 
                 max_words_per_slot: int = None,
                 definition_service: DefinitionService = None,
                 require_definitions: bool = False):
        """
        Args:
            grid: Grille de mots-croisés
            dictionary: Dictionnaire de mots
            max_words_per_slot: Limite de mots par slot
            definition_service: Service de définitions (optionnel)
            require_definitions: Si True, n'utilise que les mots avec définition
        """
        self.grid = grid
        self.dictionary = dictionary
        self.model = cp_model.CpModel()
        self.slot_vars: Dict[int, cp_model.IntVar] = {}
        self.slot_words: Dict[int, List[str]] = {}  # slot_id -> liste de mots possibles
        self.max_words = max_words_per_slot or self.MAX_WORDS_PER_SLOT
        self.definition_service = definition_service
        self.require_definitions = require_definitions
        self._excluded_words: Set[str] = set()  # Mots à exclure (sans définition)
    
    def exclude_words(self, words: Set[str]):
        """Exclut des mots de la recherche (utile pour retry sans certains mots)"""
        self._excluded_words.update(words)
    
    def _filter_words_with_definitions(self, words: List[str], max_to_check: int = 200) -> List[str]:
        """
        Filtre les mots pour ne garder que ceux ayant une définition.
        Vérifie un nombre limité de mots pour la performance.
        """
        if not self.definition_service:
            return words
        
        words_with_def = []
        checked = 0
        
        for word in words:
            if word in self._excluded_words:
                continue
                
            checked += 1
            
            # Vérifier dans le cache d'abord (rapide)
            if word.upper() in self.definition_service.cache:
                if self.definition_service.cache[word.upper()]:
                    words_with_def.append(word)
                continue
            
            # Si on a assez de mots, arrêter de vérifier les APIs
            if len(words_with_def) >= self.max_words:
                break
                
            # Vérifier via API (plus lent) - limiter le nombre
            if checked <= max_to_check:
                defn = self.definition_service.get_definition(word, max_length=100)
                if defn:
                    words_with_def.append(word)
        
        return words_with_def
    
    def build_model(self, use_arc_consistency: bool = True) -> bool:
        """
        Construit le modèle CP-SAT.
        
        Args:
            use_arc_consistency: Si True, pré-filtre les mots selon les intersections
            
        Retourne False si le modèle est trivialement impossible.
        """
        print("\n🔧 Construction du modèle CP-SAT...")
        
        # Phase 1: Collecte initiale des mots possibles (avec limite)
        for slot in self.grid.slots:
            words = self.dictionary.get_words_limited(slot.length, self.max_words * 2)
            
            # Exclure les mots blacklistés
            if self._excluded_words:
                words = [w for w in words if w not in self._excluded_words]
            
            if not words:
                print(f"❌ Aucun mot de longueur {slot.length} pour {slot}")
                return False
            
            # Phase 1b: Filtrer par définitions si demandé
            if self.require_definitions and self.definition_service:
                print(f"  🔍 Vérification définitions pour slot {slot.id} (len={slot.length})...")
                words = self._filter_words_with_definitions(words, max_to_check=300)
                if not words:
                    print(f"❌ Aucun mot avec définition de longueur {slot.length}")
                    return False
            
            # Mélanger les mots pour avoir des résultats différents à chaque exécution
            random.shuffle(words)
            
            # Limiter au max
            if len(words) > self.max_words:
                words = words[:self.max_words]
            
            self.slot_words[slot.id] = words
        
        # Phase 2: Pré-filtrage par arc-consistency (optionnel mais très efficace)
        if use_arc_consistency and self.grid.intersections:
            print("🔄 Pré-filtrage des domaines (arc-consistency)...")
            self._apply_arc_consistency()
        
        # Affiche les stats après filtrage
        for slot in self.grid.slots:
            print(f"  Slot {slot.id} ({slot.direction}, len={slot.length}): {len(self.slot_words[slot.id])} mots")
        
        # Vérifie qu'il reste des mots après filtrage
        for slot in self.grid.slots:
            if not self.slot_words[slot.id]:
                print(f"❌ Plus aucun mot possible pour {slot} après filtrage")
                return False
        
        # Crée une variable pour chaque slot
        # La variable représente l'index du mot choisi dans la liste
        for slot in self.grid.slots:
            num_words = len(self.slot_words[slot.id])
            self.slot_vars[slot.id] = self.model.NewIntVar(
                0, num_words - 1, f"slot_{slot.id}"
            )
        
        # Ajoute les contraintes d'intersection
        print(f"\n📐 Ajout de {len(self.grid.intersections)} contraintes d'intersection...")
        for inter in self.grid.intersections:
            self._add_intersection_constraint(inter)
        
        return True
    
    def _apply_arc_consistency(self):
        """
        Applique l'arc-consistency (AC-3) pour réduire les domaines.
        Filtre les mots qui n'ont aucun mot compatible dans les slots voisins.
        """
        # Construire un mapping slot_id -> intersections
        slot_intersections: Dict[int, List[Intersection]] = defaultdict(list)
        for inter in self.grid.intersections:
            slot_intersections[inter.slot1_id].append(inter)
            slot_intersections[inter.slot2_id].append(inter)
        
        # Construire un index lettre -> mots pour chaque slot et position
        # slot_id -> position -> lettre -> set de mots
        slot_letter_index: Dict[int, Dict[int, Dict[str, Set[str]]]] = {}
        
        for slot in self.grid.slots:
            slot_letter_index[slot.id] = defaultdict(lambda: defaultdict(set))
            for word in self.slot_words[slot.id]:
                for pos, letter in enumerate(word):
                    slot_letter_index[slot.id][pos][letter].add(word)
        
        # File des arcs à vérifier
        queue = list(self.grid.intersections)
        iterations = 0
        max_iterations = len(queue) * 10  # Limite pour éviter boucle infinie
        
        while queue and iterations < max_iterations:
            iterations += 1
            inter = queue.pop(0)
            
            # Vérifier dans les deux sens
            changed1 = self._revise_arc(inter.slot1_id, inter.slot1_pos, 
                                        inter.slot2_id, inter.slot2_pos,
                                        slot_letter_index)
            changed2 = self._revise_arc(inter.slot2_id, inter.slot2_pos,
                                        inter.slot1_id, inter.slot1_pos,
                                        slot_letter_index)
            
            # Si un domaine a changé, re-vérifier les arcs voisins
            if changed1:
                for other_inter in slot_intersections[inter.slot1_id]:
                    if other_inter != inter and other_inter not in queue:
                        queue.append(other_inter)
            
            if changed2:
                for other_inter in slot_intersections[inter.slot2_id]:
                    if other_inter != inter and other_inter not in queue:
                        queue.append(other_inter)
    
    def _revise_arc(self, slot1_id: int, pos1: int, slot2_id: int, pos2: int,
                    slot_letter_index: Dict) -> bool:
        """
        Révise l'arc slot1 -> slot2.
        Supprime les mots de slot1 qui n'ont aucun support dans slot2.
        Retourne True si le domaine a été modifié.
        """
        words1 = self.slot_words[slot1_id]
        index2 = slot_letter_index[slot2_id]
        
        # Trouver les lettres possibles à pos2 dans slot2
        possible_letters = set(index2[pos2].keys())
        
        # Filtrer les mots de slot1
        new_words = []
        for word in words1:
            if pos1 < len(word) and word[pos1] in possible_letters:
                # Vérifier qu'il existe au moins un mot compatible dans slot2
                if index2[pos2][word[pos1]]:
                    new_words.append(word)
        
        if len(new_words) < len(words1):
            self.slot_words[slot1_id] = new_words
            # Mettre à jour l'index pour ce slot
            slot_letter_index[slot1_id] = defaultdict(lambda: defaultdict(set))
            for word in new_words:
                for pos, letter in enumerate(word):
                    slot_letter_index[slot1_id][pos][letter].add(word)
            return True
        
        return False
    
    def _add_intersection_constraint(self, inter: Intersection):
        """
        Ajoute une contrainte pour une intersection.
        Les deux slots doivent avoir la même lettre à leur position d'intersection.
        Optimisé avec un index par lettre.
        """
        slot1_id = inter.slot1_id
        slot2_id = inter.slot2_id
        pos1 = inter.slot1_pos
        pos2 = inter.slot2_pos
        
        words1 = self.slot_words[slot1_id]
        words2 = self.slot_words[slot2_id]
        
        # Construire un index lettre -> indices pour words2
        letter_to_indices2: Dict[str, List[int]] = defaultdict(list)
        for i2, word2 in enumerate(words2):
            if pos2 < len(word2):
                letter_to_indices2[word2[pos2]].append(i2)
        
        # Liste des paires (index1, index2) compatibles - OPTIMISÉ
        compatible_pairs = []
        for i1, word1 in enumerate(words1):
            if pos1 < len(word1):
                letter = word1[pos1]
                for i2 in letter_to_indices2.get(letter, []):
                    compatible_pairs.append((i1, i2))
        
        if not compatible_pairs:
            print(f"  ⚠ Aucune paire compatible pour intersection {inter}")
            # Ajoute une contrainte impossible
            self.model.Add(self.slot_vars[slot1_id] == -1)
            return
        
        # Utilise une contrainte de table (tuple autorisés)
        self.model.AddAllowedAssignments(
            [self.slot_vars[slot1_id], self.slot_vars[slot2_id]],
            compatible_pairs
        )
    
    def _add_all_different_constraint(self):
        """
        Ajoute une contrainte pour que tous les mots soient différents.
        Utile pour éviter les répétitions dans la grille.
        """
        # Regroupe les slots par longueur
        slots_by_length: Dict[int, List[int]] = defaultdict(list)
        for slot in self.grid.slots:
            slots_by_length[slot.length].append(slot.id)
        
        # Pour chaque groupe de même longueur, les indices doivent être différents
        for length, slot_ids in slots_by_length.items():
            if len(slot_ids) > 1:
                vars_same_length = [self.slot_vars[sid] for sid in slot_ids]
                self.model.AddAllDifferent(vars_same_length)
    
    def solve(self, time_limit: float = 30.0, num_solutions: int = 1) -> bool:
        """
        Résout le problème de mots-croisés.
        
        Args:
            time_limit: Temps maximum en secondes
            num_solutions: Nombre de solutions à chercher (1 = première solution)
        
        Returns:
            True si une solution a été trouvée
        """
        print(f"\n🔍 Recherche de solution (limite: {time_limit}s)...")
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        
        # Optimisations du solveur
        solver.parameters.num_search_workers = 4  # Parallélisation
        solver.parameters.linearization_level = 0  # Désactiver linéarisation (plus rapide pour ce type de problème)
        solver.parameters.cp_model_presolve = True  # Activer le prétraitement
        
        # Utiliser une recherche aléatoire pour des grilles différentes à chaque fois
        solver.parameters.random_seed = random.randint(0, 1000000)
        solver.parameters.search_branching = cp_model.AUTOMATIC_SEARCH
        
        # Callback pour afficher les solutions trouvées
        solution_callback = SolutionCallback(self, num_solutions)
        
        start_time = time.time()
        
        if num_solutions == 1:
            status = solver.Solve(self.model)
        else:
            status = solver.SearchForAllSolutions(self.model, solution_callback)
        
        elapsed = time.time() - start_time
        
        # Interprète le résultat
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f"\n✅ Solution trouvée en {elapsed:.2f}s!")
            
            # Extrait la solution
            for slot in self.grid.slots:
                word_index = solver.Value(self.slot_vars[slot.id])
                word = self.slot_words[slot.id][word_index]
                self.grid.solution[slot.id] = word
            
            return True
        else:
            status_name = {
                cp_model.UNKNOWN: "UNKNOWN",
                cp_model.MODEL_INVALID: "MODEL_INVALID",
                cp_model.INFEASIBLE: "INFEASIBLE"
            }.get(status, str(status))
            print(f"\n❌ Pas de solution trouvée (status: {status_name}, temps: {elapsed:.2f}s)")
            return False
    
    def get_statistics(self) -> Dict:
        """Retourne des statistiques sur le problème"""
        return {
            'num_slots': len(self.grid.slots),
            'num_intersections': len(self.grid.intersections),
            'slots_by_length': {
                length: sum(1 for s in self.grid.slots if s.length == length)
                for length in set(s.length for s in self.grid.slots)
            },
            'total_combinations': sum(
                len(self.slot_words.get(s.id, [])) for s in self.grid.slots
            )
        }


class SolutionCallback(cp_model.CpSolverSolutionCallback):
    """Callback pour collecter plusieurs solutions"""
    
    def __init__(self, solver: CrosswordSolver, max_solutions: int):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.solver = solver
        self.max_solutions = max_solutions
        self.solutions = []
    
    def on_solution_callback(self):
        solution = {}
        for slot in self.solver.grid.slots:
            word_index = self.Value(self.solver.slot_vars[slot.id])
            word = self.solver.slot_words[slot.id][word_index]
            solution[slot.id] = word
        self.solutions.append(solution)
        
        if len(self.solutions) >= self.max_solutions:
            self.StopSearch()
