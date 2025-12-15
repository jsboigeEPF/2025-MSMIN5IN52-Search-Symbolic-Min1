"""
Interface Web pour le Générateur de Mots-Croisés
=================================================
Serveur Flask avec interface interactive pour créer et résoudre des grilles.

Utilisation:
    python web_interface.py

Auteur: Projet IA 2 - EPF 5A
Date: Décembre 2025
"""

from flask import Flask, render_template, request, jsonify
import time
import threading
import webbrowser

# Import depuis le package solver
from solver import CrosswordGrid, CrosswordSolver, WordDictionary, DefinitionService


# =============================================================================
# APPLICATION FLASK
# =============================================================================

app = Flask(__name__)

# Charge le dictionnaire une fois au démarrage
# Utilise load_smart() pour télécharger automatiquement un dictionnaire français complet
dictionary = WordDictionary()
dictionary.load_smart()  # Télécharge ~140k mots français ou utilise le cache/fallback

# Service de définitions (avec cache)
definition_service = DefinitionService(cache_definitions=True)


@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html')


@app.route('/solve', methods=['POST'])
def solve():
    """Endpoint pour résoudre une grille"""
    try:
        data = request.get_json()
        pattern = data.get('pattern', [])
        require_definitions = data.get('require_definitions', True)  # Par défaut, exiger des définitions
        
        if not pattern:
            return jsonify({'success': False, 'message': 'Grille vide'})
        
        start_time = time.time()
        max_total_time = 60.0  # Limite totale de 60 secondes
        
        # Crée et résout la grille
        rows = len(pattern)
        cols = len(pattern[0]) if pattern else 0
        grid = CrosswordGrid(rows, cols)
        grid.load_pattern(pattern)
        
        slots = grid.extract_slots(min_length=2)
        intersections = grid.find_intersections()
        
        if not slots:
            return jsonify({'success': False, 'message': 'Aucun emplacement de mot trouvé (min 2 lettres)'})
        
        # Vérifie que tous les slots ont des mots possibles
        for slot in slots:
            if not dictionary.get_words(slot.length):
                return jsonify({
                    'success': False, 
                    'message': f'Aucun mot de {slot.length} lettres dans le dictionnaire'
                })
        
        # Créer le solveur avec le service de définitions
        solver = CrosswordSolver(
            grid, 
            dictionary,
            definition_service=definition_service,
            require_definitions=False  # On vérifie les définitions après résolution
        )
        
        if not solver.build_model():
            return jsonify({'success': False, 'message': 'Impossible de construire le modèle'})
        
        # Temps de résolution adapté à la taille
        solve_time = min(30.0, max_total_time - (time.time() - start_time))
        success = solver.solve(time_limit=solve_time)
        elapsed = time.time() - start_time
        
        if success and require_definitions:
            # Vérifier les définitions et retry si nécessaire
            # Limiter les retries pour éviter les boucles infinies
            max_retries = 2 if len(slots) <= 12 else 1  # Moins de retries pour grandes grilles
            all_excluded_words = set()
            
            for retry_count in range(max_retries):
                # Vérifier le temps restant
                if time.time() - start_time > max_total_time - 10:
                    print(f"⏱️ Temps limite approché, arrêt des retries")
                    break
                
                # Trouver les mots sans définition
                words_without_def = []
                for slot in grid.slots:
                    if slot.id in grid.solution:
                        word = grid.solution[slot.id]
                        if word not in all_excluded_words:
                            defn = definition_service.get_definition(word, max_length=150)
                            if not defn:
                                words_without_def.append(word)
                
                # Si tous les mots ont une définition, on arrête
                if not words_without_def:
                    break
                
                print(f"⚠️ Retry {retry_count + 1}: {len(words_without_def)} mots sans définition: {words_without_def[:5]}...")
                
                # Cumuler les mots exclus
                all_excluded_words.update(words_without_def)
                
                # Recréer le solveur
                grid.solution.clear()
                solver = CrosswordSolver(
                    grid, 
                    dictionary,
                    definition_service=definition_service,
                    require_definitions=False
                )
                solver.exclude_words(all_excluded_words)
                
                if not solver.build_model():
                    print(f"❌ Impossible de construire le modèle après exclusion")
                    success = False
                    break
                
                # Temps restant pour ce retry
                remaining_time = max(5.0, max_total_time - (time.time() - start_time) - 5)
                success = solver.solve(time_limit=min(15.0, remaining_time))
                elapsed = time.time() - start_time
                
                if not success:
                    print(f"❌ Pas de solution trouvée au retry {retry_count + 1}")
                    break
        
        if success:
            # Construit la grille de résultat
            result_grid = []
            letter_grid = [[' ' for _ in range(grid.cols)] for _ in range(grid.rows)]
            
            for slot in grid.slots:
                if slot.id in grid.solution:
                    word = grid.solution[slot.id]
                    for i, (row, col) in enumerate(slot.cells):
                        if i < len(word):
                            letter_grid[row][col] = word[i]
            
            for row in range(grid.rows):
                result_row = []
                for col in range(grid.cols):
                    if grid.is_black(row, col):
                        result_row.append('#')
                    else:
                        result_row.append(letter_grid[row][col])
                result_grid.append(result_row)
            
            # Collecte les mots avec numérotation comme dans les vrais mots-croisés
            words = {'horizontal': [], 'vertical': []}
            all_words_set = set()  # Pour éviter de récupérer des définitions en double
            
            # D'abord, identifier toutes les cases de départ et leur assigner un numéro
            # Les numéros sont assignés en parcourant de gauche à droite, de haut en bas
            start_cells = {}  # (row, col) -> numéro
            cell_numbers = {}  # "row,col" -> numéro (pour le frontend)
            current_number = 1
            
            # Trier les slots par position de départ
            sorted_slots = sorted(grid.slots, key=lambda s: (s.start_row, s.start_col))
            
            for slot in sorted_slots:
                if slot.id in grid.solution:
                    pos = (slot.start_row, slot.start_col)
                    if pos not in start_cells:
                        start_cells[pos] = current_number
                        cell_numbers[f"{slot.start_row},{slot.start_col}"] = current_number
                        current_number += 1
            
            # Maintenant collecter les mots avec leurs numéros
            for slot in sorted_slots:
                if slot.id in grid.solution:
                    word = grid.solution[slot.id]
                    all_words_set.add(word)
                    pos = (slot.start_row, slot.start_col)
                    word_info = {
                        'word': word,
                        'row': slot.start_row + 1,
                        'col': slot.start_col + 1,
                        'number': start_cells[pos]
                    }
                    if slot.direction == 'H':
                        words['horizontal'].append(word_info)
                    else:
                        words['vertical'].append(word_info)
            
            # Récupère les définitions pour tous les mots uniques
            definitions = {}
            for word in all_words_set:
                defn = definition_service.get_definition(word, max_length=150)
                if defn:
                    definitions[word] = defn
            
            return jsonify({
                'success': True,
                'grid': result_grid,
                'rows': grid.rows,
                'cols': grid.cols,
                'words': words,
                'definitions': definitions,
                'cellNumbers': cell_numbers,
                'time': elapsed
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Aucune solution trouvée (temps: {elapsed:.2f}s). Essayez une autre configuration.'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})


def run_server(host: str = '127.0.0.1', port: int = 5000, open_browser: bool = True):
    """
    Lance le serveur web.
    
    Args:
        host: Adresse d'écoute
        port: Port d'écoute
        open_browser: Ouvrir automatiquement le navigateur
    """
    print("\n" + "=" * 60)
    print("   GÉNÉRATEUR DE MOTS-CROISÉS - Interface Web")
    print("=" * 60)
    print(f"\n🌐 Serveur démarré sur http://{host}:{port}")
    print("📝 Ouvrez cette adresse dans votre navigateur")
    print("⏹  Appuyez sur Ctrl+C pour arrêter le serveur\n")
    
    if open_browser:
        def open_browser_delayed():
            time.sleep(1)
            webbrowser.open(f'http://{host}:{port}')
        
        threading.Thread(target=open_browser_delayed, daemon=True).start()
    
    app.run(host=host, port=port, debug=False)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    run_server()
