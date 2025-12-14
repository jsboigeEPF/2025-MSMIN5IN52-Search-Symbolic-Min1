# Planification d'emploi du temps universitaire

Ce projet implémente un système de planification d'emploi du temps pour cours et examens universitaires en utilisant MiniZinc pour la modélisation par contraintes.

## Groupe 7

### Marilson SOUZA
### Brenda KOUNDJO
### Xiner GU

## Prérequis

- Python 3.8 ou supérieur
- MiniZinc installé (téléchargeable depuis https://www.minizinc.org/downloads.html)
- Ajouter MiniZinc au PATH système

## Installation

1. Créer un environnement virtuel :
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Sur Windows
   ```

2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

### Interface web
1. Lancer l'application Flask :
   ```bash
   python app.py
   ```
2. Ouvrir http://localhost:5000 dans votre navigateur
3. Cliquer sur "Résoudre l'emploi du temps" pour générer et visualiser l'emploi du temps
 
### Fonctionnalités actuelles (état)

- Interface web en français basée sur FullCalendar (vue hebdomadaire).
- Création / suppression de `professeurs` avec disponibilités (Lun–Sam).
- Création / suppression de `cours` (nom, enseignant, nombre d'étudiants, durée par session, nombre de sessions).
- Infobulles de disponibilité (hover) affichant les plages par jour.
- Génération automatique d'un fichier `temp_data.dzn` couvrant la période Sept–Nov (jours ouvrés, créneaux 09:00–16:00) à partir des données saisies.
- Appel au solveur MiniZinc depuis Python pour résoudre le modèle `timetable.mzn`.
- Le modèle gère des sessions multi-heures, la non-collision des enseignants et des salles, la capacité des salles, et la disponibilité des enseignants sur toute la durée d'une session.
- Le solveur cherche à préférer les petites salles adaptées (objectif heuristique : minimiser la capacité totale utilisée).

### Remarques d'exploitation

- MiniZinc doit être installé sur la machine et accessible depuis le PATH pour l'appel natif au binaire. L'utilisation du package Python `minizinc` est recommandée dans l'environnement virtuel.

### Extensions possibles

- Affiner l'objectif (minimiser les places vides par session).
- Édition des enseignants/cours existants (actuellement création/suppression seulement).
- Exporter l'emploi du temps en PDF / ICS.

## Structure du projet

- `timetable.mzn` : Modèle MiniZinc du problème
- `data.dzn` : Données d'exemple
- `solve_timetable.py` : Script Python pour résoudre le modèle en ligne de commande
- `app.py` : Application Flask pour l'interface web
- `templates/index.html` : Interface web en français avec calendrier
- `requirements.txt` : Dépendances Python

## Modèle

Le modèle inclut les contraintes suivantes :
- Pas de chevauchement pour les salles
- Pas de conflit pour les enseignants
- Respect des capacités des salles
- Disponibilité des enseignants
