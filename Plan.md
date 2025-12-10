# Plan de Réalisation : Problème des Mariages Stables

Ce document détaille les étapes pour réaliser le projet "Stable Marriage" en comparant l'approche algorithmique classique et l'approche par programmation par contraintes (CSP).

## Phase 1 : Mise en place et Approche Classique (Gale-Shapley)

**Objectif :** Comprendre le problème et avoir une solution de référence ("Ground Truth") pour vérifier les résultats futurs.

### Étape 1.1 : Environnement de développement
- **Technologie :** Python 3.x.
- **Pourquoi :** Langage standard pour l'IA et le prototypage rapide.
- **Action :** Créer un environnement virtuel (`venv`) et installer `numpy` (pour la génération de données) et `jupyter`.

### Étape 1.2 : Génération de données
- **Action :** Écrire un script pour générer des instances aléatoires du problème :
    - $N$ hommes et $N$ femmes.
    - Chaque personne a une liste de préférences ordonnée (permutation de l'autre ensemble).
- **Livrable :** Une fonction `generate_preferences(n)` qui retourne deux matrices de préférences.

### Étape 1.3 : Implémentation de Gale-Shapley
- **Technologie :** Python (Standard Library).
- **Pourquoi :** C'est l'algorithme polynomial de référence (1962) qui garantit une solution stable.
- **Action :** Implémenter l'algorithme "Men-proposing" (ou "Women-proposing").
- **Livrable :** Une fonction `gale_shapley(men_prefs, women_prefs)` qui retourne les paires formées.

---

## Phase 2 : Approche Programmation par Contraintes (CSP)

**Objectif :** Modéliser le problème de manière déclarative et laisser un solveur trouver la solution.

### Étape 2.1 : Choix du Solveur
- **Technologie :** Google OR-Tools (`ortools.sat.python.cp_model`).
- **Pourquoi :** Très performant, s'intègre parfaitement en Python, et plus flexible que MiniZinc pour ce type de projet mixte.

### Étape 2.2 : Modélisation CSP
- **Action :** Définir le modèle :
    - **Variables :** `x[m]` = la femme assignée à l'homme `m`.
    - **Domaines :** Chaque variable prend une valeur entre `0` et `N-1`.
    - **Contraintes :**
        1. *Bijection :* `AllDifferent(x)` (chaque femme est prise une seule fois).
        2. *Stabilité :* C'est le cœur du sujet. Pour toute paire (Homme `m`, Femme `w`) qui n'est PAS mariée ensemble, il est faux que (`m` préfère `w` à sa femme actuelle ET `w` préfère `m` à son mari actuel).
- **Livrable :** Une classe ou fonction `solve_stable_marriage_csp(men_prefs, women_prefs)`.

---

## Phase 3 : Analyse et Comparaison

**Objectif :** Comparer les performances et la validité des deux approches.

### Étape 3.1 : Validation
- **Action :** Vérifier que la solution trouvée par le CSP est bien stable (en utilisant une fonction de vérification) et comparer avec le résultat de Gale-Shapley.
- **Note :** Il peut y avoir plusieurs mariages stables possibles. Gale-Shapley favorise le côté qui propose. Le CSP peut en trouver d'autres selon la stratégie de recherche.

### Étape 3.2 : Benchmarking
- **Technologie :** `time`, `matplotlib`.
- **Action :** Mesurer le temps d'exécution pour $N = 10, 50, 100, 500, 1000$.
- **Livrable :** Un graphique comparant le temps d'exécution de Gale-Shapley vs OR-Tools.

---

## Phase 4 : Visualisation (Bonus/Valeur Ajoutée)

**Objectif :** Rendre les résultats intelligibles graphiquement.

### Étape 4.1 : Graphes Bipartis
- **Technologie :** `NetworkX` et `Matplotlib`.
- **Pourquoi :** NetworkX est la référence pour la manipulation de graphes en Python.
- **Action :** Dessiner deux colonnes de nœuds (Hommes/Femmes) et tracer les arêtes correspondant aux mariages trouvés.

---

## Phase 5 : Extensions (Pour aller plus loin)

**Objectif :** Explorer les variantes mentionnées dans le sujet.

### Étape 5.1 : Listes incomplètes
- **Concept :** Certaines personnes préfèrent rester seules plutôt que d'être avec certaines personnes.
- **Action :** Adapter le modèle CSP pour autoriser la non-affectation.

### Étape 5.2 : Variantes d'optimisation
- **Concept :** Parmi tous les mariages stables possibles, trouver celui qui maximise la satisfaction globale ("Egalitarian Stable Matching").
- **Action :** Ajouter une fonction objectif au modèle OR-Tools (minimiser la somme des rangs des partenaires).