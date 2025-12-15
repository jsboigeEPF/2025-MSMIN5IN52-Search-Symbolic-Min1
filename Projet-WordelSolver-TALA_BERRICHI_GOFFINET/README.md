# 🧩 Wordle Solver

## Description

**Wordle Solver** est une application web interactive qui aide les utilisateurs à résoudre le célèbre jeu **Wordle** grâce à plusieurs stratégies complémentaires :

* **CSP Solver** : résolution par programmation par contraintes (*Constraint Satisfaction Problem*).
* **LLM Solver** : suggestions générées par un modèle de langage (LLM).
* **CSP + LLM** : approche hybride combinant rigueur algorithmique et raisonnement linguistique.

L’application permet de jouer à Wordle directement dans le navigateur, de comparer les solveurs et de suivre ses performances dans une interface moderne et responsive.

---

## ✨ Fonctionnalités

* 🎮 Jouer à Wordle directement depuis le navigateur.
* 🤖 Suggestions automatiques de mots via :

  * CSP Solver
  * LLM Solver
  * CSP + LLM Solver
  
* 🧠 Évaluation automatique des propositions (vert / jaune / gris).
* 🕒 Historique des mots joués et de leurs résultats.
* 🌙 Thème clair / sombre.
* 📱 Interface moderne, responsive et accessible.

---

## 🛠️ Tech Stack

### Frontend

* **React 19**
* **Tailwind CSS**
* **Sonner** (notifications)

### Backend

* **Python – FastAPI** *(ou Node.js + Express selon la version)*
* API pour :

  * Évaluation des mots
  * Suggestions CSP / LLM / CSP+LLM

### Autres

* **LLM** (ex. Gemini) pour la génération de suggestions intelligentes
* **CSP Solver** pour Wordle (contraintes sur lettres, positions et occurrences)
* **MongoDB** *(optionnel)* pour le stockage des statistiques

---

## 🚀 Installation

### 1️⃣ Cloner le dépôt

```bash
git clone https://github.com/Safae-Berr/2025-MSMIN5IN52-Search-Symbolic-Min1.git
cd Projet-WordelSolver-TALA_BERRICHI_GOFFINET
```

---

### 2️⃣ Backend

```bash
# Naviguer vers le dossier backend
cd backend

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
# Sur Windows:
venv\Scripts\activate
# Sur Mac/Linux:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement 
copy .env.exemple .env

# Le backend sera disponible sur :
http://localhost:8000
```

---

### 3️⃣ Frontend

```bash
cd frontend
# Installer les dépendances
npm install

# Lancer le serveur
npm run dev
```

Ouvrez ensuite votre navigateur sur :
http://localhost:5173

---

## 🎯 Utilisation

1. Cliquez sur les lettres du clavier virtuel (ou utilisez le clavier physique).
2. Appuyez sur **Entrée** pour soumettre un mot.
3. Choisissez un solver :

   * **CSP** : calcule la meilleure suggestion basée sur des contraintes.
   * **LLM** : génère une suggestion via un modèle de langage.
   * **CSP + LLM** : combine les deux approches pour un choix optimal.
4. Analysez le feedback sur le plateau :

   * 🟩 **Vert** : lettre correcte et bien placée.
   * 🟨 **Jaune** : lettre correcte mais mal placée.
   * ⬜ **Gris** : lettre absente du mot.

---

## 📁 Structure du projet

```text
Projet-WordelSolver-TALA_BERRICHI_GOFFINET/
├── backend/
│   ├── notebooks/                    # Tests exploratoires, debug (Jupyter)
│   │
│   ├── app/
│   │   ├── _init_.py
│   │   │
│   │   ├── main.py                   # Point d’entrée FastAPI
│   │   │
│   │   ├── config.py                 # Config globale (CORS, env, clés API)
│   │   │
│   │   ├── routes/
│   │   │   ├── _init_.py
│   │   │   ├── wordle.py             # Routes Wordle (CSP / CSP+LLM / jeu)
│   │   │   └── llm.py                # Routes LLM isolées (optionnel)
│   │   │
│   │   ├── services/
│   │   │   ├── _init_.py
│   │   │   ├── csp_solver.py         # CSP pur + WordleConstraints
│   │   │   ├── csp_llm_solver.py     # Solveur hybride CSP + LLM
│   │   │   ├── game_manager.py       # ⭐ État du jeu Wordle (secret, tentatives)
│   │   │   ├── llm_service.py        # Intégration Gemini / OpenAI
│   │   │   └── utils.py              # Fallback, scoring, helpers
│   │   │
│   │   ├── data/
│   │   │   ├── _init_.py
│   │   │   ├── load_fr_word.py       # Dictionnaire FR
│   │   │   ├── load_en_word.py       # Dictionnaire EN
│   │   │   └── word_generator.py     # choose_secret_word()
│   │   │
│   │   ├── models/
│   │   │   ├── _init_.py
│   │   │   └── schemas.py            # Pydantic (Feedback, Request, Response)
│   │
│   ├── tests/
│   │   ├── test_csp.py               # Tests unitaires CSP
│   │   ├── test_hybrid.py            # Tests CSP+LLM
│   │   ├── test_game_manager.py      # Tests logique Wordle réelle
│   │   └── test_api.py               # Tests endpoints FastAPI
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
frontend/
├─ src/
│  ├─ components/
│  │  ├─ GameBoard.jsx        # Grille Wordle (6 x 5)
│  │  ├─ GameTile.jsx         # Case individuelle (lettre + couleur)
│  │  ├─ Keyboard.jsx         # Clavier virtuel Wordle
│  │  ├─ SolverPanel.jsx     # Choix solveur (CSP / CSP+LLM)
│  │  └─ GameStats.jsx       # Tentatives, état victoire/défaite
│  │
│  ├─ utils/
│  │  ├─ api.js              # 🔌 Appels backend (guess, start, reset)
│  │  ├─ feedback.js         # Conversion feedback backend → UI
│  │  └─ constants.js        # WORD_LENGTH, MAX_ATTEMPTS
│  │
│  ├─ App.jsx                # État global du jeu
│  └─ main.jsx               # Bootstrap React
│
├─ package.json
├─ tailwind.config.js
└─ README.mdfrontend/
├─ src/
│  ├─ components/
│  │  ├─ GameBoard.jsx        # Grille Wordle (6 x 5)
│  │  ├─ GameTile.jsx         # Case individuelle (lettre + couleur)
│  │  ├─ Keyboard.jsx         # Clavier virtuel Wordle
│  │  ├─ SolverPanel.jsx     # Choix solveur (CSP / CSP+LLM)
│  │  └─ GameStats.jsx       # Tentatives, état victoire/défaite
│  │
│  ├─ utils/
│  │  ├─ api.js              # 🔌 Appels backend (guess, start, reset)
│  │  ├─ feedback.js         # Conversion feedback backend → UI
│  │  └─ constants.js        # WORD_LENGTH, MAX_ATTEMPTS
│  │
│  ├─ App.jsx                # État global du jeu
│  └─ main.jsx               # Bootstrap React
│
├─ package.json
├─ tailwind.config.js
└─ README.md
```

---

## Collaborateurs : 
Safae BERRICHI
Lamyae TALA 
Pauline GOFFINET

## 📜 Licence

Ce projet est open-source. Vous pouvez l’utiliser, le modifier et le distribuer librement.
👨‍💻 Projet académique / expérimental autour de l’IA, des CSP et du développement web moderne.