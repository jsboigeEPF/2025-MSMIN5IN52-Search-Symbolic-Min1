@echo off
REM Script de démarrage du Wordle Solver pour Windows
REM Lance le backend et le frontend

echo 🚀 Démarrage du Wordle Solver...
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé. Veuillez l'installer d'abord.
    pause
    exit /b 1
)

REM Vérifier si Node.js est installé
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js n'est pas installé. Veuillez l'installer d'abord.
    pause
    exit /b 1
)

REM Vérifier si npm est installé
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm n'est pas installé. Veuillez l'installer d'abord.
    pause
    exit /b 1
)

REM Installer les dépendances Python si nécessaire
if not exist "backend\venv" (
    echo 📦 Installation des dépendances Python...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    pip install -q -r requirements.txt
    pip install -q -r ..\requirements.txt
    cd ..
    echo ✅ Dépendances Python installées
)

REM Installer les dépendances Node.js si nécessaire
if not exist "frontend\node_modules" (
    echo 📦 Installation des dépendances Node.js...
    cd frontend
    npm install --silent
    cd ..
    echo ✅ Dépendances Node.js installées
)

REM Démarrer le backend dans une nouvelle fenêtre
echo.
echo 🔧 Démarrage du backend API (port 8000)...
start "Wordle Solver - Backend" cmd /c "cd backend && call venv\Scripts\activate && python main.py"

REM Attendre que le backend soit prêt
echo ⏳ Attente du démarrage du backend...
timeout /t 3 /nobreak >nul

REM Démarrer le frontend dans une nouvelle fenêtre
echo.
echo 🎨 Démarrage du frontend React (port 3000)...
start "Wordle Solver - Frontend" cmd /c "cd frontend && npm run dev"

REM Attendre que le frontend soit prêt
timeout /t 3 /nobreak >nul

echo.
echo ✅ Wordle Solver est prêt !
echo.
echo 🌐 Frontend : http://localhost:3000
echo 🔌 Backend API : http://localhost:8000
echo 📚 Documentation API : http://localhost:8000/docs
echo.
echo Les serveurs tournent dans des fenêtres séparées.
echo Fermez les fenêtres pour arrêter les serveurs.
echo.
pause
