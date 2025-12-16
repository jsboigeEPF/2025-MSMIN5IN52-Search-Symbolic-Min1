# Guide d'Utilisation - Solveur de Démineur CSP

## 🚀 Installation

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# Ou individuellement :
pip install ortools pygame numpy
```

## 🎮 Lancement

```bash
python main.py
```

## 🎯 Fonctionnalités Implémentées

### ✅ Phase 1 : Fondations
- **`game/board.py`** : Logique complète du démineur
  - Génération de grilles avec évitement du premier clic
  - Révélation récursive (flood fill)
  - Détection de victoire/défaite
  
- **`game/visualizer.py`** : Interface Pygame interactive
  - Affichage grille avec couleurs
  - Overlay des probabilités (pourcentages)
  - Highlight de la case sélectionnée
  - Zone d'information avec stats

### ✅ Phase 2 : Moteur CSP
- **`csp/constraint_builder.py`** : Construction contraintes
  - Variables = cases cachées
  - Contraintes de somme sur les voisins
  - Simplification automatique (AFN/AMN)
  
- **`csp/probability.py`** : Calcul probabilités exactes
  - Énumération de toutes les solutions
  - P(mine) = nb_solutions_avec_mine / total_solutions

### ✅ Phase 3 : Solveur OR-Tools
- **`solvers/ortools_solver.py`** : Solveur CSP complet
  - Modélisation CP-SAT
  - Énumération jusqu'à 1000 solutions
  - Choix optimal (probabilité minimale)
  - Distinction déductions logiques / paris

## 🎨 Interface Graphique

### Affichage
- **Cases grises** : Cachées (avec probabilités si activées)
- **Cases blanches** : Révélées avec chiffres
- **Cases rouges** : Mines (défaite)
- **Contour vert** : Case sélectionnée par le solveur
- **Pourcentages** : Probabilité qu'une case contienne une mine

### Contrôles
- **ESPACE** : Jouer le prochain coup (mode pas-à-pas)
- **P** : Activer/désactiver l'affichage des probabilités
- **Q** : Quitter l'application

## 📊 Statistiques Affichées

À la fin de chaque partie :
- **Coups joués** : Nombre total de cases révélées
- **Déductions logiques** : Cases révélées avec certitude (prob = 0%)
- **Paris probabilistes** : Cases révélées par calcul de probabilités
- **Ratio logique/paris** : Indique la qualité des déductions

## 🧪 Configuration des Difficultés

Dans `main.py`, ligne 20-23 :

```python
# Débutant : 9x9, 10 mines
WIDTH = 9
HEIGHT = 9
NUM_MINES = 10

# Intermédiaire : 16x16, 40 mines
# WIDTH = 16
# HEIGHT = 16
# NUM_MINES = 40

# Expert : 30x16, 99 mines
# WIDTH = 30
# HEIGHT = 16
# NUM_MINES = 99
```

## 🔬 Approche CSP Implémentée

### Modélisation
- **Variables** : $X_i \in \{0, 1\}$ pour chaque case cachée
- **Contraintes** : $\sum_{i \in \text{voisins}} X_i = n$ pour chaque case révélée

### Algorithme
1. **Construction** : Extraire variables et contraintes de la grille
2. **Simplification** : Détecter cases évidentes (AFN/AMN)
3. **Résolution CP-SAT** : Énumérer toutes les solutions valides
4. **Calcul probabilités** : P(mine) via comptage de solutions
5. **Décision** : Choisir la case avec probabilité minimale

### Optimisations
- Timeout de 1 seconde sur le solveur
- Maximum 1000 solutions énumérées
- Simplification des contraintes avant résolution

## 📈 Performances Attendues

### Taux de Victoire Cibles
- **Débutant (9×9, 10 mines)** : >95%
- **Intermédiaire (16×16, 40 mines)** : >85%
- **Expert (30×16, 99 mines)** : >45%

### Temps de Décision
- **Débutant** : <50ms par coup
- **Intermédiaire** : <200ms par coup
- **Expert** : <1s par coup

## 🐛 Debugging

Si la fenêtre ne s'affiche pas :
```bash
# Vérifier l'installation de Pygame
python -c "import pygame; print(pygame.version.ver)"

# Sur macOS, vous devrez peut-être autoriser l'accès à l'écran
```

## 📁 Structure du Projet

```
Solveur_Demineur/
├── game/
│   ├── __init__.py
│   ├── board.py          # Logique du démineur
│   └── visualizer.py     # Interface Pygame
├── csp/
│   ├── __init__.py
│   ├── constraint_builder.py  # Construction contraintes
│   └── probability.py    # Calcul probabilités
├── solvers/
│   ├── __init__.py
│   ├── base_solver.py    # Classe abstraite
│   └── ortools_solver.py # Solveur CSP OR-Tools
├── main.py               # Script principal
├── requirements.txt      # Dépendances
└── README.md            # Documentation
```

## 🎓 Concepts Pédagogiques Démontrés

1. **Modélisation CSP** : Transformation d'un jeu en problème de contraintes
2. **Propagation** : Simplification via AFN/AMN
3. **Énumération** : Backtracking avec OR-Tools CP-SAT
4. **Probabilités exactes** : Comptage de solutions
5. **Heuristiques** : Choix de la case optimale

## 🔮 Extensions Futures

- Mode automatique (touche A)
- Restart sans fermer (touche R)
- Décomposition en composantes connexes
- Benchmarks sur 1000+ parties
- Graphiques de performance
- Solveur baseline pour comparaison

---

**Projet - Solveur CSP de Démineur - 2025**
