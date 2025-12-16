"""
Guide d'utilisation du Solveur de Démineur
==========================================

Ce guide explique comment utiliser les différents solveurs et fonctionnalités.

## Installation

1. **Cloner le projet et installer les dépendances:**
```bash
pip install -r requirements.txt
```

2. **Pour support GPU (RTX 3060):**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## Utilisation Rapide

### 1. Démo Interactive

Lancer une démo avec le solveur optimisé:
```bash
python demo.py
```

Avec un solveur spécifique:
```bash
python demo.py --solver optimized
python demo.py --solver csp
python demo.py --solver simple
```

Difficulté personnalisée:
```bash
# Débutant
python demo.py --width 9 --height 9 --mines 10

# Intermédiaire (défaut)
python demo.py --width 16 --height 16 --mines 40

# Expert
python demo.py --width 30 --height 16 --mines 99
```

**Contrôles pendant la démo:**
- `ESPACE` - Pause/Reprendre
- `S` - Un coup à la fois (step-by-step)
- `P` - Afficher/Masquer les probabilités
- `H` - Afficher/Masquer la heatmap
- `C` - Afficher/Masquer les composantes connexes
- `+/-` - Augmenter/Diminuer la vitesse
- `R` - Recommencer
- `ESC` - Quitter

### 2. Entraîner le Modèle CNN

**Générer les datasets:**
```bash
python training/generate_dataset.py
```

Cela génère 3 datasets:
- `datasets/easy_*.npz` (9x9, 10 mines)
- `datasets/medium_*.npz` (16x16, 40 mines)
- `datasets/hard_*.npz` (30x16, 99 mines)

**Entraîner le modèle:**
```bash
# Sur difficulté intermédiaire (recommandé)
python training/train.py --difficulty medium --epochs 50

# Sur autre difficulté
python training/train.py --difficulty easy --epochs 30
python training/train.py --difficulty hard --epochs 100
```

Options avancées:
```bash
python training/train.py \
  --difficulty medium \
  --epochs 50 \
  --batch-size 64 \
  --lr 0.001 \
  --model-type cnn
```

Le modèle entraîné sera sauvegardé dans `training/models/{difficulty}_cnn/best_model.pth`.

### 3. Utiliser le Solveur Supervisé

Une fois le modèle entraîné:
```bash
# Solveur CNN seul
python demo.py --solver supervised

# Solveur hybride (CSP + CNN)
python demo.py --solver hybrid
```

### 4. Benchmarking

Comparer tous les solveurs:
```bash
python benchmark_all_solvers.py
```

Cela va:
1. Tester chaque solveur sur 100 parties (débutant et intermédiaire) ou 50 (expert)
2. Afficher les statistiques (win rate, temps, déductions logiques)
3. Générer des graphiques comparatifs (sauvegardés en PNG)

## Architecture des Solveurs

### 1. Simple Solver (`solvers/simple_solver.py`)
- Utilise uniquement les règles AFN (Aucune Frontière N'a de mine) et AMN (Toutes Mines Nécessaires)
- Rapide mais limité
- Bon pour situations simples

### 2. CSP Solver (`solvers/ortools_solver.py`)
- Utilise OR-Tools CP-SAT pour résoudre les contraintes
- Énumère toutes les solutions possibles
- Calcule les probabilités exactes
- Complet mais peut être lent sur grandes grilles

### 3. Optimized Solver (`solvers/optimized_solver.py`)
- **Approche 3 du projet**
- Détecte les composantes connexes indépendantes
- Résout chaque composante séparément
- **Gain de performance: 10-100x** sur grilles complexes
- Utilise `csp/components.py` pour la décomposition

### 4. Supervised Solver (`solvers/supervised_solver.py`)
- **Approche 4 du projet**
- Utilise un CNN entraîné pour prédire les meilleurs coups
- Apprentissage supervisé depuis le solveur CSP expert
- Rapide à l'inférence (quelques ms par coup)

### 5. Hybrid Solver (`solvers/supervised_solver.py`)
- Combine CSP pour coups certains + CNN pour coups ambigus
- Meilleur compromis performance/précision
- Utilise CSP quand certitude > seuil, sinon CNN

## Visualisation Interactive

### Features de `game/interactive_visualizer.py`

**Approche 5 du projet** - Visualisation en temps réel:

1. **Heatmap de probabilités:**
   - Vert = Sûr (prob mine < 20%)
   - Jaune = Incertain (20-80%)
   - Rouge = Dangereux (prob mine > 80%)

2. **Overlay de probabilités:**
   - Affiche le % de chance de mine sur chaque cellule
   - Mis à jour en temps réel

3. **Composantes connexes:**
   - Colore chaque région indépendante
   - Montre comment le solveur optimisé décompose le problème

4. **Panneau de contrôle:**
   - Statistiques du jeu
   - Décisions du solveur
   - Métriques de performance

## Structure du Projet

```
.
├── game/
│   ├── board.py                    # Logique du jeu
│   ├── visualizer.py               # Visualisation basique
│   └── interactive_visualizer.py   # Visualisation avancée (Approche 5)
│
├── solvers/
│   ├── base_solver.py              # Interface commune
│   ├── simple_solver.py            # Règles AFN/AMN
│   ├── ortools_solver.py           # CSP avec OR-Tools
│   ├── optimized_solver.py         # CSP + composantes (Approche 3)
│   └── supervised_solver.py        # CNN + Hybride (Approche 4)
│
├── csp/
│   ├── constraint_builder.py       # Construction des contraintes
│   ├── probability.py              # Calcul de probabilités
│   └── components.py               # Détection composantes connexes
│
├── training/
│   ├── generate_dataset.py         # Génération de données
│   ├── model.py                    # Architectures CNN
│   └── train.py                    # Pipeline d'entraînement GPU
│
├── demo.py                         # Script de démo
├── benchmark_all_solvers.py        # Benchmarking complet
└── requirements.txt                # Dépendances
```

## Performances Attendues

### Win Rates (approximatifs):
- **Simple:** 50-70%
- **CSP:** 75-85%
- **Optimized:** 75-85% (même précision, plus rapide)
- **Supervised:** 70-80% (après bon entraînement)
- **Hybrid:** 80-90% (meilleur des deux mondes)

### Temps par coup:
- **Simple:** < 1ms
- **CSP:** 10-100ms
- **Optimized:** 1-10ms (gain 10-100x)
- **Supervised:** 2-5ms
- **Hybrid:** 5-15ms

## Optimisations GPU (RTX 3060)

Le module `training/train.py` inclut:
- **Mixed Precision Training (AMP):** Accélération ~2x, réduction mémoire
- **DataLoader optimisé:** `pin_memory=True`, `num_workers=4`
- **Batch size adaptatif:** 64 par défaut (ajustable selon VRAM)
- **AdamW optimizer:** Meilleure généralisation
- **ReduceLROnPlateau:** Ajustement automatique du learning rate

## Troubleshooting

### Erreur "No module named 'torch'"
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Erreur "CUDA out of memory"
Réduire le batch size:
```bash
python training/train.py --batch-size 32
```

### Pygame ne s'affiche pas
Vérifier que vous n'êtes pas en SSH sans X11 forwarding.

### Modèle CNN non disponible
Entraîner d'abord:
```bash
python training/generate_dataset.py
python training/train.py --difficulty medium
```

## Références

- **OR-Tools:** https://developers.google.com/optimization
- **PyTorch:** https://pytorch.org/
- **Pygame:** https://www.pygame.org/

## Contact

Pour questions ou suggestions, ouvrir une issue sur le repo.
