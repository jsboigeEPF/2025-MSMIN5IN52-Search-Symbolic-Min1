#!/usr/bin/env python3
"""Test simple pour vérifier que ROBOT est maintenant trouvable."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Import sans ortools
from wordle_solver.game import generate_feedback
from wordle_solver.csp.constraint_manager import ConstraintManager
from wordle_solver.csp.word_filter import WordFilter
from wordle_solver.dictionaries import DictionaryLoader

def test_robot_fix():
    print("="*70)
    print("TEST: Vérification du correctif ROBOT")
    print("="*70)
    
    # 1. Vérifier que ROBOT est dans le dictionnaire
    print("\n1️⃣ Vérification du dictionnaire")
    dictionary = DictionaryLoader.load_english()
    if "ROBOT" in dictionary:
        print("   ✅ ROBOT est dans le dictionnaire")
    else:
        print("   ❌ ROBOT n'est pas dans le dictionnaire")
        return False
    
    # 2. Test du scénario complet
    print("\n2️⃣ Test du scénario AROSE → COURT → ROBOT")
    
    wf = WordFilter(dictionary)
    cm = ConstraintManager()
    
    # Feedback 1: AROSE
    print("\n   Feedback 1: AROSE vs ROBOT")
    fb1 = generate_feedback("AROSE", "ROBOT")
    print(f"   Résultat: {fb1}")
    cm.apply_feedback(fb1)
    
    possible1 = wf.filter_by_constraints(cm)
    print(f"   Mots possibles: {len(possible1)}")
    
    if "ROBOT" in possible1:
        print("   ✅ ROBOT dans les mots possibles")
    else:
        print("   ❌ ROBOT devrait être dans les mots possibles")
        print(f"   Échantillon: {sorted(list(possible1))[:10]}")
        return False
    
    # Feedback 2: COURT
    print("\n   Feedback 2: COURT vs ROBOT")
    fb2 = generate_feedback("COURT", "ROBOT")
    print(f"   Résultat: {fb2}")
    cm.apply_feedback(fb2)
    
    possible2 = wf.filter_by_constraints(cm)
    print(f"   Mots possibles: {len(possible2)}")
    print(f"   Mots: {sorted(possible2)}")
    
    if "ROBOT" in possible2:
        print("   ✅ ROBOT dans les mots possibles")
    else:
        print("   ❌ ROBOT devrait être dans les mots possibles")
        return False
    
    # 3. Test de validation directe
    print("\n3️⃣ Test de validation directe")
    is_valid = cm.is_word_valid("ROBOT")
    print(f"   is_word_valid('ROBOT'): {is_valid}")
    
    if is_valid:
        print("   ✅ ROBOT est valide selon les contraintes")
    else:
        print("   ❌ ROBOT devrait être valide")
        return False
    
    print("\n" + "="*70)
    print("✅ TOUS LES TESTS PASSÉS - Le bug est corrigé !")
    print("="*70)
    return True

if __name__ == "__main__":
    try:
        success = test_robot_fix()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
