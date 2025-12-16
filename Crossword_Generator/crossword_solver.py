# -*- coding: utf-8 -*-
"""
Générateur de Mots-Croisés avec Programmation par Contraintes (CSP)
===================================================================

Module principal - Point d'entrée pour la génération de mots-croisés.
Utilise OR-Tools CP-SAT pour la résolution du problème CSP.

Ce fichier réexporte les classes des sous-modules pour la compatibilité
et fournit la fonction principale create_crossword().

Classes exportées:
    - Slot: Représente un emplacement de mot
    - Intersection: Représente une intersection entre deux slots
    - WordDictionary: Gestion du dictionnaire de mots
    - DefinitionService: Service pour récupérer les définitions (Wiktionnaire, Dicolink)
    - CrosswordGrid: Représentation de la grille
    - CrosswordSolver: Solveur CSP avec CP-SAT
    - SolutionCallback: Callback pour collecter les solutions
    - GRID_PATTERNS: Motifs de grilles prédéfinis
"""

from typing import List, Optional

# Réexporter toutes les classes depuis le package solver
from solver import (
    Slot,
    Intersection,
    WordDictionary,
    remove_accents,
    DefinitionService,
    CrosswordGrid,
    CrosswordSolver,
    SolutionCallback,
    GRID_PATTERNS,
)


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def create_crossword(
    pattern_name: str = 'mini_5x5',
    custom_pattern: Optional[List[str]] = None,
    dictionary_file: Optional[str] = None,
    time_limit: float = 30.0,
    verbose: bool = True
) -> Optional[CrosswordGrid]:
    """
    Crée et résout une grille de mots-croisés.
    
    Args:
        pattern_name: Nom du motif prédéfini à utiliser
        custom_pattern: Motif personnalisé (prioritaire sur pattern_name)
        dictionary_file: Chemin vers un fichier dictionnaire
        time_limit: Temps limite pour la résolution
        verbose: Afficher les détails
    
    Returns:
        La grille résolue ou None si échec
    """
    
    print("=" * 60)
    print("   GÉNÉRATEUR DE MOTS-CROISÉS (CP-SAT)")
    print("=" * 60)
    
    # 1. Charge le dictionnaire
    dictionary = WordDictionary()
    if dictionary_file:
        dictionary.load_from_file(dictionary_file)
    else:
        # Utilise le chargement intelligent (téléchargement auto ou fallback)
        dictionary.load_smart()
    
    if verbose:
        print("\n📚 Statistiques du dictionnaire:")
        for length, count in sorted(dictionary.get_stats().items()):
            print(f"   {length} lettres: {count} mots")
    
    # 2. Crée la grille
    if custom_pattern:
        pattern = custom_pattern
    elif pattern_name in GRID_PATTERNS:
        pattern = GRID_PATTERNS[pattern_name]
    else:
        print(f"⚠ Motif '{pattern_name}' inconnu, utilisation de 'mini_5x5'")
        pattern = GRID_PATTERNS['mini_5x5']
    
    grid = CrosswordGrid(len(pattern), len(pattern[0]))
    grid.load_pattern(pattern)
    
    print(f"\n📐 Grille chargée: {grid.rows}×{grid.cols}")
    if verbose:
        grid.display_structure()
    
    # 3. Extrait les slots et intersections
    slots = grid.extract_slots(min_length=2)
    intersections = grid.find_intersections()
    
    print(f"\n📊 Analyse de la grille:")
    print(f"   - {len(slots)} emplacements de mots")
    print(f"   - {len(intersections)} intersections")
    
    if verbose:
        print("\n   Slots:")
        for slot in slots:
            print(f"     {slot}")
    
    # 4. Résout le CSP
    solver = CrosswordSolver(grid, dictionary)
    
    if not solver.build_model():
        print("\n❌ Impossible de construire le modèle (dictionnaire insuffisant)")
        return None
    
    if solver.solve(time_limit=time_limit):
        # Affiche la solution
        print("\n" + "=" * 60)
        print("   SOLUTION")
        print("=" * 60)
        grid.display_solution()
        
        # Affiche les mots
        words = grid.get_solution_words()
        print("\n📝 Mots trouvés:")
        for direction, word_list in words.items():
            if word_list:
                print(f"\n   {direction}:")
                for word, (row, col) in word_list:
                    print(f"     ({row},{col}) → {word}")
        
        return grid
    
    return None


# =============================================================================
# DEMO / TEST
# =============================================================================

if __name__ == "__main__":
    # Test basique du module
    print("Test du module crossword_solver")
    print("-" * 40)
    
    result = create_crossword(
        pattern_name='mini_5x5',
        time_limit=30.0,
        verbose=True
    )
    
    if result:
        print("\n✅ Module fonctionne correctement!")
    else:
        print("\n❌ Problème avec le module")
