#!/usr/bin/env python3
"""
Script de vérification rapide pour tester le système CSP.

Lance quelques tests rapides pour s'assurer que tout fonctionne.
"""

import sys
from pathlib import Path

# Ajouter le dossier racine au path
sys.path.insert(0, str(Path(__file__).parent))

from wordle_solver import (
    WordleGame,
    HybridSolver,
    ConstraintManager,
    DictionaryLoader,
    generate_feedback,
    Feedback
)


def test_feedback_system():
    """Test du système de feedback."""
    print("🧪 Test 1: Système de feedback")
    print("-" * 50)
    
    # Test 1: Toutes correctes
    fb = generate_feedback("ROBOT", "ROBOT")
    assert fb.is_correct(), "Échec: toutes les lettres devraient être correctes"
    print("  ✓ Test feedback all correct: OK")
    
    # Test 2: Aucune correspondance
    fb = generate_feedback("AROSE", "FIGHT")
    assert not fb.is_correct(), "Échec: aucune lettre ne devrait être correcte"
    print("  ✓ Test feedback no match: OK")
    
    # Test 3: Mélange - R et O sont présents mais mal placés
    fb = generate_feedback("AROSE", "ROBOT")
    present_letters = [fb.guess[i] for i, f in enumerate(fb.feedbacks) if f == Feedback.PRESENT]
    assert 'R' in present_letters and 'O' in present_letters, "R et O devraient être présents"
    print("  ✓ Test feedback mixed: OK")
    
    print("✅ Système de feedback: OK\n")


def test_constraint_manager():
    """Test du gestionnaire de contraintes."""
    print("🧪 Test 2: Gestionnaire de contraintes")
    print("-" * 50)
    
    cm = ConstraintManager()
    
    # Appliquer un feedback
    fb = generate_feedback("AROSE", "ROBOT")
    cm.apply_feedback(fb)
    
    # Vérifier les contraintes
    assert cm.correct_positions.get(1) == 'R', "R devrait être en position 1"
    assert 'O' in cm.present_letters, "O devrait être présent"
    print("  ✓ Application de contraintes: OK")
    
    # Test de validation
    assert cm.is_word_valid("ROBOT"), "ROBOT devrait être valide"
    assert not cm.is_word_valid("AROSE"), "AROSE ne devrait plus être valide"
    print("  ✓ Validation de mots: OK")
    
    print("✅ Gestionnaire de contraintes: OK\n")


def test_dictionary_loading():
    """Test du chargement des dictionnaires."""
    print("🧪 Test 3: Chargement des dictionnaires")
    print("-" * 50)
    
    try:
        # Charger dictionnaire anglais
        en_dict = DictionaryLoader.load_english()
        print(f"  ✓ Dictionnaire EN chargé: {len(en_dict)} mots")
        
        # Charger dictionnaire français
        fr_dict = DictionaryLoader.load_french()
        print(f"  ✓ Dictionnaire FR chargé: {len(fr_dict)} mots")
        
        # Vérifier qu'ils contiennent bien des mots
        assert len(en_dict) > 0, "Le dictionnaire anglais est vide"
        assert len(fr_dict) > 0, "Le dictionnaire français est vide"
        
        print("✅ Chargement des dictionnaires: OK\n")
        return True
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}\n")
        return False


def test_word_filter():
    """Test du filtre de mots."""
    print("🧪 Test 4: Filtre de mots")
    print("-" * 50)
    
    # Créer un petit dictionnaire de test
    test_dict = {"ROBOT", "AROSE", "SLATE", "ROVER", "ROOST"}
    
    from wordle_solver.csp import WordFilter
    wf = WordFilter(test_dict)
    
    # Créer des contraintes
    cm = ConstraintManager()
    fb = generate_feedback("AROSE", "ROBOT")
    cm.apply_feedback(fb)
    
    # Filtrer
    valid = wf.filter_by_constraints(cm)
    
    assert "ROBOT" in valid, "ROBOT devrait être dans les résultats"
    assert "AROSE" not in valid, "AROSE ne devrait pas être dans les résultats"
    print(f"  ✓ Filtrage: {len(valid)} mots valides trouvés")
    print(f"    Mots valides: {sorted(valid)}")
    
    print("✅ Filtre de mots: OK\n")


def test_hybrid_solver():
    """Test du solveur hybride."""
    print("🧪 Test 5: Solveur hybride")
    print("-" * 50)
    
    # Créer un dictionnaire de test
    test_dict = {"ROBOT", "AROSE", "SLATE", "ROVER", "ROOST", "ROOTS"}
    
    solver = HybridSolver(test_dict)
    cm = ConstraintManager()
    
    # Première tentative
    fb1 = generate_feedback("AROSE", "ROBOT")
    cm.apply_feedback(fb1)
    
    possible1 = solver.get_possible_words(cm, limit=10)
    print(f"  ✓ Après 1ère tentative: {len(possible1)} mots possibles")
    print(f"    {sorted(possible1)}")
    
    # Deuxième tentative
    if possible1:
        fb2 = generate_feedback("ROVER", "ROBOT")
        cm.apply_feedback(fb2)
        
        possible2 = solver.get_possible_words(cm, limit=10)
        print(f"  ✓ Après 2ème tentative: {len(possible2)} mots possibles")
        print(f"    {sorted(possible2)}")
        
        assert "ROBOT" in possible2, "ROBOT devrait être dans les résultats"
    
    print("✅ Solveur hybride: OK\n")


def test_wordle_game():
    """Test du jeu Wordle."""
    print("🧪 Test 6: Jeu Wordle")
    print("-" * 50)
    
    # Créer une partie
    game = WordleGame("ROBOT")
    
    # Première tentative
    fb1 = game.make_guess("AROSE")
    print(f"  Tentative 1: {fb1.to_string()}")
    assert not game.is_over
    
    # Deuxième tentative (gagner)
    fb2 = game.make_guess("ROBOT")
    print(f"  Tentative 2: {fb2.to_string()}")
    assert game.is_won
    assert game.is_over
    
    print(f"  ✓ Partie gagnée en {len(game.attempts)} tentatives")
    print("✅ Jeu Wordle: OK\n")


def run_all_tests():
    """Lance tous les tests."""
    print("\n" + "="*70)
    print(" "*20 + "TESTS DE VÉRIFICATION")
    print("="*70 + "\n")
    
    tests = [
        test_feedback_system,
        test_constraint_manager,
        test_dictionary_loading,
        test_word_filter,
        test_hybrid_solver,
        test_wordle_game
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ ÉCHEC: {e}\n")
            failed += 1
        except Exception as e:
            print(f"❌ ERREUR: {e}\n")
            failed += 1
    
    print("="*70)
    print(f"Résultats: {passed} tests réussis, {failed} tests échoués")
    print("="*70 + "\n")
    
    if failed == 0:
        print("🎉 Tous les tests sont passés ! Le système CSP est opérationnel.\n")
        return True
    else:
        print(f"⚠️  {failed} test(s) ont échoué. Vérifiez les erreurs ci-dessus.\n")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus par l'utilisateur\n")
        sys.exit(130)
