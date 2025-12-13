"""
Module pour résoudre le problème de tournées de véhicules (VRP) classique
avec contraintes de capacité et fenêtres temporelles.
Utilise OR-Tools CP-SAT pour la résolution.
"""

from ortools.sat.python import cp_model
import numpy as np
from typing import List, Tuple, Dict, Optional
import math


class VRPClassique:
    """
    Classe pour résoudre le VRP classique avec :
    - Contraintes de capacité
    - Fenêtres temporelles
    - Minimisation de la distance totale
    """
    
    def __init__(
        self,
        depot: Tuple[float, float],
        clients: List[Tuple[float, float]],
        demandes: List[int],
        capacite_vehicule: int = None,
        capacites_vehicules: Optional[List[int]] = None,
        fenetres_temps: Optional[List[Tuple[int, int]]] = None,
        temps_service: Optional[List[int]] = None,
        nombre_vehicules: int = 1
    ):
        """
        Initialise le problème VRP.
        
        Args:
            depot: Coordonnées (x, y) du dépôt
            clients: Liste des coordonnées (x, y) des clients
            demandes: Liste des demandes de chaque client
            capacite_vehicule: Capacité maximale d'un véhicule (déprécié, utiliser capacites_vehicules)
            capacites_vehicules: Liste des capacités de chaque véhicule
            fenetres_temps: Liste de (début, fin) pour chaque client (optionnel)
            temps_service: Temps de service à chaque client (optionnel)
            nombre_vehicules: Nombre de véhicules disponibles
        """
        self.depot = depot
        self.clients = clients
        self.demandes = demandes
        self.fenetres_temps = fenetres_temps or [(0, 10000)] * len(clients)
        self.temps_service = temps_service or [0] * len(clients)
        self.nombre_vehicules = nombre_vehicules
        
        # gestion des capacités : priorité à capacites_vehicules
        if capacites_vehicules:
            self.capacites_vehicules = capacites_vehicules[:nombre_vehicules]
            if len(self.capacites_vehicules) < nombre_vehicules:
                derniere = self.capacites_vehicules[-1] if self.capacites_vehicules else 50
                self.capacites_vehicules.extend([derniere] * (nombre_vehicules - len(self.capacites_vehicules)))
        elif capacite_vehicule:
            self.capacites_vehicules = [capacite_vehicule] * nombre_vehicules
        else:
            self.capacites_vehicules = [50] * nombre_vehicules
        
        # compatibilité avec l'ancien code
        self.capacite_vehicule = self.capacites_vehicules[0] if self.capacites_vehicules else 50
        
        # calcul des distances euclidiennes
        self.distances = self._calculer_distances()
        
        # nombre de nœuds (dépôt + clients)
        self.n = len(clients) + 1
        self.num_clients = len(clients)
        
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """calcule la distance en kilomètres entre deux points GPS (formule de Haversine)"""
        # rayon de la terre en kilomètres
        R = 6371.0
        
        # conversion en radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # différences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # formule de Haversine
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # distance en kilomètres
        distance = R * c
        return distance
    
    def _calculer_distances(self) -> np.ndarray:
        """calcule la matrice des distances en kilomètres entre tous les points"""
        points = [self.depot] + self.clients
        n = len(points)
        distances = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # points[i] = (latitude, longitude)
                    lat1, lon1 = points[i]
                    lat2, lon2 = points[j]
                    distances[i][j] = self._haversine_distance(lat1, lon1, lat2, lon2)
        
        return distances
    
    def resoudre(self, limite_temps: int = 30) -> Dict:
        """
        Résout le problème VRP avec CP-SAT.
        
        Args:
            limite_temps: Temps limite de résolution en secondes
            
        Returns:
            Dictionnaire contenant les tournées, distance totale, et statut
        """
        model = cp_model.CpModel()
        
        # variables de décision
        # x[i][j][k] = 1 si le véhicule k va de i à j
        x = {}
        for k in range(self.nombre_vehicules):
            for i in range(self.n):
                for j in range(self.n):
                    if i != j:
                        x[i, j, k] = model.NewBoolVar(f'x_{i}_{j}_{k}')
        
        # variables pour l'ordre de visite (position dans la tournée)
        position = {}
        for k in range(self.nombre_vehicules):
            for i in range(self.n):
                position[i, k] = model.NewIntVar(0, self.n, f'pos_{i}_{k}')
        
        # variables pour le temps d'arrivée
        temps_arrivee = {}
        for k in range(self.nombre_vehicules):
            for i in range(self.n):
                temps_arrivee[i, k] = model.NewIntVar(0, 10000, f'time_{i}_{k}')
        
        # variables pour la charge du véhicule
        charge = {}
        for k in range(self.nombre_vehicules):
            capacite_k = self.capacites_vehicules[k] if k < len(self.capacites_vehicules) else self.capacite_vehicule
            for i in range(self.n):
                charge[i, k] = model.NewIntVar(0, capacite_k, f'load_{i}_{k}')
        
        # contraintes : chaque client visité exactement une fois
        for j in range(1, self.n):  # exclut le dépôt
            model.Add(sum(x[i, j, k] for i in range(self.n) for k in range(self.nombre_vehicules) if i != j) == 1)
        
        # contraintes : chaque véhicule part du dépôt
        for k in range(self.nombre_vehicules):
            model.Add(sum(x[0, j, k] for j in range(1, self.n)) <= 1)
            model.Add(sum(x[i, 0, k] for i in range(1, self.n)) <= 1)
        
        # contraintes : conservation de flux
        for k in range(self.nombre_vehicules):
            for j in range(self.n):
                model.Add(
                    sum(x[i, j, k] for i in range(self.n) if i != j) ==
                    sum(x[j, i, k] for i in range(self.n) if i != j)
                )
        
        # contraintes : capacité
        for k in range(self.nombre_vehicules):
            capacite_k = self.capacites_vehicules[k] if k < len(self.capacites_vehicules) else self.capacite_vehicule
            # départ du dépôt avec charge 0
            model.Add(charge[0, k] == 0)
            
            for j in range(1, self.n):
                # si on va de i à j avec le véhicule k
                for i in range(self.n):
                    if i != j:
                        demande_j = self.demandes[j-1]  # j-1 car dépôt est index 0
                        model.Add(
                            charge[j, k] >= charge[i, k] + demande_j - 
                            capacite_k * (1 - x[i, j, k])
                        )
                        model.Add(
                            charge[j, k] <= charge[i, k] + demande_j + 
                            capacite_k * (1 - x[i, j, k])
                        )
        
        # contraintes : fenêtres temporelles
        for k in range(self.nombre_vehicules):
            # départ du dépôt à t=0
            model.Add(temps_arrivee[0, k] == 0)
            
            for j in range(1, self.n):
                debut, fin = self.fenetres_temps[j-1]
                model.Add(temps_arrivee[j, k] >= debut)
                model.Add(temps_arrivee[j, k] <= fin)
                
                # temps de trajet et service
                for i in range(self.n):
                    if i != j:
                        dist = int(self.distances[i][j])
                        # temps de service : 0 pour le dépôt, sinon temps_service[i-1]
                        temps_serv = self.temps_service[i-1] if i > 0 else 0
                        model.Add(
                            temps_arrivee[j, k] >= temps_arrivee[i, k] + 
                            temps_serv + dist - 
                            10000 * (1 - x[i, j, k])
                        )
        
        # contraintes : position dans la tournée (pour éviter les sous-tours)
        for k in range(self.nombre_vehicules):
            model.Add(position[0, k] == 0)
            
            for i in range(1, self.n):
                for j in range(1, self.n):
                    if i != j:
                        model.Add(
                            position[j, k] >= position[i, k] + 1 - 
                            self.n * (1 - x[i, j, k])
                        )
        
        # objectif : minimiser la distance totale
        objectif = []
        for k in range(self.nombre_vehicules):
            for i in range(self.n):
                for j in range(self.n):
                    if i != j:
                        dist = int(self.distances[i][j] * 100)  # conversion en entiers
                        objectif.append(dist * x[i, j, k])
        
        model.Minimize(sum(objectif))
        
        # résolution
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = limite_temps
        status = solver.Solve(model)
        
        # extraction des résultats
        tournees = []
        distance_totale = 0
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            for k in range(self.nombre_vehicules):
                tournee = [0]  # commence au dépôt
                current = 0
                distance_vehicule = 0
                
                while True:
                    trouve = False
                    for j in range(self.n):
                        if j != current and solver.Value(x[current, j, k]) == 1:
                            tournee.append(j)
                            distance_vehicule += self.distances[current][j]
                            current = j
                            trouve = True
                            break
                    
                    if not trouve or current == 0:
                        break
                
                if len(tournee) > 1:  # si le véhicule a été utilisé
                    tournees.append(tournee)
                    distance_totale += distance_vehicule
        
        return {
            'statut': 'optimal' if status == cp_model.OPTIMAL else 'feasible' if status == cp_model.FEASIBLE else 'infeasible',
            'tournees': tournees,
            'distance_totale': distance_totale,
            'nombre_vehicules_utilises': len(tournees)
        }

