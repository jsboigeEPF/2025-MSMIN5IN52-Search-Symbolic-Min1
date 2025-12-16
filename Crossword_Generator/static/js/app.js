/**
 * =============================================================================
 * GÉNÉRATEUR DE MOTS-CROISÉS - JavaScript Principal
 * =============================================================================
 */

// ============ ÉTAT DE L'APPLICATION ============
let gridState = [];
let rows = 7;
let cols = 7;

// Variables du jeu
let gameData = null;
let playerGrid = [];
let selectedCell = null;
let selectedWord = null;
let currentDirection = 'H';
let gameTimer = null;
let gameSeconds = 0;
let hintsUsed = 0;
let gameWon = false;
let isPaused = false;
let completedWords = new Set(); // Pour suivre les mots complétés

// Motifs prédéfinis
const patterns = {
    'mini_5x5': {
        name: 'Mini 5×5',
        grid: [
            ".....",
            ".#.#.",
            ".....",
            ".#.#.",
            "....."
        ]
    },
    'standard_7x7': {
        name: 'Standard 7×7',
        grid: [
            ".......",
            ".#...#.",
            "..#.#..",
            ".......",
            "..#.#..",
            ".#...#.",
            "......."
        ]
    },
    'classic_9x9': {
        name: 'Classic 9×9',
        grid: [
            ".........",
            ".#.#.#.#.",
            "..#...#..",
            ".#.....#.",
            "...#.#...",
            ".#.....#.",
            "..#...#..",
            ".#.#.#.#.",
            "........."
        ]
    },
    'medium_11x11': {
        name: 'Medium 11×11',
        grid: [
            "...........",
            ".##...##...",
            "....#......",
            ".#.#.#.#.#.",
            "....#...#..",
            "##.......##",
            "..#...#....",
            ".#.#.#.#.#.",
            "......#....",
            "...##...##.",
            "..........."
        ]
    },
    'simple_6x6': {
        name: 'Simple 6×6',
        grid: [
            "......",
            ".#..#.",
            "......",
            "......",
            ".#..#.",
            "......"
        ]
    }
};

// ============ INITIALISATION ============
document.addEventListener('DOMContentLoaded', function() {
    renderPatternSelector();
    loadPattern('standard_7x7');
    initResizeHandle();
});

// ============ GESTION DU REDIMENSIONNEMENT ============
function initResizeHandle() {
    const handle = document.getElementById('resizeHandle');
    const leftColumn = document.querySelector('.left-column');
    let isResizing = false;
    
    handle.addEventListener('mousedown', function(e) {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    });
    
    document.addEventListener('mousemove', function(e) {
        if (!isResizing) return;
        
        const editorPanel = document.querySelector('.editor-panel');
        const panelRect = editorPanel.getBoundingClientRect();
        let newWidth = e.clientX - panelRect.left - 20;
        
        newWidth = Math.max(280, newWidth);
        leftColumn.style.width = newWidth + 'px';
    });
    
    document.addEventListener('mouseup', function() {
        isResizing = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
    });
}

// ============ SÉLECTEUR DE MOTIFS ============
function renderPatternSelector() {
    const container = document.getElementById('patternSelector');
    container.innerHTML = '';
    
    for (const [key, pattern] of Object.entries(patterns)) {
        const option = document.createElement('div');
        option.className = 'pattern-option';
        option.id = 'pattern-' + key;
        option.onclick = () => loadPattern(key);
        
        const preview = createPatternPreview(pattern.grid);
        option.appendChild(preview);
        
        const name = document.createElement('div');
        name.className = 'pattern-name';
        name.textContent = pattern.name;
        option.appendChild(name);
        
        container.appendChild(option);
    }
}

function createPatternPreview(grid) {
    const preview = document.createElement('div');
    preview.className = 'pattern-preview';
    preview.style.gridTemplateColumns = `repeat(${grid[0].length}, 8px)`;
    
    for (let r = 0; r < grid.length; r++) {
        for (let c = 0; c < grid[0].length; c++) {
            const cell = document.createElement('div');
            cell.className = 'mini-cell ' + (grid[r][c] === '#' ? 'black' : 'white');
            preview.appendChild(cell);
        }
    }
    
    return preview;
}

function loadPattern(patternKey) {
    document.querySelectorAll('.pattern-option').forEach(el => {
        el.classList.remove('selected');
    });
    document.getElementById('pattern-' + patternKey).classList.add('selected');
    
    const pattern = patterns[patternKey].grid;
    rows = pattern.length;
    cols = pattern[0].length;
    
    document.getElementById('rows').value = rows;
    document.getElementById('cols').value = cols;
    
    gridState = [];
    for (let r = 0; r < rows; r++) {
        const row = [];
        for (let c = 0; c < cols; c++) {
            row.push(pattern[r][c] === '#' ? 1 : 0);
        }
        gridState.push(row);
    }
    
    renderGrid();
    updateStats();
    clearSolution();
}

// ============ GESTION DE LA GRILLE ============
function createEmptyGrid() {
    rows = parseInt(document.getElementById('rows').value);
    cols = parseInt(document.getElementById('cols').value);
    
    gridState = [];
    for (let r = 0; r < rows; r++) {
        gridState.push(new Array(cols).fill(0));
    }
    
    document.querySelectorAll('.pattern-option').forEach(el => {
        el.classList.remove('selected');
    });
    
    renderGrid();
    updateStats();
    clearSolution();
}

function clearGrid() {
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            gridState[r][c] = 0;
        }
    }
    renderGrid();
    updateStats();
    clearSolution();
}

function renderGrid() {
    const container = document.getElementById('gridEditor');
    container.innerHTML = '';
    container.style.gridTemplateColumns = `repeat(${cols}, 38px)`;
    
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            const cell = document.createElement('div');
            cell.className = 'cell ' + (gridState[r][c] === 1 ? 'black' : 'white');
            cell.onclick = () => toggleCell(r, c);
            container.appendChild(cell);
        }
    }
}

function toggleCell(r, c) {
    gridState[r][c] = gridState[r][c] === 0 ? 1 : 0;
    renderGrid();
    updateStats();
    clearSolution();
}

// ============ STATISTIQUES ============
function updateStats() {
    let whiteCells = 0;
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (gridState[r][c] === 0) whiteCells++;
        }
    }
    
    const analysis = analyzeGrid();
    
    document.getElementById('statCells').textContent = whiteCells;
    document.getElementById('statSlots').textContent = analysis.slots;
    document.getElementById('statIntersections').textContent = analysis.intersections;
}

function analyzeGrid() {
    let slots = 0;
    let intersections = 0;
    const cellSlots = {};
    const slotCells = []; // Pour stocker les cellules de chaque slot valide
    
    // Slots horizontaux
    for (let r = 0; r < rows; r++) {
        let c = 0;
        while (c < cols) {
            if (gridState[r][c] === 0) {
                let startCol = c;
                let len = 0;
                const cells = [];
                while (c < cols && gridState[r][c] === 0) {
                    cells.push([r, c]);
                    len++;
                    c++;
                }
                if (len >= 2) {
                    slots++;
                    slotCells.push(cells);
                }
            } else {
                c++;
            }
        }
    }
    
    // Slots verticaux
    for (let c = 0; c < cols; c++) {
        let r = 0;
        while (r < rows) {
            if (gridState[r][c] === 0) {
                let startRow = r;
                let len = 0;
                const cells = [];
                while (r < rows && gridState[r][c] === 0) {
                    cells.push([r, c]);
                    len++;
                    r++;
                }
                if (len >= 2) {
                    slots++;
                    slotCells.push(cells);
                }
            } else {
                r++;
            }
        }
    }
    
    // Compter les intersections : chaque cellule partagée par 2 slots
    for (const cells of slotCells) {
        for (const [r, c] of cells) {
            const key = r + ',' + c;
            if (!cellSlots[key]) cellSlots[key] = 0;
            cellSlots[key]++;
        }
    }
    
    for (const key in cellSlots) {
        if (cellSlots[key] === 2) intersections++;
    }
    
    return { slots, intersections };
}

// ============ RÉSOLUTION ============
function clearSolution() {
    gameData = null;
    document.getElementById('resultActions').style.display = 'none';
}

async function solveGrid() {
    const btn = document.getElementById('solveBtn');
    const statusDiv = document.getElementById('statusMessage');
    const resultActions = document.getElementById('resultActions');
    
    resultActions.style.display = 'none';
    
    const pattern = [];
    for (let r = 0; r < rows; r++) {
        let row = '';
        for (let c = 0; c < cols; c++) {
            row += gridState[r][c] === 1 ? '#' : '.';
        }
        pattern.push(row);
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Génération...';
    statusDiv.className = 'status loading';
    statusDiv.textContent = '🔄 Génération de la grille en cours...';
    
    try {
        const response = await fetch('/solve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ pattern })
        });
        
        const result = await response.json();
        
        if (result.success) {
            initPlayMode(result);
            
            statusDiv.className = 'status success';
            statusDiv.innerHTML = `✅ Grille générée en ${result.time.toFixed(2)}s ! <strong>${result.words.horizontal.length + result.words.vertical.length} mots</strong> trouvés.`;
            
            resultActions.style.display = 'flex';
        } else {
            statusDiv.className = 'status error';
            statusDiv.innerHTML = `❌ ${result.message}`;
            resultActions.style.display = 'none';
        }
    } catch (error) {
        statusDiv.className = 'status error';
        statusDiv.textContent = '❌ Erreur de connexion au serveur';
        resultActions.style.display = 'none';
        console.error(error);
    }
    
    btn.disabled = false;
    btn.innerHTML = '🔍 Générer la Grille';
}

// ============ MODE JEU ============
function initPlayMode(result) {
    gameData = result;
    gameWon = false;
    hintsUsed = 0;
    gameSeconds = 0;
    
    playerGrid = [];
    for (let r = 0; r < result.rows; r++) {
        const row = [];
        for (let c = 0; c < result.cols; c++) {
            row.push(result.grid[r][c] === '#' ? '#' : '');
        }
        playerGrid.push(row);
    }
    
    buildWordMap();
}

function buildWordMap() {
    if (!gameData) return;
    
    gameData.wordMap = {};
    
    for (const word of gameData.words.horizontal) {
        const cells = [];
        for (let i = 0; i < word.word.length; i++) {
            cells.push({ r: word.row - 1, c: word.col - 1 + i });
        }
        gameData.wordMap[`H${word.number}`] = {
            ...word,
            direction: 'H',
            cells: cells
        };
    }
    
    for (const word of gameData.words.vertical) {
        const cells = [];
        for (let i = 0; i < word.word.length; i++) {
            cells.push({ r: word.row - 1 + i, c: word.col - 1 });
        }
        gameData.wordMap[`V${word.number}`] = {
            ...word,
            direction: 'V',
            cells: cells
        };
    }
}

// ============ MODE PLEIN ÉCRAN - JEU ============
function openFullscreenGame() {
    if (!gameData) return;
    
    document.getElementById('fullscreenGame').classList.add('active');
    document.body.style.overflow = 'hidden';
    
    if (gameWon) {
        resetGameFS();
    }
    
    completedWords.clear(); // Réinitialiser les mots complétés au démarrage
    renderFSGrid();
    renderFSDefinitions();
    updateFSStats();
}

function closeFullscreenGame() {
    document.getElementById('fullscreenGame').classList.remove('active');
    document.body.style.overflow = 'auto';
}

function renderFSGrid() {
    if (!gameData) return;
    
    const container = document.getElementById('fsGrid');
    container.innerHTML = '';
    container.style.gridTemplateColumns = `repeat(${gameData.cols}, 38px)`;
    
    const cellNumbers = gameData.cellNumbers || {};
    
    for (let r = 0; r < gameData.rows; r++) {
        for (let c = 0; c < gameData.cols; c++) {
            const cell = document.createElement('div');
            const cellKey = `${r},${c}`;
            const isBlack = gameData.grid[r][c] === '#';
            
            cell.className = 'play-cell ' + (isBlack ? 'black' : 'white');
            cell.dataset.row = r;
            cell.dataset.col = c;
            
            if (!isBlack) {
                if (cellNumbers[cellKey]) {
                    const numSpan = document.createElement('span');
                    numSpan.className = 'cell-number';
                    numSpan.textContent = cellNumbers[cellKey];
                    cell.appendChild(numSpan);
                }
                
                const input = document.createElement('input');
                input.type = 'text';
                input.maxLength = 1;
                input.value = playerGrid[r][c];
                input.dataset.row = r;
                input.dataset.col = c;
                
                input.addEventListener('focus', () => selectCellFS(r, c));
                input.addEventListener('input', (e) => handleInputFS(e, r, c));
                input.addEventListener('keydown', (e) => handleKeydownFS(e, r, c));
                
                cell.appendChild(input);
            }
            
            container.appendChild(cell);
        }
    }
}

function selectCellFS(row, col) {
    if (isPaused) return;
    
    if (selectedCell && selectedCell.row === row && selectedCell.col === col) {
        toggleDirectionFS();
        highlightWordFS(row, col);
        return;
    }
    
    selectedCell = { row, col };
    highlightWordFS(row, col);
}

function toggleDirectionFS() {
    currentDirection = currentDirection === 'H' ? 'V' : 'H';
    updateDirectionIndicator();
}

function updateDirectionIndicator() {
    const indicator = document.getElementById('fsDirectionIndicator');
    if (currentDirection === 'H') {
        indicator.innerHTML = '<span class="arrow">→</span><span>Horizontal</span>';
    } else {
        indicator.innerHTML = '<span class="arrow">↓</span><span>Vertical</span>';
    }
}

function highlightWordFS(row, col) {
    document.querySelectorAll('#fsGrid .play-cell').forEach(cell => {
        cell.classList.remove('selected', 'highlighted');
    });
    document.querySelectorAll('.def-item').forEach(item => {
        item.classList.remove('active');
    });
    
    let foundWord = null;
    const dir = currentDirection;
    
    for (const [key, wordData] of Object.entries(gameData.wordMap)) {
        if (key.startsWith(dir)) {
            for (const cell of wordData.cells) {
                if (cell.r === row && cell.c === col) {
                    foundWord = { key, ...wordData };
                    break;
                }
            }
        }
        if (foundWord) break;
    }
    
    if (!foundWord) {
        const otherDir = dir === 'H' ? 'V' : 'H';
        for (const [key, wordData] of Object.entries(gameData.wordMap)) {
            if (key.startsWith(otherDir)) {
                for (const cell of wordData.cells) {
                    if (cell.r === row && cell.c === col) {
                        foundWord = { key, ...wordData };
                        currentDirection = otherDir;
                        updateDirectionIndicator();
                        break;
                    }
                }
            }
            if (foundWord) break;
        }
    }
    
    if (foundWord) {
        selectedWord = foundWord.key;
        
        for (const cell of foundWord.cells) {
            const cellEl = document.querySelector(`#fsGrid .play-cell[data-row="${cell.r}"][data-col="${cell.c}"]`);
            if (cellEl) {
                if (cell.r === row && cell.c === col) {
                    cellEl.classList.add('selected');
                } else {
                    cellEl.classList.add('highlighted');
                }
            }
        }
        
        const defItem = document.getElementById(`fs-def-${foundWord.key}`);
        if (defItem) {
            defItem.classList.add('active');
            defItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
        updateCurrentDefinition(foundWord);
    }
}

function updateCurrentDefinition(wordData) {
    const number = wordData.key.substring(1);
    const dir = wordData.key[0] === 'H' ? 'Horizontal' : 'Vertical';
    const def = gameData.definitions[wordData.word] || 'Définition non disponible';
    
    document.getElementById('fsDefNumber').textContent = number;
    document.getElementById('fsDefDir').textContent = dir;
    document.getElementById('fsDefText').textContent = def;
}

function handleInputFS(e, row, col) {
    // Ne pas modifier si la cellule est révélée par un indice
    if (e.target.parentElement.classList.contains('revealed')) {
        e.target.value = playerGrid[row][col] || '';
        return;
    }
    
    // Ne pas modifier si la cellule fait partie d'un mot complété
    if (e.target.parentElement.classList.contains('completed')) {
        e.target.value = playerGrid[row][col] || '';
        return;
    }
    
    const value = e.target.value.toUpperCase();
    if (value.length > 0) {
        playerGrid[row][col] = value[value.length - 1];
        e.target.value = playerGrid[row][col];
        moveToNextCellFS(row, col);
    } else {
        playerGrid[row][col] = '';
    }
    checkAndHighlightCompletedWords();
    updateFSStats();
    checkVictoryFS();
}

function handleKeydownFS(e, row, col) {
    if (isPaused) {
        e.preventDefault();
        return;
    }
    
    switch(e.key) {
        case 'ArrowRight':
            e.preventDefault();
            if (currentDirection !== 'H') {
                currentDirection = 'H';
                updateDirectionIndicator();
                highlightWordFS(row, col);
            } else {
                moveFocusFS(row, col + 1);
            }
            break;
        case 'ArrowLeft':
            e.preventDefault();
            if (currentDirection !== 'H') {
                currentDirection = 'H';
                updateDirectionIndicator();
                highlightWordFS(row, col);
            } else {
                moveFocusFS(row, col - 1);
            }
            break;
        case 'ArrowDown':
            e.preventDefault();
            if (currentDirection !== 'V') {
                currentDirection = 'V';
                updateDirectionIndicator();
                highlightWordFS(row, col);
            } else {
                moveFocusFS(row + 1, col);
            }
            break;
        case 'ArrowUp':
            e.preventDefault();
            if (currentDirection !== 'V') {
                currentDirection = 'V';
                updateDirectionIndicator();
                highlightWordFS(row, col);
            } else {
                moveFocusFS(row - 1, col);
            }
            break;
        case 'Backspace':
            e.preventDefault();
            // Ne pas supprimer si la cellule courante est révélée ou complétée
            if (e.target.parentElement.classList.contains('revealed') || 
                e.target.parentElement.classList.contains('completed')) {
                // Passer à la cellule précédente supprimable
                const prevCell = getPrevCellFS(row, col);
                if (prevCell) {
                    moveFocusFS(prevCell.row, prevCell.col);
                }
                break;
            }
            if (playerGrid[row][col]) {
                playerGrid[row][col] = '';
                e.target.value = '';
                checkAndHighlightCompletedWords();
                updateFSStats();
            } else {
                const prevCell = getPrevCellFS(row, col);
                if (prevCell) {
                    playerGrid[prevCell.row][prevCell.col] = '';
                    const prevInput = document.querySelector(`#fsGrid .play-cell[data-row="${prevCell.row}"][data-col="${prevCell.col}"] input`);
                    if (prevInput) {
                        prevInput.value = '';
                        prevInput.focus();
                    }
                    checkAndHighlightCompletedWords();
                    updateFSStats();
                }
            }
            break;
        case 'Tab':
            e.preventDefault();
            moveToNextWordFS();
            break;
        case 'Escape':
            closeFullscreenGame();
            break;
    }
}

function getPrevCellFS(row, col) {
    let prevRow = row;
    let prevCol = col;
    
    while (true) {
        if (currentDirection === 'H') {
            prevCol--;
        } else {
            prevRow--;
        }
        
        if (prevRow < 0 || prevCol < 0) return null;
        if (gameData.grid[prevRow][prevCol] === '#') return null;
        
        // Vérifier si la cellule est supprimable
        const prevInput = document.querySelector(`#fsGrid .play-cell[data-row="${prevRow}"][data-col="${prevCol}"] input`);
        if (prevInput) {
            const isLocked = prevInput.parentElement.classList.contains('revealed') || 
                           prevInput.parentElement.classList.contains('completed');
            if (!isLocked) {
                return { row: prevRow, col: prevCol };
            }
            // Si la cellule est verrouillée, continuer à chercher
        } else {
            return { row: prevRow, col: prevCol };
        }
    }
}

function moveToNextCellFS(row, col) {
    let nextRow = row;
    let nextCol = col;
    
    while (true) {
        if (currentDirection === 'H') {
            nextCol++;
        } else {
            nextRow++;
        }
        
        if (nextRow >= gameData.rows || nextCol >= gameData.cols) break;
        if (gameData.grid[nextRow][nextCol] === '#') break;
        
        if (!playerGrid[nextRow][nextCol]) {
            moveFocusFS(nextRow, nextCol);
            return;
        }
    }
    
    if (currentDirection === 'H') {
        moveFocusFS(row, col + 1);
    } else {
        moveFocusFS(row + 1, col);
    }
}

function moveFocusFS(row, col) {
    if (row < 0 || row >= gameData.rows || col < 0 || col >= gameData.cols) return;
    if (gameData.grid[row][col] === '#') return;
    
    const input = document.querySelector(`#fsGrid .play-cell[data-row="${row}"][data-col="${col}"] input`);
    if (input) {
        input.focus();
    }
}

function moveToNextWordFS() {
    if (!selectedWord || !gameData.wordMap) return;
    
    const keys = Object.keys(gameData.wordMap);
    const currentIndex = keys.indexOf(selectedWord);
    const nextIndex = (currentIndex + 1) % keys.length;
    const nextWord = gameData.wordMap[keys[nextIndex]];
    
    if (nextWord && nextWord.cells.length > 0) {
        selectedWord = keys[nextIndex];
        currentDirection = keys[nextIndex][0];
        updateDirectionIndicator();
        const firstCell = nextWord.cells[0];
        moveFocusFS(firstCell.r, firstCell.c);
    }
}

function renderFSDefinitions() {
    if (!gameData) return;
    
    const hDiv = document.getElementById('fsHorizontalWords');
    const vDiv = document.getElementById('fsVerticalWords');
    
    hDiv.innerHTML = '';
    vDiv.innerHTML = '';
    
    const definitions = gameData.definitions || {};
    
    for (const word of gameData.words.horizontal) {
        const item = createFSDefItem(word, 'H', definitions);
        hDiv.appendChild(item);
    }
    
    for (const word of gameData.words.vertical) {
        const item = createFSDefItem(word, 'V', definitions);
        vDiv.appendChild(item);
    }
}

function createFSDefItem(word, direction, definitions) {
    const item = document.createElement('div');
    item.className = 'def-item';
    item.id = `fs-def-${direction}${word.number}`;
    
    const def = definitions[word.word] || '<em>Pas de définition</em>';
    const preview = '_'.repeat(word.word.length);
    
    item.innerHTML = `
        <div><span class="def-num">${word.number}</span>${def}</div>
        <div class="word-preview">${preview}</div>
    `;
    
    item.onclick = () => {
        const wordData = gameData.wordMap[`${direction}${word.number}`];
        if (wordData && wordData.cells.length > 0) {
            currentDirection = direction;
            updateDirectionIndicator();
            selectedWord = `${direction}${word.number}`;
            const firstCell = wordData.cells[0];
            moveFocusFS(firstCell.r, firstCell.c);
        }
    };
    
    return item;
}

function checkAndHighlightCompletedWords() {
    if (!gameData) return;
    
    // Réinitialiser les classes correct/incorrect (mais pas completed pour les mots déjà validés)
    document.querySelectorAll('#fsGrid .play-cell.white').forEach(cell => {
        cell.classList.remove('correct', 'incorrect');
    });
    
    // Vérifier tous les mots
    const allWords = [...(gameData.words?.horizontal || []), ...(gameData.words?.vertical || [])];
    
    allWords.forEach(wordInfo => {
        const wordKey = `${wordInfo.number}-${wordInfo.row}-${wordInfo.col}`;
        const cells = getWordCells(wordInfo);
        
        if (!cells || cells.length === 0) return;
        
        // Vérifier si le mot est complètement rempli
        let isComplete = true;
        let isCorrect = true;
        
        for (const {row, col, correctLetter} of cells) {
            const playerLetter = playerGrid[row][col];
            if (!playerLetter) {
                isComplete = false;
                break;
            }
            if (playerLetter.toUpperCase() !== correctLetter.toUpperCase()) {
                isCorrect = false;
            }
        }
        
        // Si le mot est complet et correct, le marquer en vert
        if (isComplete && isCorrect) {
            // Ajouter aux mots complétés si ce n'est pas déjà fait
            if (!completedWords.has(wordKey)) {
                completedWords.add(wordKey);
            }
            
            // Mettre toutes les cellules du mot en vert et les protéger
            cells.forEach(({row, col}) => {
                const cell = document.querySelector(`#fsGrid .play-cell[data-row="${row}"][data-col="${col}"]`);
                if (cell) {
                    cell.classList.add('correct');
                    cell.classList.add('completed'); // Marquer comme complété
                }
            });
        } else if (isComplete && !isCorrect) {
            // Retirer des mots complétés si le mot était complété mais a été modifié
            completedWords.delete(wordKey);
        } else {
            // Mot incomplet, retirer des mots complétés
            completedWords.delete(wordKey);
        }
    });
}

function getWordCells(wordInfo) {
    if (!gameData || !wordInfo) return [];
    
    const cells = [];
    const word = wordInfo.word;
    const startRow = wordInfo.row - 1; // Les coordonnées sont 1-indexées
    const startCol = wordInfo.col - 1;
    
    // Déterminer la direction (H ou V)
    const horizontalWords = gameData.words?.horizontal || [];
    const isHorizontal = horizontalWords.some(w => 
        w.number === wordInfo.number && w.row === wordInfo.row && w.col === wordInfo.col
    );
    
    for (let i = 0; i < word.length; i++) {
        const row = isHorizontal ? startRow : startRow + i;
        const col = isHorizontal ? startCol + i : startCol;
        cells.push({
            row,
            col,
            correctLetter: word[i]
        });
    }
    
    return cells;
}

function updateFSStats() {
    // Calculer le score basé uniquement sur les mots complétés
    const score = Math.max(0, (completedWords.size * 10) - (hintsUsed * 5));
    document.getElementById('fsScore').textContent = score;
    document.getElementById('fsHints').textContent = hintsUsed;
}

function revealLetterFS() {
    if (!selectedCell || !gameData) return;
    
    const { row, col } = selectedCell;
    const correct = gameData.grid[row][col];
    
    if (correct === '#') return;
    
    playerGrid[row][col] = correct;
    
    const input = document.querySelector(`#fsGrid .play-cell[data-row="${row}"][data-col="${col}"] input`);
    if (input) {
        input.value = correct;
        input.parentElement.classList.add('revealed');
    }
    
    hintsUsed++;
    checkAndHighlightCompletedWords();
    updateFSStats();
    checkVictoryFS();
}

function revealWordFS() {
    if (!selectedWord || !gameData.wordMap[selectedWord]) return;
    
    const word = gameData.wordMap[selectedWord];
    
    for (const cell of word.cells) {
        const correct = gameData.grid[cell.r][cell.c];
        playerGrid[cell.r][cell.c] = correct;
        
        const input = document.querySelector(`#fsGrid .play-cell[data-row="${cell.r}"][data-col="${cell.c}"] input`);
        if (input) {
            input.value = correct;
            input.parentElement.classList.add('revealed');
        }
    }
    
    hintsUsed += word.cells.length;
    checkAndHighlightCompletedWords();
    updateFSStats();
    checkVictoryFS();
}

function resetGameFS() {
    if (!gameData) return;
    
    gameWon = false;
    hintsUsed = 0;
    gameSeconds = 0;
    isPaused = false;
    currentDirection = 'H';
    completedWords.clear(); // Réinitialiser les mots complétés
    
    for (let r = 0; r < gameData.rows; r++) {
        for (let c = 0; c < gameData.cols; c++) {
            if (gameData.grid[r][c] !== '#') {
                playerGrid[r][c] = '';
            }
        }
    }
    
    selectedCell = null;
    selectedWord = null;
    
    renderFSGrid();
    renderFSDefinitions();
    updateFSStats();
    updateDirectionIndicator();
    
    document.getElementById('victoryOverlay').classList.remove('active');
}

function checkVictoryFS() {
    if (gameWon) return;
    
    let allCorrect = true;
    for (let r = 0; r < gameData.rows; r++) {
        for (let c = 0; c < gameData.cols; c++) {
            if (gameData.grid[r][c] !== '#') {
                if (playerGrid[r][c].toUpperCase() !== gameData.grid[r][c].toUpperCase()) {
                    allCorrect = false;
                    break;
                }
            }
        }
        if (!allCorrect) break;
    }
    
    if (allCorrect) {
        victoryFS();
    }
}

function victoryFS() {
    gameWon = true;
    
    const finalScore = parseInt(document.getElementById('fsScore').textContent);
    
    document.getElementById('victoryScore').textContent = finalScore;
    document.getElementById('victoryHints').textContent = hintsUsed;
    
    document.getElementById('victoryOverlay').classList.add('active');
}

function closeVictory() {
    document.getElementById('victoryOverlay').classList.remove('active');
}

// ============ PAGE SOLUTION ============
function openSolutionPage() {
    if (!gameData) return;
    
    document.getElementById('fullscreenSolution').classList.add('active');
    document.body.style.overflow = 'hidden';
    
    renderSolutionGrid();
    renderSolutionDefinitions();
}

function closeSolutionPage() {
    document.getElementById('fullscreenSolution').classList.remove('active');
    document.body.style.overflow = 'auto';
}

function closeSolutionOpenGame() {
    closeSolutionPage();
    setTimeout(() => openFullscreenGame(), 100);
}

function renderSolutionGrid() {
    if (!gameData) return;
    
    const container = document.getElementById('solGrid');
    container.innerHTML = '';
    container.style.gridTemplateColumns = `repeat(${gameData.cols}, 38px)`;
    
    const cellNumbers = gameData.cellNumbers || {};
    
    for (let r = 0; r < gameData.rows; r++) {
        for (let c = 0; c < gameData.cols; c++) {
            const cell = document.createElement('div');
            const isBlack = gameData.grid[r][c] === '#';
            const cellKey = `${r},${c}`;
            
            cell.className = 'cell ' + (isBlack ? 'black' : 'white solved');
            
            if (!isBlack) {
                if (cellNumbers[cellKey]) {
                    const numSpan = document.createElement('span');
                    numSpan.className = 'cell-number';
                    numSpan.textContent = cellNumbers[cellKey];
                    cell.appendChild(numSpan);
                }
                
                const letterSpan = document.createElement('span');
                letterSpan.textContent = gameData.grid[r][c];
                cell.appendChild(letterSpan);
            }
            
            container.appendChild(cell);
        }
    }
}

function renderSolutionDefinitions() {
    if (!gameData) return;
    
    const hDiv = document.getElementById('solHorizontalWords');
    const vDiv = document.getElementById('solVerticalWords');
    
    hDiv.innerHTML = '';
    vDiv.innerHTML = '';
    
    const definitions = gameData.definitions || {};
    
    for (const word of gameData.words.horizontal) {
        const item = createSolutionWordItem(word, definitions);
        hDiv.appendChild(item);
    }
    
    for (const word of gameData.words.vertical) {
        const item = createSolutionWordItem(word, definitions);
        vDiv.appendChild(item);
    }
}

function createSolutionWordItem(word, definitions) {
    const item = document.createElement('div');
    item.className = 'solution-word-item';
    
    const def = definitions[word.word] || '<em>Définition non disponible</em>';
    
    item.innerHTML = `
        <div class="word-header">
            <span class="word-num">${word.number}</span>
            <span class="word-text">${word.word}</span>
        </div>
        <div class="word-def">${def}</div>
    `;
    
    return item;
}
