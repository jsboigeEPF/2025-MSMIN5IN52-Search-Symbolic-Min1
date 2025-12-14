# Cemantix IA - README

## 📋 Vue d'ensemble

**Cemantix IA** est une application web complète pour jouer au jeu Cemantix (trouver un mot cible basé sur la similarité sémantique) avec support d'IA. **L'objectif principal de ce projet est d'utiliser un LLM (Large Language Model) pour résoudre le jeu**, même si c'est plus lent que les approches heuristiques.

Le projet est composé de trois parties :

- **Backend** : API FastAPI en Python (gestion du jeu, calcul de similarité, IA avec LLM)
- **Frontend** : Interface Angular moderne avec suggestions LLM
- **IA** : Résolution automatique utilisant Ollama (LLM local)

---

## 🎮 Fonctionnement

### Jeu Cemantix
1. Un mot cible est sélectionné aléatoirement
2. Le joueur (ou l'IA) propose des mots
3. Chaque mot reçoit un score de similarité (0-100) par rapport au mot cible
4. L'objectif : trouver le mot cible

### 🧠 Approche IA : LLM Ollama

**Ce projet utilise Ollama (LLM local) par défaut** pour résoudre le Cemantix. Le LLM raisonne sur les indices comme un humain, analysant les patterns dans l'historique des tentatives pour proposer le meilleur mot suivant.

**Ollama** : Local, gratuit, **AUCUNE clé API nécessaire !** ⭐

---

## 🛠️ Installation et mise en place

### Prérequis
- **Python 3.11+** (installez depuis https://www.python.org/downloads/)
- **Node.js 18+** (pour le frontend Angular)
- **Git**

### 1️⃣ Backend (FastAPI)

```bash
# Naviguer au dossier backend
cd backend

# Créer et activer l'environnement virtuel
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# Installer les dépendances
pip install -r requirements.txt
```

#### Modèle spaCy

Le modèle spaCy détermine la qualité du calcul de similarité sémantique. **Le code essaie automatiquement d'utiliser le meilleur modèle disponible** :

| Modèle | Taille | Qualité | Recommandation |
|--------|--------|---------|----------------|
| `fr_core_news_lg` | ~500 MB | 🌟 Excellente | **Recommandé** ⭐ |
| `fr_core_news_md` | ~100 MB | Bonne | Équilibre (fallback) |

**Installation du modèle** :
```bash
# Télécharger et installer le modèle recommandé
python -m spacy download fr_core_news_lg    # ⭐ Recommandé (meilleure qualité, scores plus précis)
```

**Comportement automatique** :

Le code dans [`backend/app/game.py`](backend/app/game.py) essaie automatiquement :
1. **D'abord** `fr_core_news_lg` (meilleure précision des scores)
2. **Sinon** `fr_core_news_md` (fallback)
3. **Sinon** erreur avec instructions

#### Configuration du LLM - Ollama

Le projet utilise **Ollama (local, gratuit) par défaut** ⭐ - **AUCUNE clé API nécessaire !**

**Étape 1 : Installer Ollama**
1. Téléchargez Ollama depuis https://ollama.ai
2. Installez-le (Windows/Mac/Linux)
3. Lancez Ollama (il démarre automatiquement en arrière-plan)

**Étape 2 : Télécharger un modèle**
```bash
# Téléchargez le modèle recommandé
ollama pull llama3.2      # Recommandé (2GB)
```

**Lancer le serveur** :
```bash
# Ollama est utilisé par défaut - aucune clé API nécessaire !
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Le backend sera accessible à `http://127.0.0.1:8000`

**Documentation API** : `http://127.0.0.1:8000/docs` (Swagger)

### 2️⃣ Frontend (Angular)

```bash
# Naviguer au dossier frontend
cd frontend/cemantix-fr

# Installer les dépendances
npm install

# Lancer le serveur de développement
ng serve
# ou
npm start
```

Le frontend sera accessible à `http://localhost:4200`

---

## 🚀 Démarrage rapide

**Prérequis** : Installer Ollama depuis https://ollama.ai et lancer `ollama pull llama3.2`

### Windows
```powershell
# Terminal 1 - Backend
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - Frontend
cd frontend/cemantix-fr
npm install
ng serve
```

### Linux/macOS
```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - Frontend
cd frontend/cemantix-fr
npm install
ng serve
```

**Note** : Le frontend propose deux boutons :
- **💡 Suggestion LLM** : Obtient une suggestion unique du LLM
- **🤖 LLM résout** : Résout automatiquement toute la partie avec le LLM (affichage en temps réel)

---

## 📡 Architecture Backend

### Fichiers clés

| Fichier | Rôle |
|---------|------|
| `app/main.py` | Application FastAPI principale, endpoints |
| `app/game.py` | Logique du jeu (scoring, gestion des parties) |
| `app/ai_solver_llm.py` | **IA LLM avec Ollama** 🎯 |
| `app/ai_solver.py` | IA heuristique (fallback si USE_LLM=false) |
| `app/vocab.txt` | Vocabulaire français (~50k mots) |

### Endpoints API

#### 🎮 Gestion du jeu
- **POST** `/start` → Démarre une nouvelle partie
- **POST** `/guess` → Envoie une proposition
- **GET** `/game/{game_id}` → Récupère le statut d'une partie
- **GET** `/vocab` → Récupère une partie du vocabulaire

#### 🤖 IA (LLM Ollama)
- **POST** `/ai/suggest` → Obtient une suggestion unique du LLM pour le prochain mot
- **POST** `/ai/solve` → Résout automatiquement la partie avec le LLM (streaming en temps réel)

#### 📊 Debug
- **GET** `/health` → Santé du serveur

---

## 🧠 Module IA

### `ai_solver_llm.py` - LLM Ollama 🎯
**C'est le module principal du projet.** Il utilise Ollama (LLM local) pour raisonner sur les indices et proposer le meilleur mot.

**Fonctionnement** :
1. Analyse l'historique des tentatives (mots proposés, scores, rangs)
2. Construit un prompt contextuel pour le LLM
3. Le LLM raisonne comme un humain et propose un mot
4. Validation anti-régression pour éviter les mots moins bons que les précédents
5. Fallback heuristique si le mot proposé n'est pas dans le vocabulaire

**Configuration** :
- `OLLAMA_URL` : URL du serveur (par défaut : `http://localhost:11434`)
- `OLLAMA_MODEL` : Modèle à utiliser (par défaut : `llama3.2`)
- **Aucune clé API nécessaire !**

### `ai_solver.py` - Heuristique (Fallback optionnel)
- Rapide, peu de mémoire
- Basé sur la similarité sémantique avec spaCy
- Utilisé uniquement si `USE_LLM=false`

---

## ⚙️ Configuration

### Variables d'environnement

#### Backend - Configuration LLM

- `USE_LLM` : `true` (par défaut) ou `false` pour désactiver le LLM
  ```powershell
  $env:USE_LLM = "true"   # Windows (par défaut)
  export USE_LLM=true     # Linux/macOS (par défaut)
  ```

- `LLM_MODEL` : Type de LLM à utiliser (par défaut : `ollama`)
  ```powershell
  $env:LLM_MODEL = "ollama"  # Ollama (gratuit, local, pas de clé API) - PAR DÉFAUT ⭐
  ```

**Variables pour Ollama** ⭐ :
- `OLLAMA_URL` : URL du serveur (par défaut : `http://localhost:11434`)
- `OLLAMA_MODEL` : Modèle à utiliser (par défaut : `llama3.2`)
- **Aucune clé API nécessaire !**

#### Frontend
- Configuré dans `src/environments/`
- URL du backend : `http://127.0.0.1:8000` (à adapter si nécessaire)

---

## 🐛 Dépannage

### Erreur : "Can't find model 'fr_core_news_lg'"
```bash
python -m spacy download fr_core_news_lg
```

### Erreur : "SSL module not available"
Réinstallez Python 3.11+ depuis https://www.python.org/downloads/
- ✅ Cochez "Install certificates"
- ✅ Cochez "Add Python to PATH"

### Erreur : "Port 8000 déjà utilisé"
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### Frontend : CORS error
Vérifiez que le backend tourne sur `http://127.0.0.1:8000`

### Ollama - Problèmes courants

**Ollama (défaut)** ⭐ :
- ✅ **Aucune clé API nécessaire !**
- Installez depuis https://ollama.ai
- Téléchargez un modèle : `ollama pull llama3.2`
- Vérifiez que Ollama tourne : `ollama list` (doit afficher les modèles)
- Si erreur de connexion : Vérifiez que Ollama est lancé (il démarre automatiquement après installation)

---

## 📚 Documentation supplémentaire

| Resource | Lien |
|----------|------|
| FastAPI | https://fastapi.tiangolo.com/ |
| Angular | https://angular.dev |
| spaCy | https://spacy.io/ |
| Ollama | https://ollama.ai |
