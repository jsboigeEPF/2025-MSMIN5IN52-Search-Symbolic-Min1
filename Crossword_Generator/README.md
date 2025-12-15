# 🎯 Générateur de Mots-Croisés

Un générateur intelligent de mots-croisés utilisant la **programmation par contraintes** (CSP) avec OR-Tools CP-SAT et une interface web interactive développée avec Flask.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-green)
![OR-Tools](https://img.shields.io/badge/OR--Tools-9.0%2B-orange)


## ✨ Fonctionnalités

### 🎨 Éditeur de Grille Interactif
- Création de grilles personnalisées (3×3 à 15×15)
- 5 motifs prédéfinis (mini, standard, classique, medium)
- Éditeur visuel avec clic pour placer/retirer les cases noires
- Redimensionnement dynamique du panneau
- Statistiques en temps réel (cases, emplacements, intersections)

### 🧩 Génération Intelligente
- **Solveur CSP** avec OR-Tools CP-SAT
- Dictionnaire français de ~140 000 mots
- Téléchargement automatique du dictionnaire
- Contraintes d'intersections entre mots
- Génération en moins de 30 secondes

### 📖 Définitions Automatiques
- Récupération depuis **Wiktionnaire** (API gratuite)
- Fallback sur **Dicolink**
- Cache local pour performances optimales
- Définitions claires et concises

### 🎮 Mode Jeu Immersif
- Interface plein écran épurée
- Navigation clavier et souris
- Vérification en temps réel
- Système d'indices (lettre/mot)
- Score et statistiques
- Indicateur de direction (H/V)
- Détection automatique de victoire

### 📊 Page Solution
- Affichage de la grille complète
- Définitions organisées par direction
- Numérotation comme les vrais mots-croisés
- Passage facile entre solution et jeu

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Installation des dépendances

```bash
# Cloner le dépôt
git clone https://github.com/tjehanne/Crossword_Generator.git
cd Crossword_Generator/Crossword_Generator

# Installer les dépendances
pip install -r requirements.txt
```

### Dépendances principales

```
Flask>=3.0.0
ortools>=9.0.0
```

Le dictionnaire français sera **téléchargé automatiquement** au premier lancement (~140k mots, 2-3 Mo).

## 💻 Utilisation

### Lancement rapide

```bash
# Démarrer le serveur web
python web_interface.py
```

Le serveur démarre sur `http://127.0.0.1:5000` et ouvre automatiquement votre navigateur.



### Workflow de création

1. **Créer/Charger une grille**
   - Choisir un motif prédéfini
   - Ou créer une grille personnalisée (définir lignes/colonnes)
   - Cliquer sur les cases pour les rendre noires/blanches

2. **Générer la grille**
   - Cliquer sur "🔍 Générer la Grille"
   - Attendre la résolution (quelques secondes)
   - Voir les statistiques et le résultat

3. **Jouer**
   - Cliquer sur "🎮 Jouer" pour le mode jeu
   - Remplir les cases avec le clavier
   - Utiliser les indices si nécessaire
   - Consulter la solution avec "📊 Solution"

## 🏗️ Architecture

```
Crossword_Generator/
├── web_interface.py          # Serveur Flask et routes
├── crossword_solver.py       # Point d'entrée principal
├── solver/                   # Package du solveur
│   ├── __init__.py          # Exports des classes
│   ├── models.py            # Slot, Intersection
│   ├── grid.py              # CrosswordGrid (structure)
│   ├── dictionary.py        # WordDictionary (chargement/filtrage)
│   ├── definitions.py       # DefinitionService (Wiktionnaire, cache)
│   ├── solver.py            # CrosswordSolver (CSP avec CP-SAT)
│   └── patterns.py          # GRID_PATTERNS (motifs prédéfinis)
├── templates/               # Templates HTML
│   └── index.html          # Interface principale
├── static/                  # Assets statiques
│   ├── css/
│   │   └── style.css       # Styles (1271 lignes)
│   └── js/
│       └── app.js          # JavaScript (1134 lignes)
└── .dict_cache/            # Cache (généré automatiquement)
    ├── french_words.txt    # Dictionnaire téléchargé
    └── definitions_cache.json  # Cache des définitions
```

### Modules principaux

#### 🧩 `CrosswordGrid` (`grid.py`)
- Représentation de la grille (cases noires/blanches)
- Extraction des slots (emplacements de mots)
- Détection des intersections
- Affichage de la solution

#### 📚 `WordDictionary` (`dictionary.py`)
- Chargement intelligent du dictionnaire
- Téléchargement automatique depuis GitHub
- Filtrage par longueur et pattern
- Index par lettre/position pour recherche rapide

#### 📖 `DefinitionService` (`definitions.py`)
- API Wiktionnaire (gratuite, illimitée)
- API Dicolink (fallback)
- Cache local (JSON)
- Génération de variantes avec accents

#### 🔧 `CrosswordSolver` (`solver.py`)
- Modélisation CSP avec OR-Tools CP-SAT
- Variables : choix de mot par slot
- Contraintes : lettres identiques aux intersections
- Optimisations : pré-filtrage, arc-consistency
- Limite : 500 mots max par slot

## 🛠️ Technologies

### Backend
- **Python 3.8+** : Langage principal
- **Flask 3.0+** : Framework web
- **OR-Tools 9.0+** : Solveur CSP (CP-SAT)

### Frontend
- **HTML5/CSS3** : Structure et style
- **JavaScript ES6** : Logique interactive
- **Design responsive** : Grilles CSS Grid et Flexbox

### APIs externes
- **Wiktionnaire API** : Définitions françaises
- **Dicolink API** : Définitions fallback
- **Lexique.org** : Source du dictionnaire

### Algorithmes
- **Constraint Satisfaction Problem (CSP)**
- **Arc-consistency** (pré-filtrage)
- **Backtracking** avec heuristiques
- **CP-SAT Solver** (Google OR-Tools)

### Éditeur de Grille
Interface intuitive pour créer des grilles personnalisées avec motifs prédéfinis.

### Mode Jeu
Expérience immersive avec définitions, indices, et vérification automatique.

### Page Solution
Affichage complet de la solution avec numérotation et définitions organisées.

## 🤝 Contexte du projet
- Projet développé dans le cadre du cours **IA 2 - EPF 5A**
- Date : Décembre 2025

**Bon jeu ! 🎯🧩**
