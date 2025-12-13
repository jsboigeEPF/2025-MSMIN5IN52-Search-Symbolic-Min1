"""
Application Flask pour l'interface web d'optimisation VRP.
Permet de configurer et visualiser les solutions en temps réel.
"""

from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import json
import time
import threading
from typing import List, Tuple, Dict, Optional, Callable
from backend.vrp_classique import VRPClassique
from backend.vrp_vert import VRPVert

app = Flask(__name__)
CORS(app)

# stockage temporaire des solutions en cours
solutions_en_cours = {}


class SolutionCallback:
    """callback pour suivre la progression de la résolution"""
    
    def __init__(self, solution_id: str):
        self.solution_id = solution_id
        self.iterations = []
        self.meilleure_distance = float('inf')
        self.start_time = time.time()
    
    def on_solution_callback(self, distance: float, tournees: List[List[int]]):
        """appelé à chaque nouvelle solution trouvée"""
        elapsed = time.time() - self.start_time
        self.meilleure_distance = min(self.meilleure_distance, distance)
        self.iterations.append({
            'temps': elapsed,
            'distance': distance,
            'tournees': tournees
        })
        
        # mettre à jour le stockage global
        if self.solution_id in solutions_en_cours:
            solutions_en_cours[self.solution_id] = {
                'distance': self.meilleure_distance,
                'tournees': tournees,
                'temps': elapsed,
                'statut': 'en_cours'
            }


@app.route('/')
def index():
    """page principale"""
    return render_template('index.html')


@app.route('/api/solve', methods=['POST'])
def solve_vrp():
    """résout un problème VRP"""
    data = request.json
    
    depot = tuple(data['depot'])
    clients = [tuple(c) for c in data['clients']]
    stations = [tuple(s) for s in data.get('stations', [])]
    nombre_vehicules = data.get('nombre_vehicules', 1)
    limite_temps = data.get('limite_temps', 30)
    type_vrp = data.get('type', 'classique')  # 'classique' ou 'vert'
    
    # capacités par véhicule (nouveau)
    capacites_vehicules = data.get('capacites_vehicules', [50] * nombre_vehicules)
    if len(capacites_vehicules) < nombre_vehicules:
        # compléter avec la dernière valeur ou 50 par défaut
        derniere_capacite = capacites_vehicules[-1] if capacites_vehicules else 50
        capacites_vehicules.extend([derniere_capacite] * (nombre_vehicules - len(capacites_vehicules)))
    capacites_vehicules = capacites_vehicules[:nombre_vehicules]  # limiter au nombre de véhicules
    
    # génération des paramètres par défaut
    demandes = data.get('demandes', [10] * len(clients))
    if len(demandes) < len(clients):
        # compléter avec 10 par défaut
        demandes.extend([10] * (len(clients) - len(demandes)))
    demandes = demandes[:len(clients)]  # limiter au nombre de clients
    
    fenetres_temps = data.get('fenetres_temps', [(0, 10000)] * len(clients))
    temps_service = data.get('temps_service', [0] * len(clients))
    
    solution_id = f"solution_{int(time.time() * 1000)}"
    
    # lancer la résolution dans un thread séparé
    thread = threading.Thread(
        target=_resoudre_vrp_thread,
        args=(
            solution_id, depot, clients, stations, nombre_vehicules,
            capacites_vehicules, limite_temps, type_vrp, demandes,
            fenetres_temps, temps_service
        )
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'solution_id': solution_id})


def _resoudre_vrp_thread(
    solution_id: str,
    depot: Tuple[float, float],
    clients: List[Tuple[float, float]],
    stations: List[Tuple[float, float]],
    nombre_vehicules: int,
    capacites_vehicules: List[int],
    limite_temps: int,
    type_vrp: str,
    demandes: List[int],
    fenetres_temps: List[Tuple[int, int]],
    temps_service: List[int]
):
    """résout le VRP dans un thread séparé"""
    try:
        solutions_en_cours[solution_id] = {
            'statut': 'en_cours',
            'distance': None,
            'tournees': [],
            'temps': 0
        }
        
        if type_vrp == 'vert':
            # paramètres pour VRP vert
            # calculer une autonomie réaliste basée sur les distances
            # estimer la distance moyenne entre points
            import numpy as np
            all_points = [depot] + clients + stations
            distances_estimees = []
            for i, p1 in enumerate(all_points):
                for j, p2 in enumerate(all_points[i+1:], i+1):
                    dist = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
                    distances_estimees.append(dist)
            
            if distances_estimees:
                distance_moyenne = np.mean(distances_estimees)
                # autonomie = environ 2-3 fois la distance moyenne pour forcer des recharges
                autonomie_max = max(20.0, min(50.0, distance_moyenne * 2.5))
            else:
                autonomie_max = 30.0  # valeur par défaut plus réaliste
            
            consommation = 1.0
            temps_recharge = 30
            
            vrp = VRPVert(
                depot=depot,
                clients=clients,
                stations_recharge=stations,
                demandes=demandes,
                capacites_vehicules=capacites_vehicules,
                autonomie_max=autonomie_max,
                consommation=consommation,
                temps_recharge=temps_recharge,
                fenetres_temps=fenetres_temps,
                temps_service=temps_service,
                nombre_vehicules=nombre_vehicules
            )
        else:
            vrp = VRPClassique(
                depot=depot,
                clients=clients,
                demandes=demandes,
                capacites_vehicules=capacites_vehicules,
                fenetres_temps=fenetres_temps,
                temps_service=temps_service,
                nombre_vehicules=nombre_vehicules
            )
        
        # résolution avec simulation de progression
        resultat = _resoudre_avec_progression(vrp, limite_temps, solution_id)
        
        solutions_en_cours[solution_id] = {
            'statut': resultat['statut'],
            'distance': resultat['distance_totale'],
            'tournees': resultat['tournees'],
            'temps': limite_temps,
            'nombre_vehicules': resultat.get('nombre_vehicules_utilises', 0)
        }
        
    except Exception as e:
        solutions_en_cours[solution_id] = {
            'statut': 'erreur',
            'erreur': str(e)
        }


def _resoudre_avec_progression(vrp, limite_temps: int, solution_id: str):
    """résout le VRP avec simulation de progression"""
    import queue
    resultat_queue = queue.Queue()
    
    # démarrer la résolution dans un thread séparé
    def resoudre():
        resultat = vrp.resoudre(limite_temps=limite_temps)
        resultat_queue.put(resultat)
    
    solve_thread = threading.Thread(target=resoudre)
    solve_thread.daemon = True
    solve_thread.start()
    
    # simuler des mises à jour progressives pour le temps réel
    n_updates = min(20, max(5, limite_temps // 2))  # entre 5 et 20 mises à jour
    intervalle = limite_temps / n_updates
    
    # obtenir les informations du problème
    n_clients = len(vrp.clients) if hasattr(vrp, 'clients') else 0
    n_vehicules = vrp.nombre_vehicules
    
    # envoyer des mises à jour progressives
    for i in range(n_updates):
        time.sleep(intervalle)
        
        # vérifier si la résolution est terminée
        try:
            resultat_final = resultat_queue.get_nowait()
            # résolution terminée, utiliser le résultat réel
            solutions_en_cours[solution_id] = {
                'statut': resultat_final['statut'],
                'distance': resultat_final.get('distance_totale', 0),
                'tournees': resultat_final.get('tournees', []),
                'temps': limite_temps,
                'progression': 100,
                'nombre_vehicules': resultat_final.get('nombre_vehicules_utilises', 0)
            }
            return resultat_final
        except queue.Empty:
            pass
        
        # simuler une amélioration progressive
        progression = (i + 1) / n_updates
        
        # estimer une distance qui s'améliore progressivement
        distance_estimee = n_clients * 10 * (2 - progression) if n_clients > 0 else 0
        
        # créer des tournées partielles simulées (construction progressive)
        tournees_simulees = []
        if n_clients > 0:
            # simuler une construction progressive des tournées
            clients_assignes = int(n_clients * progression)
            if clients_assignes > 0:
                # créer des tournées partielles
                clients_par_vehicule = max(1, clients_assignes // n_vehicules)
                
                for k in range(n_vehicules):
                    tournee = [0]  # dépôt
                    start_idx = k * clients_par_vehicule
                    end_idx = min(start_idx + int(clients_par_vehicule * progression), clients_assignes)
                    
                    for j in range(start_idx, end_idx):
                        if j < n_clients:
                            tournee.append(j + 1)  # +1 car dépôt est index 0
                    
                    if len(tournee) > 1:
                        tournees_simulees.append(tournee)
        
        solutions_en_cours[solution_id] = {
            'statut': 'en_cours',
            'distance': distance_estimee,
            'tournees': tournees_simulees,
            'temps': (i + 1) * intervalle,
            'progression': progression * 100
        }
    
    # attendre la fin de la résolution si nécessaire
    solve_thread.join(timeout=2)
    
    # récupérer le résultat final
    try:
        resultat_final = resultat_queue.get(timeout=1)
    except queue.Empty:
        # si pas de résultat, créer un résultat par défaut
        resultat_final = {
            'statut': 'en_cours',
            'distance_totale': 0,
            'tournees': [],
            'nombre_vehicules_utilises': 0
        }
    
    return resultat_final


@app.route('/api/solution/<solution_id>')
def get_solution(solution_id):
    """récupère l'état d'une solution"""
    if solution_id in solutions_en_cours:
        return jsonify(solutions_en_cours[solution_id])
    else:
        return jsonify({'statut': 'non_trouve'}), 404


@app.route('/api/solution/<solution_id>/stream')
def stream_solution(solution_id):
    """stream des mises à jour de solution via Server-Sent Events"""
    def generate():
        while True:
            if solution_id in solutions_en_cours:
                data = solutions_en_cours[solution_id]
                yield f"data: {json.dumps(data)}\n\n"
                
                if data.get('statut') in ['optimal', 'feasible', 'infeasible', 'erreur']:
                    break
            else:
                yield f"data: {json.dumps({'statut': 'attente'})}\n\n"
            
            time.sleep(0.5)  # mise à jour toutes les 0.5 secondes
    
    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

