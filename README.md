# Job-Shop Scheduling par CSP (OR-Tools + Streamlit)

Projet academique cle en main: ordonnancement Job-Shop formule comme un probleme de satisfaction de contraintes (CSP) optimise via OR-Tools CP-SAT, avec visualisation Streamlit. L'objectif est de minimiser le makespan tout en montrant un agent rationnel deliberatif (modele explicite des contraintes, evaluation d'etats, recherche guidee par un objectif).

## Positionnement IA exploratoire et symbolique
- Modelisation declarative: variables d'intervalle, contraintes logiques explicites, propagation + recherche (CP-SAT).
- Agent rationnel: etat = assignations de debuts/fin; actions = placement d'operations; but = minimiser le makespan; fonction d'evaluation = borne inferieure CP-SAT; boucle perception-decision via le solveur.
- Separation stricte raisonnement / interpretation: `model.py` et `solver.py` encapsulent la resolution; `visualization.py` et Streamlit ne modifient pas le plan.

## Formulation CSP (CP-SAT)
- Variables: pour chaque operation (job j, operation k) un intervalle `(start_{j,k}, duration_{j,k}, end_{j,k})`.
- Contraintes:
  - Precedence intra-job: `end_{j,k} <= start_{j,k+1}`.
  - Non-chevauchement machine: `NoOverlap(operations sur la meme machine)`.
  - Definition du makespan: `end_{j,last} <= makespan`.
- Objectif: `Minimize(makespan)`.

## Architecture logicielle
```
jobshop-csp/
|-- docker-compose.yml
|-- docker/
|   `-- Dockerfile
|-- requirements.txt
|-- src/
|   |-- app.py
|   |-- data.py
|   |-- model.py
|   |-- solver.py
|   `-- visualization.py
|-- output/
|   `-- (gantt.png)
`-- README.md
```

## Lancer le projet (Docker Compose)
Prerequis: Docker et Docker Compose.
```bash
docker compose up --build
```
Puis ouvrir http://localhost:8501. Streamlit demarre automatiquement, le solveur s'execute depuis le bouton **"Resoudre / Recalculer"** et le planning est affiche.

## Visualisation interactive (Streamlit)
- Diagramme de Gantt interactif (Plotly) avec couleurs par job et axe Y = machines.
- Hover detaille: job, operation, machine, duree, start/end.
- Makespan affiche (ligne verticale) et metrics solveur (wall time, bornes, conflits, branches).
- Controle de zoom temporel, export PNG du Gantt dans `output/gantt.png`.

## Instances fournies (3 jobs x 3 machines)
- `didactic_3x3`: ordre entrelace pour illustrer les conflits machines.
- `alternating_3x3`: permutation des machines pour observer l'impact de l'ordre.
Les sequences sont definies en dur dans `src/data.py` et extensibles.

## Ajouter une instance
Dans `src/data.py`, ajouter un dictionnaire `job_sequences` (machine, duree) puis appeler `_make_instance`:
```python
custom = _make_instance(
    name="demo",
    job_sequences={
        "Job A": [("M1", 2), ("M2", 4)],
        "Job B": [("M2", 3), ("M1", 5)],
    },
    description="Petite instance pour demo",
)
```
Elle sera automatiquement disponible dans la liste deroulante Streamlit.

## Choix techniques
- OR-Tools CP-SAT pour la propagation forte et les recherches paralleles.
- Variables d'intervalle pour exprimer naturellement les fenetres de temps.
- Plotly pour le Gantt interactif et Kaleido pour l'export image.
- Container unique (Python 3.11 slim) pour reproductibilite.

## Limites et extensions possibles
- Maintenance machine: introduire des intervalles bloquants par machine et les ajouter au `NoOverlap`.
- Multi-objectif: ponderer makespan + retard moyen via une somme ponderee ou une approche epsilonee (two-phase solve).
- Calendrier non continu: fenetres de disponibilite machines (contraintes de fenetre sur start/end).
- Instances plus grandes: ajuster `time_limit`, `num_search_workers` dans `solver.solve`.

## Validation rapide
- Resolution automatique au chargement puis via le bouton Streamlit.
- Metrics solveur affichees; vous pouvez verifier la coherence des precedences dans le tableau et sur le Gantt.