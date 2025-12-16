"""
Script de vérification de l'installation et des imports.

Teste que tous les modules et dépendances sont correctement installés.
"""

import sys
from typing import List, Tuple


def test_import(module_name: str, package_name: str = None) -> Tuple[bool, str]:
    """
    Teste l'import d'un module.
    
    Args:
        module_name: Nom du module à importer
        package_name: Nom du package (pour affichage)
        
    Returns:
        (succès, message)
    """
    try:
        __import__(module_name)
        return True, f"✅ {package_name or module_name}"
    except ImportError as e:
        return False, f"❌ {package_name or module_name}: {e}"


def check_dependencies():
    """Vérifie les dépendances externes."""
    print("="*60)
    print("Vérification des dépendances")
    print("="*60 + "\n")
    
    dependencies = [
        ('numpy', 'NumPy'),
        ('ortools', 'OR-Tools'),
        ('pygame', 'Pygame'),
        ('matplotlib', 'Matplotlib'),
        ('torch', 'PyTorch'),
        ('torchvision', 'TorchVision'),
        ('tqdm', 'tqdm'),
        ('PIL', 'Pillow'),
    ]
    
    all_ok = True
    for module, name in dependencies:
        success, msg = test_import(module, name)
        print(msg)
        if not success:
            all_ok = False
    
    print()
    return all_ok


def check_cuda():
    """Vérifie le support CUDA pour PyTorch."""
    print("="*60)
    print("Vérification du support GPU (CUDA)")
    print("="*60 + "\n")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            print(f"✅ CUDA disponible")
            print(f"   Version CUDA: {torch.version.cuda}")
            print(f"   Nombre de GPUs: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                print(f"   GPU {i}: {gpu_name}")
            
            # Test d'allocation mémoire
            try:
                x = torch.randn(1000, 1000).cuda()
                print(f"✅ Test d'allocation GPU réussi")
                del x
                torch.cuda.empty_cache()
            except Exception as e:
                print(f"⚠️  Erreur d'allocation GPU: {e}")
        else:
            print("⚠️  CUDA non disponible")
            print("   L'entraînement se fera sur CPU (plus lent)")
            print("   Pour installer PyTorch avec CUDA:")
            print("   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
    
    except ImportError:
        print("❌ PyTorch non installé")
    
    print()


def check_project_structure():
    """Vérifie la structure du projet."""
    print("="*60)
    print("Vérification de la structure du projet")
    print("="*60 + "\n")
    
    modules = [
        # Game
        ('game.board', 'game/board.py'),
        ('game.visualizer', 'game/visualizer.py'),
        ('game.interactive_visualizer', 'game/interactive_visualizer.py'),
        
        # Solvers
        ('solvers.base_solver', 'solvers/base_solver.py'),
        ('solvers.simple_solver', 'solvers/simple_solver.py'),
        ('solvers.ortools_solver', 'solvers/ortools_solver.py'),
        ('solvers.optimized_solver', 'solvers/optimized_solver.py'),
        ('solvers.supervised_solver', 'solvers/supervised_solver.py'),
        
        # CSP
        ('csp.constraint_builder', 'csp/constraint_builder.py'),
        ('csp.probability', 'csp/probability.py'),
        ('csp.components', 'csp/components.py'),
        
        # Training
        ('training.model', 'training/model.py'),
        ('training.generate_dataset', 'training/generate_dataset.py'),
        ('training.train', 'training/train.py'),
    ]
    
    all_ok = True
    for module, path in modules:
        success, msg = test_import(module, path)
        print(msg)
        if not success:
            all_ok = False
    
    print()
    return all_ok


def check_models():
    """Vérifie la présence des modèles entraînés."""
    print("="*60)
    print("Vérification des modèles entraînés")
    print("="*60 + "\n")
    
    import os
    
    models = [
        'training/models/easy_cnn/best_model.pth',
        'training/models/medium_cnn/best_model.pth',
        'training/models/hard_cnn/best_model.pth',
    ]
    
    found = False
    for model_path in models:
        if os.path.exists(model_path):
            print(f"✅ {model_path}")
            found = True
        else:
            print(f"⚠️  {model_path} (non trouvé)")
    
    if not found:
        print("\n💡 Aucun modèle entraîné trouvé.")
        print("   Pour entraîner un modèle:")
        print("   1. python training/generate_dataset.py")
        print("   2. python training/train.py --difficulty medium")
    
    print()


def test_basic_functionality():
    """Teste la fonctionnalité de base."""
    print("="*60)
    print("Tests de fonctionnalité de base")
    print("="*60 + "\n")
    
    try:
        # Test création board
        from game.board import Board, GameState
        board = Board(9, 9, 10, seed=42)
        print("✅ Board créé (9x9, 10 mines)")
        
        # Test solveur simple
        from solvers.simple_solver import SimpleSolver
        solver = SimpleSolver(board)
        move = solver.get_next_move()
        if move:
            print(f"✅ SimpleSolver fonctionne (premier coup: {move})")
        
        # Test solveur CSP
        from solvers.ortools_solver import ORToolsSolver
        board2 = Board(9, 9, 10, seed=42)
        solver2 = ORToolsSolver(board2)
        move2 = solver2.get_next_move()
        if move2:
            print(f"✅ ORToolsSolver fonctionne (premier coup: {move2})")
        
        # Test solveur optimisé
        from solvers.optimized_solver import OptimizedSolver
        board3 = Board(9, 9, 10, seed=42)
        solver3 = OptimizedSolver(board3)
        move3 = solver3.get_next_move()
        if move3:
            print(f"✅ OptimizedSolver fonctionne (premier coup: {move3})")
        
        print("\n✅ Tous les tests de base passent !")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def main():
    """Point d'entrée principal."""
    print("\n" + "="*60)
    print(" VÉRIFICATION DE L'INSTALLATION - SOLVEUR DÉMINEUR")
    print("="*60 + "\n")
    
    # Vérifier dépendances
    deps_ok = check_dependencies()
    
    # Vérifier CUDA
    check_cuda()
    
    # Vérifier structure
    structure_ok = check_project_structure()
    
    # Vérifier modèles
    check_models()
    
    # Tests de base
    if deps_ok and structure_ok:
        test_basic_functionality()
    
    # Résumé
    print("="*60)
    print(" RÉSUMÉ")
    print("="*60 + "\n")
    
    if deps_ok and structure_ok:
        print("✅ Installation complète !")
        print("\n📚 Prochaines étapes:")
        print("   1. Lire USAGE.md pour le guide complet")
        print("   2. Lancer demo.py pour une démo interactive")
        print("   3. Générer datasets: python training/generate_dataset.py")
        print("   4. Entraîner CNN: python training/train.py --difficulty medium")
        print("   5. Benchmarker: python benchmark_all_solvers.py")
    else:
        print("⚠️  Installation incomplète")
        print("\n🔧 Actions requises:")
        if not deps_ok:
            print("   - Installer les dépendances: pip install -r requirements.txt")
        if not structure_ok:
            print("   - Vérifier que tous les fichiers du projet sont présents")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
