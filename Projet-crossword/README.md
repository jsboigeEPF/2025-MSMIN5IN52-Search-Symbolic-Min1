# Crossword Generator

Generer des grilles de mots croises a l'aide de la programmation par contraintes et jouez-y via une interface web.

Le billet de blog associe est disponible [ici](https://pedtsr.ca/2023/generating-crossword-grids-using-constraint-programming.html).

## Installation

1. (Optionnel) Creez un environnement virtuel :
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Installez les dependances necessaires :
   ```bash
   pip install ortools streamlit
   ```
   (l'environnement fourni dans ce depot contient deja `ortools`.)

## Utilisation en ligne de commande

Le script `crosswords.py` genere une grille, affiche le statut du solveur et dessine la grille dans le terminal.
Il liste egalement les indices horizontaux et verticaux trouves.

```bash
python crosswords.py
```

Utilisez les parametres par defaut (6 x 8) ou importez la fonction `generer_grille` pour ajuster la taille et la liste de mots depuis un autre script.

## Application Streamlit

Une application interactive est disponible dans `streamlit_app.py` :

```bash
streamlit run streamlit_app.py
```

Fonctionnalites principales :
- Generation d'une nouvelle grille depuis la barre laterale (dimensions configurables).
- Interface de jeu permettant de saisir les lettres directement dans la grille.
- Bouton de verification qui calcule le score (lettres correctes / total) et indices affiches dans la page.
- Bouton pour effacer les reponses et expander facultatif pour afficher la solution.

### Format de `wordlist.txt`

Chaque ligne peut contenir juste un mot, ou bien un mot suivi d'un indice separe par `|` :

```
POMME|Fruit croquant
MER
```

Si aucun indice n'est fourni, un indice generique « Mot de N lettres » sera utilise.

Amusez-vous bien !
