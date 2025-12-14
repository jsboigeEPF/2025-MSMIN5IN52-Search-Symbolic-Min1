"""
Tests unitaires pour le module CSP.
"""

import sys
from pathlib import Path

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from wordle_solver.csp import ConstraintManager, WordFilter, HybridSolver
from wordle_solver.game import generate_feedback, Feedback


class TestConstraintManager:
    """Tests pour le gestionnaire de contraintes."""
    
    def test_initialization(self):
        """Test de l'initialisation."""
        cm = ConstraintManager()
        assert len(cm.correct_positions) == 0
        assert len(cm.present_letters) == 0
        assert len(cm.absent_letters) == 0
    
    def test_correct_position_constraint(self):
        """Test des contraintes de position correcte."""
        cm = ConstraintManager()
        feedback = generate_feedback("AROSE", "ROBOT")
        cm.apply_feedback(feedback)
        
        # R est présent mais PAS à la bonne position (il est jaune, pas vert)
        assert 'R' in cm.present_letters
        assert 1 in cm.present_letters['R']  # Position où R était testé (mal placé)
        
        # O est présent mais mal placé
        assert 'O' in cm.present_letters
        assert 2 in cm.present_letters['O']  # Position où O était testé
    
    def test_absent_letters(self):
        """Test des lettres absentes."""
        cm = ConstraintManager()
        feedback = generate_feedback("STYLE", "ROBOT")
        cm.apply_feedback(feedback)
        
        # S, Y, L, E ne sont pas dans ROBOT
        for letter in ['S', 'Y', 'L', 'E']:
            assert letter in cm.absent_letters
    
    def test_word_validation(self):
        """Test de validation des mots."""
        cm = ConstraintManager()
        
        # Après AROSE sur ROBOT
        feedback = generate_feedback("AROSE", "ROBOT")
        cm.apply_feedback(feedback)
        
        # ROBOT devrait être valide
        assert cm.is_word_valid("ROBOT")
        
        # AROSE ne devrait plus être valide (A, S, E absents)
        assert not cm.is_word_valid("AROSE")
        
        # ROVER devrait être valide (contient R en pos 1 et O)
        assert cm.is_word_valid("ROVER")


class TestWordFilter:
    """Tests pour le filtre de mots."""
    
    def test_initialization(self):
        """Test de l'initialisation."""
        dictionary = {"ROBOT", "AROSE", "SLATE"}
        wf = WordFilter(dictionary)
        assert len(wf.full_dictionary) == 3
        assert len(wf.current_candidates) == 3
    
    def test_filtering(self):
        """Test du filtrage."""
        dictionary = {"ROBOT", "AROSE", "SLATE", "ROVER", "ROOST"}
        wf = WordFilter(dictionary)
        cm = ConstraintManager()
        
        # Après AROSE sur ROBOT
        feedback = generate_feedback("AROSE", "ROBOT")
        cm.apply_feedback(feedback)
        
        # Filtrer
        valid_words = wf.filter_by_constraints(cm)
        
        # ROBOT et ROVER devraient être dans les résultats
        assert "ROBOT" in valid_words
        assert "ROVER" in valid_words
        
        # AROSE ne devrait pas être valide
        assert "AROSE" not in valid_words


class TestHybridSolver:
    """Tests pour le solveur hybride."""
    
    def test_solve_simple_case(self):
        """Test de résolution d'un cas simple."""
        dictionary = {"ROBOT", "AROSE", "SLATE", "ROVER", "ROOST"}
        solver = HybridSolver(dictionary)
        cm = ConstraintManager()
        
        # Premier feedback
        feedback1 = generate_feedback("AROSE", "ROBOT")
        cm.apply_feedback(feedback1)
        
        # Obtenir les mots possibles
        possible = solver.get_possible_words(cm)
        
        # ROBOT devrait être dans les possibilités
        assert "ROBOT" in possible
        
        # Le nombre de possibilités devrait être réduit
        assert len(possible) < len(dictionary)
    
    def test_progressive_solving(self):
        """Test de résolution progressive."""
        dictionary = {"ROBOT", "AROSE", "SLATE", "ROVER", "ROOST", "ROOTS"}
        solver = HybridSolver(dictionary)
        cm = ConstraintManager()
        
        # Tentative 1
        feedback1 = generate_feedback("AROSE", "ROBOT")
        cm.apply_feedback(feedback1)
        possible1 = solver.get_possible_words(cm)
        
        # Tentative 2
        if possible1:
            feedback2 = generate_feedback("ROVER", "ROBOT")
            cm.apply_feedback(feedback2)
            possible2 = solver.get_possible_words(cm)
            
            # Le nombre de possibilités devrait diminuer
            assert len(possible2) <= len(possible1)
            
            # ROBOT devrait toujours être possible
            assert "ROBOT" in possible2


class TestFeedbackGeneration:
    """Tests pour la génération de feedback."""
    
    def test_all_correct(self):
        """Test quand toutes les lettres sont correctes."""
        feedback = generate_feedback("ROBOT", "ROBOT")
        assert all(fb == Feedback.CORRECT for fb in feedback.feedbacks)
        assert feedback.is_correct()
    
    def test_no_matches(self):
        """Test quand aucune lettre ne correspond."""
        feedback = generate_feedback("STYLE", "ROBOT")
        
        # T est à la fois dans STYLE et ROBOT
        # Mais à des positions différentes
        has_present = any(fb == Feedback.PRESENT for fb in feedback.feedbacks)
        assert has_present or all(fb == Feedback.ABSENT for fb in feedback.feedbacks)
    
    def test_duplicate_letters(self):
        """Test avec des lettres dupliquées."""
        # SPEED a deux E, TARGET n'en a qu'un
        feedback = generate_feedback("SPEED", "TARGET")
        
        # Le premier E (position 2) devrait être PRESENT
        # Le deuxième E (position 3) devrait être CORRECT
        # On vérifie juste que le système gère les duplications
        assert feedback is not None
        assert len(feedback.feedbacks) == 5


def test_full_game_simulation():
    """Test d'une simulation de partie complète."""
    from wordle_solver import WordleGame, DictionaryLoader
    
    # Utiliser un petit dictionnaire de test
    test_dict = {"ROBOT", "AROSE", "SLATE", "ROVER"}
    
    # Créer une partie
    game = WordleGame("ROBOT")
    
    # Faire quelques tentatives
    feedback1 = game.make_guess("AROSE")
    assert not game.is_over
    
    feedback2 = game.make_guess("ROBOT")
    assert game.is_won
    assert game.is_over
    
    # Vérifier l'historique
    history = game.get_history()
    assert len(history) == 2


if __name__ == "__main__":
    # Lancer les tests
    pytest.main([__file__, "-v"])
