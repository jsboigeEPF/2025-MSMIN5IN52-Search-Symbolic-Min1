# 🎯 Wordle Solver - Solveur Intelligent

Un solveur de Wordle qui combine **programmation par contraintes (CSP)** et **stratégies d'optimisation** pour résoudre n'importe quel Wordle en moins de 4 tentatives en moyenne.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![React](https://img.shields.io/badge/React-18-61dafb) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)

---

## 📖 C'est quoi ?

**Wordle Solver** est une application web interactive qui vous aide à résoudre des grilles Wordle en utilisant des algorithmes intelligents. L'application analyse chaque tentative et vous suggère les meilleurs mots à jouer en fonction des contraintes découvertes.

### Comment ça fonctionne ?

1. **Vous jouez** - Entrez un mot de 5 lettres
2. **Le moteur analyse** - Le système CSP filtre les mots possibles selon les indices (vert/jaune/gris)
3. **L'IA suggère** - Une stratégie intelligente vous propose le meilleur mot suivant
4. **Vous gagnez** - En moyenne en 3-4 tentatives !

### Technologies utilisées

- **Backend** : Python + FastAPI + OR-Tools (moteur CSP de Google)
- **Frontend** : React + Vite + Tailwind CSS
- **Algorithmes** : 6 stratégies d'optimisation (Fréquence, Entropie, Minimax, etc.)
- **Dictionnaires** : 500+ mots anglais, 2000+ mots français

---

## 🚀 Lancement Rapide (5 minutes)

### Prérequis

- Python 3.8+
- Node.js 16+
- npm

### 🎯 Option 1 : Démarrage automatique (Recommandé)

**Tout en un seul script :**

```bash
# Rendre les scripts exécutables (première fois seulement)
chmod +x start-all.sh start-backend.sh start-frontend.sh

# Lancer backend + frontend en une commande
cd wordle-solver
./start-all.sh
```

✅ L'application complète démarre automatiquement !
- Backend : **http://localhost:8000**
- Frontend : **http://localhost:3000**

**Ou lancer séparément :**

```bash
# Backend uniquement
cd wordle-solver
./start-backend.sh

# Frontend uniquement (dans un autre terminal)
cd wordle-solver
./start-frontend.sh
```

### 🔧 Option 2 : Démarrage manuel

**1. Backend (Terminal 1)**

```bash
cd backend

# Installer les dépendances
pip install -r requirements.txt
pip install -r ../requirements.txt

# Démarrer le serveur
python main.py
```

✅ Le backend est accessible sur **http://localhost:8000**

**2. Frontend (Terminal 2)**

```bash
cd frontend

# Installer les dépendances
npm install

# Démarrer l'application
npm run dev
```

✅ L'interface web est accessible sur **http://localhost:3000**

**3. Jouer**

Ouvrez votre navigateur sur **http://localhost:3000** et commencez à jouer !

---

## 🎮 Utilisation

### Interface Web

1. **Cliquez sur "Démarrer"** pour lancer une partie
2. **Choisissez votre langue** (EN/FR) et votre **stratégie** (Fréquence recommandée)
3. **Tapez un mot** avec votre clavier ou le clavier virtuel
4. **Appuyez sur Entrée** pour valider
5. **Observez les suggestions** dans le panneau de droite
6. **Cliquez sur un mot suggéré** pour l'utiliser directement

### Fonctionnalités

- 🎨 **Interface intuitive** - Grille colorée comme le vrai Wordle
- ⌨️ **Clavier virtuel** - États des lettres en temps réel (vert/jaune/gris)
- 💡 **Suggestions IA** - Le meilleur mot à jouer selon la stratégie choisie
- 📊 **Statistiques** - Nombre de mots possibles restants
- 🔍 **Visualisation** - Liste des candidats possibles
- 🌍 **Multilingue** - Support FR et EN
- 📖 **Définitions Gemini** - Obtenez la définition de n'importe quel mot via l'IA Gemini (optionnel)

---

## 🤖 Fonctionnalité Bonus : Définitions IA avec Gemini

L'application inclut une intégration avec l'API **Google Gemini** pour obtenir des définitions de mots en temps réel.

### Configuration rapide (optionnel)

1. **Obtenez une clé API gratuite** sur https://ai.google.dev/
2. **Créez un fichier `.env`** dans le dossier `wordle-solver/` :
   ```bash
   GEMINI_API_KEY=votre_clé_api_ici
   ```
3. **Installez la dépendance** :
   ```bash
   pip install google-genai
   ```
4. **Relancez le backend** - Le panneau "Définition de Mot" apparaîtra automatiquement !

> **Note** : Cette fonctionnalité est complètement optionnelle. L'application fonctionne normalement sans.

### Test rapide

```bash
# Tester l'intégration
python test_gemini_integration.py
```

---

## 🧠 Les Stratégies Disponibles

Le solveur propose 6 stratégies différentes :

| Stratégie | Description | Performance | Vitesse |
|-----------|-------------|-------------|---------|
| **Fréquence** ⭐ | Privilégie les lettres fréquentes | ~3.8 tentatives | Rapide |
| **Entropie Rapide** 🔥 | Maximise l'information (optimal) | ~3.7 tentatives | Moyen |
| **Minimax** | Minimise le pire cas | ~3.9 tentatives | Moyen |
| **Entropie** | Version exhaustive | ~3.6 tentatives | Lent |
| **Taille Attendue** | Compromis | ~3.8 tentatives | Moyen |
| **Positionnelle** | Par position de lettre | ~4.1 tentatives | Rapide |

💡 **Recommandation** : Utilisez **Fréquence** pour la rapidité ou **Entropie Rapide** pour l'optimalité.

---

## 🏗️ Architecture

```
wordle-solver/
├── backend/                 # API FastAPI
│   ├── main.py             # Serveur principal
│   └── requirements.txt
│
├── frontend/                # Application React
│   ├── src/
│   │   ├── components/     # Interface utilisateur
│   │   ├── services/       # Communication API
│   │   └── App.jsx
│   └── package.json
│
└── wordle_solver/           # Moteur Python
    ├── csp/                # Contraintes et filtrage
    ├── strategies/         # Algorithmes d'optimisation
    ├── game/               # Simulation Wordle
    └── dictionaries/       # Mots FR/EN
```

---

## 🐛 Dépannage

### Le backend ne démarre pas

```bash
# Vérifier Python
python --version  # Doit être 3.8+

# Réinstaller les dépendances
cd backend
pip install -r requirements.txt
pip install -r ../requirements.txt
```

### Le frontend ne démarre pas

```bash
# Vérifier Node.js
node --version  # Doit être 16+

# Réinstaller les dépendances
cd frontend
rm -rf node_modules
npm install
```

### Erreur de connexion backend ↔ frontend

1. Vérifiez que le backend tourne sur **http://localhost:8000**
2. Testez l'API : `curl http://localhost:8000/api/languages`
3. Vérifiez les logs du backend dans le terminal

### Port déjà utilisé

```bash
# Backend (port 8000)
lsof -ti:8000 | xargs kill -9

# Frontend (port 3000)
lsof -ti:3000 | xargs kill -9
```

### Installation sur macOS

```bash
# Utiliser python3 et pip3
python3 -m pip install -r requirements.txt
python3 main.py

# Environnement virtuel (recommandé)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🧪 Tests

```bash
# Lancer les tests
pytest

# Avec couverture
pytest --cov=wordle_solver

# Tests spécifiques
pytest tests/test_strategies.py
```

---

## 📊 Performance

Sur 100 mots anglais aléatoires :

- ✅ **Taux de victoire** : 100%
- ✅ **Moyenne** : 3.7-3.8 tentatives
- ✅ **Temps de réponse** : < 1 seconde
- ✅ **Meilleur cas** : 2 tentatives
- ✅ **Pire cas** : 6 tentatives (rare)

---

## 📚 Documentation Complémentaire

- **Stratégies détaillées** : Voir [`docs/STRATEGIES.md`](docs/STRATEGIES.md)
- **API Backend** : http://localhost:8000/docs (après démarrage)
- **Exemples Python** : Dossier `examples/`

---

## 🎯 Résumé

**En bref :**
1. Clone le projet
2. Lance le backend (`cd backend && python main.py`)
3. Lance le frontend (`cd frontend && npm run dev`)
4. Ouvre http://localhost:3000
5. Joue et gagne avec l'aide de l'IA !

**L'application résout n'importe quel Wordle en analysant les contraintes et en suggérant intelligemment les meilleurs mots à chaque étape.**

---

## 🤝 Contribution

Les contributions sont bienvenues ! Ouvrez une issue ou une PR.

## 📄 Licence

MIT License

---

**Créé pour démontrer l'efficacité de la programmation par contraintes appliquée aux jeux de mots** 🎮