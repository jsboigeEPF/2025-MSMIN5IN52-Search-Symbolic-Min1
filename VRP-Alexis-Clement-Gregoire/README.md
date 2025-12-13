# Optimisation de Tournées de Livraison (VRP)

## 📋 Table des matières

1. [Présentation](#présentation)
2. [Installation](#installation)
3. [Utilisation](#utilisation)
4. [Tests](#tests)
5. [Contexte théorique](#contexte-théorique)
6. [Architecture technique](#architecture-technique)
7. [Performances](#performances)
8. [Qualité du code](#qualité-du-code)

---

## 🎯 Présentation

Ce projet propose une solution complète pour l'optimisation de tournées de véhicules (Vehicle Routing Problem, VRP) avec une interface web interactive. Le système supporte deux variantes principales :

- **VRP Classique** : optimisation avec contraintes de capacité et fenêtres temporelles
- **VRP Vert (E-VRP)** : optimisation pour véhicules électriques avec contraintes d'autonomie et stations de recharge

### Fonctionnalités principales

- ✅ Interface web interactive avec visualisation cartographique
- ✅ Résolution en temps réel avec suivi de progression
- ✅ Support de multiples véhicules
- ✅ Contraintes de capacité et fenêtres temporelles
- ✅ Gestion de l'autonomie pour véhicules électriques
- ✅ Visualisation des tournées sur carte interactive

### Technologies utilisées

- **Backend** : Python 3.12+, Flask, OR-Tools CP-SAT
- **Frontend** : HTML5, JavaScript, Leaflet.js
- **Optimisation** : Google OR-Tools (Constraint Programming)
- **Visualisation** : Folium, Leaflet

---

## 🚀 Installation

### Prérequis

- Python 3.12 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner le dépôt** (si applicable) ou naviguer vers le répertoire du projet

2. **Créer un environnement virtuel** (recommandé)

```bash
python -m venv venv
```

3. **Activer l'environnement virtuel**

   - Sur Windows (PowerShell) :
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   - Sur Linux/Mac :
   ```bash
   source venv/bin/activate
   ```

4. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

---

## 💻 Utilisation

### Démarrage de l'application

```bash
python main.py
```

L'application démarre sur `http://localhost:5000`

### Interface web

1. **Ouvrir le navigateur** à l'adresse `http://localhost:5000`
2. **Configurer le problème** :
   - Cliquer sur la carte pour définir le dépôt (point de départ)
   - Ajouter des clients en cliquant sur la carte
   - Pour le VRP vert, ajouter des stations de recharge
   - Configurer les paramètres (nombre de véhicules, capacité, etc.)
3. **Lancer l'optimisation** : cliquer sur "Résoudre"
4. **Visualiser les résultats** : les tournées s'affichent automatiquement sur la carte

### Paramètres configurables

- **Nombre de véhicules** : nombre de véhicules disponibles
- **Capacité** : capacité maximale de chaque véhicule (1 client = 10 unités de capacité)
- **Limite de temps** : temps maximum alloué à la résolution (en secondes)
- **Type VRP** : classique ou vert (électrique)
- **Autonomie** : pour VRP vert, autonomie maximale de la batterie

---

## 🧪 Tests

### Tests manuels

1. **Test de démarrage** :
   ```bash
   python main.py
   ```
   Vérifier que le serveur démarre sans erreur et que l'interface est accessible.

2. **Test de résolution simple** :
   - Créer un problème avec 3-5 clients
   - Lancer la résolution
   - Vérifier que des tournées sont générées

3. **Test VRP vert** :
   - Sélectionner le mode "VRP Vert"
   - Ajouter au moins une station de recharge
   - Vérifier que les contraintes d'autonomie sont respectées

### Tests de validation

Le système valide automatiquement :
- ✅ Cohérence des données d'entrée
- ✅ Respect des contraintes (capacité, fenêtres temporelles, autonomie)
- ✅ Génération de solutions réalisables

### Exemples de problèmes

**Problème simple** :
- 1 dépôt
- 5 clients
- 1 véhicule, capacité 50
- Temps limite : 10 secondes

**Problème complexe** :
- 1 dépôt
- 15 clients
- 3 véhicules, capacité 100
- Fenêtres temporelles
- Temps limite : 30 secondes

---

## 📚 Contexte théorique

### Le problème VRP

Le **Vehicle Routing Problem (VRP)** est un problème d'optimisation combinatoire classique qui consiste à déterminer un ensemble de tournées optimales pour une flotte de véhicules devant servir un ensemble de clients à partir d'un dépôt central.

#### Formulation mathématique

Soit :
- $G = (V, E)$ un graphe avec $V = \{0, 1, ..., n\}$ (0 = dépôt, 1..n = clients)
- $d_{ij}$ : distance entre les nœuds $i$ et $j$
- $q_i$ : demande du client $i$
- $Q$ : capacité d'un véhicule
- $K$ : nombre de véhicules disponibles

**Objectif** : Minimiser la distance totale parcourue

**Contraintes** :
- Chaque client est visité exactement une fois
- Chaque véhicule part et revient au dépôt
- La somme des demandes sur une tournée ne dépasse pas $Q$
- Pas de sous-tours (connectivité)

### Variantes implémentées

#### VRP Classique (CVRP)

Extension du VRP avec :
- **Contraintes de capacité** : $\sum_{i \in T_k} q_i \leq Q$ pour chaque tournée $T_k$
- **Fenêtres temporelles** : chaque client $i$ doit être visité dans $[a_i, b_i]$
- **Temps de service** : temps nécessaire pour servir chaque client

#### VRP Vert (E-VRP)

Extension pour véhicules électriques avec :
- **Contraintes d'autonomie** : niveau de batterie $B_i \geq 0$ à chaque nœud
- **Consommation** : $B_j = B_i - c \cdot d_{ij}$ où $c$ est la consommation
- **Stations de recharge** : possibilité de recharger à $B_{max}$ dans les stations
- **Temps de recharge** : temps nécessaire pour recharger complètement

### Méthode de résolution

Le projet utilise **OR-Tools CP-SAT** (Constraint Programming - Satisfiability), une approche de programmation par contraintes qui :

1. Modélise le problème avec des variables de décision booléennes et entières
2. Définit les contraintes du problème
3. Utilise un solveur SAT pour trouver des solutions optimales ou réalisables

**Avantages** :
- Résolution exacte pour des problèmes de taille moyenne
- Gestion efficace des contraintes complexes
- Flexibilité pour ajouter de nouvelles contraintes

**Limitations** :
- Temps de résolution exponentiel dans le pire cas
- Nécessite des limites de temps pour les grands problèmes

### Complexité

- **Complexité théorique** : NP-difficile
- **Complexité pratique** : O($n! \cdot K$) dans le pire cas, mais les solveurs modernes utilisent des heuristiques efficaces

---

## 🏗️ Architecture technique

### Structure du projet

```
Optimisation-de-tournees-de-livraison-VRP/
├── main.py                 # Point d'entrée principal
├── requirements.txt        # Dépendances Python
├── backend/
│   ├── vrp_classique.py   # Implémentation VRP classique
│   └── vrp_vert.py        # Implémentation VRP vert (E-VRP)
└── frontend/
    ├── app.py             # Application Flask
    └── templates/
        └── index.html     # Interface web
```

### Modules principaux

#### `backend/vrp_classique.py`

Classe `VRPClassique` qui implémente :
- Calcul de matrice de distances euclidiennes
- Modélisation CP-SAT avec variables de décision
- Contraintes de capacité, fenêtres temporelles, flux
- Extraction et formatage des solutions

**Points clés** :
- Variables booléennes `x[i,j,k]` : véhicule $k$ va de $i$ à $j$
- Variables entières pour position, temps, charge
- Contraintes de conservation de flux et élimination de sous-tours

#### `backend/vrp_vert.py`

Classe `VRPVert` qui étend le VRP classique avec :
- Gestion des stations de recharge
- Variables de niveau de batterie
- Contraintes de consommation et recharge
- Suivi des stations visitées

**Extensions** :
- Indexation spéciale : dépôt (0), clients (1..n), stations (n+1..n+m)
- Contraintes de batterie avec recharge complète aux stations
- Temps de recharge intégré dans les fenêtres temporelles

#### `frontend/app.py`

Application Flask avec :
- Route principale `/` : rendu de l'interface
- API `/api/solve` : lancement de la résolution
- API `/api/solution/<id>` : récupération de l'état
- API `/api/solution/<id>/stream` : streaming Server-Sent Events

**Architecture asynchrone** :
- Résolution dans des threads séparés
- Mises à jour progressives pour feedback temps réel
- Gestion d'état avec dictionnaire global

#### `frontend/templates/index.html`

Interface web interactive avec :
- Carte Leaflet pour visualisation
- Gestion des événements de clic (dépôt, clients, stations)
- Communication AJAX avec le backend
- Affichage dynamique des tournées et statistiques

### Flux de données

```
Interface Web → Flask API → Thread de résolution → OR-Tools → Solution → Interface Web
```

1. L'utilisateur configure le problème sur l'interface
2. Requête POST vers `/api/solve` avec les paramètres
3. Création d'un thread de résolution
4. Instanciation de `VRPClassique` ou `VRPVert`
5. Résolution avec OR-Tools CP-SAT
6. Mises à jour progressives via `solutions_en_cours`
7. Interface récupère les résultats via polling ou SSE
8. Visualisation sur la carte Leaflet

---

## ⚡ Performances

### Métriques de performance

#### Temps de résolution

| Taille du problème | Temps moyen | Statut |
|-------------------|-------------|--------|
| 5 clients, 1 véhicule | < 1s | Optimal |
| 10 clients, 2 véhicules | 2-5s | Optimal/Feasible |
| 15 clients, 3 véhicules | 10-30s | Feasible |
| 20+ clients | 30s+ | Feasible (limite) |

**Facteurs influençant les performances** :
- Nombre de clients : impact exponentiel
- Nombre de véhicules : impact linéaire
- Contraintes (fenêtres temporelles) : augmentation modérée
- VRP vert vs classique : +20-30% de temps (contraintes supplémentaires)

#### Utilisation mémoire

- **Problèmes petits** (< 10 clients) : < 100 MB
- **Problèmes moyens** (10-20 clients) : 100-500 MB
- **Problèmes grands** (> 20 clients) : 500 MB - 2 GB

La mémoire est principalement utilisée par :
- Matrice de distances : O($n^2$)
- Variables CP-SAT : O($n^2 \cdot K$)
- Structures de données OR-Tools

### Optimisations implémentées

1. **Limite de temps** : évite les résolutions infinies
2. **Résolution asynchrone** : interface reste responsive
3. **Mises à jour progressives** : feedback utilisateur sans bloquer
4. **Conversion en entiers** : distances multipliées par 100 pour CP-SAT (meilleure performance)

### Limitations actuelles

- **Taille maximale pratique** : ~20 clients pour résolution en temps raisonnable
- **Pas de parallélisation** : résolution séquentielle
- **Pas de pré-traitement** : pas d'heuristiques de réduction du problème
- **Pas de cache** : recalcul à chaque résolution

### Améliorations possibles

- Implémentation d'heuristiques (nearest neighbor, savings)
- Parallélisation multi-thread pour plusieurs véhicules
- Cache des matrices de distances
- Pré-traitement pour éliminer les arcs impossibles
- Utilisation de solveurs hybrides (exact + heuristique)

---

## 🔍 Qualité du code

### Standards de codage

Le code suit les conventions Python (PEP 8) avec :
- Noms de variables en minuscules avec underscores
- Docstrings pour toutes les classes et méthodes principales
- Commentaires en français (conformément aux règles du projet)
- Type hints pour les signatures de fonctions

### Structure et organisation

**Points forts** :
- ✅ Séparation claire backend/frontend
- ✅ Classes bien définies avec responsabilités uniques
- ✅ Gestion d'erreurs avec try/except
- ✅ Code modulaire et réutilisable

**Exemple de structure** :

```python
class VRPClassique:
    """Classe bien documentée avec docstring"""
    
    def __init__(self, ...):
        """Initialisation claire avec type hints"""
        
    def resoudre(self, limite_temps: int = 30) -> Dict:
        """Méthode principale avec documentation"""
```

### Gestion des erreurs

- Vérification des dépendances au démarrage
- Gestion des exceptions dans les threads
- Retour de statuts explicites ('optimal', 'feasible', 'infeasible', 'erreur')
- Messages d'erreur informatifs pour l'utilisateur

### Maintenabilité

**Facilité d'extension** :
- Ajout de nouvelles contraintes : modifier les classes VRP
- Nouveaux types de VRP : créer une nouvelle classe héritant du pattern existant
- Amélioration de l'interface : templates HTML modulaires

**Documentation** :
- Docstrings pour les méthodes publiques
- Commentaires pour les sections complexes
- README complet (ce fichier)

### Points d'amélioration

1. **Tests unitaires** : ajouter des tests automatisés (pytest)
2. **Validation des entrées** : vérification plus stricte des paramètres
3. **Logging** : système de logs structuré au lieu de print
4. **Configuration** : fichier de configuration externe
5. **Documentation API** : Swagger/OpenAPI pour les endpoints

### Dépendances

Toutes les dépendances sont listées dans `requirements.txt` avec versions minimales :
- `ortools>=9.8.3296` : solveur d'optimisation
- `flask>=2.3.0` : framework web
- `folium>=0.14.0` : génération de cartes
- `numpy>=1.24.0` : calculs numériques

**Sécurité** : toutes les dépendances sont des bibliothèques Python standard et bien maintenues.

---

## 📖 Perspectives

### Améliorations futures

1. **Algorithmes avancés** :
   - Implémentation d'heuristiques (Clark-Wright, nearest neighbor)
   - Algorithmes méta-heuristiques (genetic algorithms, simulated annealing)
   - Hybridation exact/heuristique

2. **Fonctionnalités** :
   - Import/export de problèmes (formats standards)
   - Historique des solutions
   - Comparaison de solutions
   - Export des résultats (CSV, JSON, PDF)

3. **Interface utilisateur** :
   - Édition des paramètres clients (demandes, fenêtres temporelles)
   - Animation des tournées
   - Statistiques détaillées
   - Mode sombre

4. **Performance** :
   - Parallélisation
   - Cache intelligent
   - Pré-traitement automatique
   - Résolution incrémentale

5. **Extensions du problème** :
   - VRP avec time windows multiples
   - VRP avec pick-up and delivery
   - VRP multi-dépôts
   - VRP dynamique (clients apparaissant en temps réel)

### Applications réelles

Ce système peut être adapté pour :
- **Logistique urbaine** : optimisation des livraisons en ville
- **Transport scolaire** : planification des trajets de bus
- **Services à domicile** : optimisation des tournées de techniciens
- **Collecte de déchets** : planification des tournées de camions
- **Livraison e-commerce** : optimisation des tournées de livreurs

---

## 📝 Licence

Ce projet est fourni à des fins éducatives et de recherche.

---

## 👥 Auteurs

Projet développé dans le cadre du cours d'Intelligence Artificielle II - Optimisation.

---

## 📚 Références

- **OR-Tools Documentation** : https://developers.google.com/optimization
- **VRP Theory** : Toth, P., & Vigo, D. (2014). *Vehicle Routing: Problems, Methods, and Applications*
- **CP-SAT** : Perron, L., & Furnon, V. (2019). *OR-Tools*