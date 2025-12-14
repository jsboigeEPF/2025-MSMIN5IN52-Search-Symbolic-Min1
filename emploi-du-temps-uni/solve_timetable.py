#!/usr/bin/env python3
"""
Script Python pour résoudre le problème de planification d'emploi du temps universitaire
en utilisant MiniZinc via pyminizinc.
"""

import minizinc
import sys

def main():
    try:
        # Charger le modèle MiniZinc
        model = minizinc.Model("timetable.mzn")
        model.add_file("data.dzn")

        # Sélectionner un solveur (Gecode pour satisfaction)
        solver = minizinc.Solver.lookup("gecode")

        # Créer une instance
        instance = minizinc.Instance(solver, model)

        # Résoudre
        print("Résolution du problème d'emploi du temps...")
        result = instance.solve()  # Timeout de 60 secondes

        if result.status == minizinc.Status.SATISFIED:
            print("Solution trouvée !")
            print("Emploi du temps :")
            for e in range(1, result['num_events'] + 1):
                teacher = result['event_teacher'][e-1]
                start = result['event_start'][e-1]
                room = result['event_room'][e-1]
                print(f"Cours {e}: Professeur {teacher}, Début {start}, Salle {room}")
        elif result.status == minizinc.Status.UNSATISFIABLE:
            print("Aucune solution trouvée. Le problème est insatisfaisable.")
        else:
            print(f"Statut: {result.status}")

    except Exception as e:
        print(f"Erreur: {e}")
        print("Assurez-vous que MiniZinc est installé et accessible.")
        sys.exit(1)

if __name__ == "__main__":
    main()