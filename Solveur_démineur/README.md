# Solveur de Démineur par Programmation par Contraintes

## 🎯 Objectif du Projet

**Développer un solveur automatique du Démineur utilisant la programmation par contraintes (CSP) pour maximiser le taux de victoire sur différentes difficultés de grilles.**

Le défi principal : transformer un jeu combinatoire en un problème CSP, utiliser la propagation de contraintes pour les déductions logiques certaines, et calculer des probabilités exactes lorsque plusieurs configurations restent possibles.

### Objectifs Mesurables
- **Taux de victoire cible** : >95% (débutant), >85% (intermédiaire), >45% (expert)
- **Performance** : Décision en <100ms par coup
- **Qualité** : Maximiser l'utilisation de déductions logiques vs paris probabilistes

---

## 🔬 Modélisation CSP

### Principe
Chaque case inconnue = **variable booléenne** $X_i \in \{0,1\}$ (0=pas mine, 1=mine)

Chaque case révélée avec valeur $n$ = **contrainte de somme** sur ses voisins :
$$\sum_{i \in \text{voisins}} X_i = n$$

Contrainte globale optionnelle : $\sum_i X_i = M$ (nombre total de mines)

### Résolution
1. **Propagation AC-3** : Réduire les domaines automatiquement
2. **Backtracking intelligent** : Énumérer les solutions avec heuristiques MRV/LCV
3. **Calcul de probabilités exactes** : $P(\text{mine}) = \frac{\text{solutions où mine}}{\text{total solutions}}$
4. **Décomposition** : Résoudre les composantes connexes indépendamment

---

## 🎯 Objectifs Pédagogiques

1. **Modélisation CSP** : Variables, domaines, contraintes
2. **Propagation de contraintes** : Arc-consistency (AC-3)
3. **Backtracking intelligent** : Heuristiques MRV, Degree, LCV
4. **Complexité** : Comprendre un problème NP-complet en pratique
5. **Solveurs modernes** : OR-Tools CP-SAT, Z3

---

## 🧠 Approches Envisagées

### 1. **Solveur CSP Complet (Approche Principale)**
Modélisation complète avec propagation AC-3 + backtracking + calcul probabilités exactes.
- ✅ **Déductions logiques garanties** 
- ✅ **Probabilités exactes** via énumération solutions
- ⚠️ Coûteux en calcul sur grandes régions ambiguës
- **Technologies** : OR-Tools CP-SAT (recommandé), python-constraint, Z3

### 2. **Solveur Baseline (Règles Simples)**
Règles AFN/AMN + probabilités naïves locales.
- ✅ Très rapide, simple (~100 lignes)
- ❌ Ignore contraintes croisées, taux victoire ~60%
- **Utilité** : Comparaison et validation

### 3. **Solveur CSP Optimisé (Composantes Connexes)**
Décomposition en sous-problèmes indépendants pour gain exponentiel.
- ✅ **Gain ×10 à ×100** en vitesse vs CSP naïf
- ✅ Maintient les garanties de correction
- **Optimisation clé** pour grilles expertes

### 4. **Apprentissage Supervisé (CNN) ✅ IMPLÉMENTÉ**
CNN entraîné sur parties du solveur expert CSP.
- ✅ **Rapide à l'inférence** : ~2-5ms par coup
- ✅ **Optimisé GPU** : Mixed precision pour RTX 3060
- ✅ **Hybride disponible** : CSP pour coups certains + CNN pour ambigus
- **Technologies** : PyTorch, CUDA

### 5. **Visualisation Interactive ✅ IMPLÉMENTÉ**
Interface Pygame avec heatmaps, overlays probabilités, composantes connexes.
- ✅ **Mode temps réel** avec contrôles (pause, step-by-step)
- ✅ **Heatmap** : vert (sûr) → jaune → rouge (danger)
- ✅ **Voir la "pensée" des modèles** en temps réel
- **Objectif** : Pédagogie, debug, et compréhension

---

## 📊 Évaluation

**Benchmarks** : 1000+ parties par difficulté (débutant 9×9, intermédiaire 16×16, expert 30×16)

**Métriques clés** :
- Taux de victoire par difficulté
- Temps de décision moyen/max
- % déductions logiques vs paris probabilistes
- Taille composantes connexes, profondeur backtracking

---

## 🗂️ Structure du Projet
      # Classe Board : logique du jeu
│   ├── visualizer.py               # Visualisation basique
│   └── interactive_visualizer.py   # ✅ Visualisation avancée (Approche 5)
│
├── solvers/
│   ├── base_solver.py              # Classe abstraite pour tous les solveurs
│   ├── simple_solver.py            # Règles AFN/AMN + probabilités naïves
│   ├── ortools_solver.py           # Solveur CSP avec OR-Tools CP-SAT
│   ├── optimized_solver.py         # ✅ CSP + composantes connexes (Approche 3)
│   └── supervised_solver.py        # ✅ CNN + Hybride (Approche 4)
│
├── csp/
│   ├── constraint_builder.py       # Construction des contraintes
│   ├── probability.py              # Calcul de probabilités exactes
│   └── components.py               # ✅ Détection composantes connexes
│
├── training/                       # ✅ Module ML (Approche 4)
│   ├── generate_dataset.py         # Génération de datasets depuis expert CSP
│   ├── model.py                    # Architectures CNN (ResNet, standard)
│   └── train.py                    # Pipeline entraînement GPU (RTX 3060)
│
├── demo.py                         # ✅ Script de démo interactive
├── benchmark_all_solvers.py        # ✅ Benchmarking complet
├── compare_solvers.py              # Comparaison de base
└── USAGE.md                        # ✅ Guide d'utilisation détaillé
└── notebooks/
    ├── csp_exploration.ipynb # Exploration de la modélisation CSP
    ├── performance.ipynb     # Analyse des performances
    └── visualization.ipynb   # Visualisation des stratégies
```

---

## 📚 Références

- **Bayer & Snyder (2013)** : *A Constraint-Based Approach to Solving Minesweeper*
- **Kaye (2000)** : *Minesweeper is NP-complete*
- **OR-Tools** : [developers.google.com/optimization](https://developers.google.com/optimization)
- **Russell & Norvig** : *AI: A Modern Approach* - Chapitre 6 CSP

---

## 🛠️ Technologies

**Python 3.8+** | OR-Tools 9.5+ | Pygame 2.0+ | NumPy | Matplotlib

```bash
pip install ortools pygame numpy matplotlib python-constraint z3-solver
```

---

*Projet Démarrage Rapide

### Installation
```bash
# Installer les dépendances
pip install -r requirements.txt

# Pour support GPU (RTX 3060)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Démo Interactive
```bash
# Lancer une démo avec le solveur optimisé
python demo.py

# Avec un solveur spécifique
python demo.py --solver optimized  # Approche 3
python demo.py --solver supervised # Approche 4 (nécessite modèle entraîné)
python demo.py --solver hybrid     # Approche 4 hybride

# Difficulté expert
python demo.py --width 30 --height 16 --mines 99
```

**Contrôles:**
- `ESPACE` - Pause/Reprendre
- `S` - Step-by-step  
- `P` - Toggle probabilités
- `H` - Toggle heatmap
- `C` - Toggle composantes connexes
- `+/-` - Vitesse

### Entraîner le CNN
```bash
# Générer les datasets
python training/generate_dataset.py

# Entraîner (optimisé pour RTX 3060)
python training/train.py --difficulty medium --epochs 50
```

### Benchmarking
```bash
# Comparer tous les solveurs
python benchmark_all_solvers.py
```

📖 **Guide complet:** Voir [USAGE.md](USAGE.md)

---

## 🛠️ Technologies

**Python 3.8+** | OR-Tools 9.5+ | PyTorch 2.0+ (CUDA) | Pygame 2.0+ | NumPy | Matplotlib

---

## ✅ État du Projet

- ✅ **Approche 1-2** : Solveurs simple et CSP (implémentés par collègues)
- ✅ **Approche 3** : CSP Optimisé avec composantes connexes
- ✅ **Approche 4** : Apprentissage supervisé (CNN) + Hybride
- ✅ **Approche 5** : Visualisation interactive avec heatmaps
- ✅ **Optimisation GPU** : Mixed precision pour RTX 3060
- 🔄 **Tests** : En cours