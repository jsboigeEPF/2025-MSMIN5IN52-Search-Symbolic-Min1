# Projet : Recherche Symbolique — Stable Marriage et Wordle

Ce dépôt contient des travaux de groupe portant sur l'analyse du problème du mariage stable (Stable Marriage) et un solveur Wordle.

---

## 1. Analyse du Problème du Mariage Stable

Le fichier principal pour cette partie est `stable_marriage_analysis.ipynb`.

### Contenu du Notebook

- Implémentation de l'algorithme de référence de **Gale-Shapley**.
- Modélisation du problème en **Programmation par Contraintes (CSP)** avec la bibliothèque Google OR-Tools.
- Fonctions pour :
  - Générer des instances de test.
  - Valider la stabilité d'une solution.
  - Benchmarker les performances des deux approches.
  - Visualiser les résultats.

### Installation et Lancement

Suivez ces étapes pour configurer l'environnement et exécuter le notebook `stable_marriage_analysis.ipynb`.

**Note :** Le projet contient plusieurs fichiers `requirements.txt`. Pour cette analyse, assurez-vous d'utiliser celui situé dans le dossier `Groupe13/`.

1.  **Créer et Activer l'Environnement Virtuel** (recommandé) :
    ```shell
    # Créer l'environnement
    python -m venv .venv

    # Activer sous Windows (PowerShell)
    .\.venv\Scripts\activate
    ```

2.  **Installer les Dépendances** :
    Exécutez la commande suivante depuis la racine du projet pour installer toutes les bibliothèques nécessaires (`numpy`, `matplotlib`, `ortools`, etc.).
    ```shell
    pip install -r Groupe13/requirements.txt
    ```

3.  **Configurer le Noyau Jupyter** (Optionnel) :
    Cette étape garantit que Jupyter utilise les bonnes dépendances.
    ```shell
    # 1. S'assurer qu'ipykernel est installé
    pip install ipykernel

    # 2. Créer un noyau Jupyter lié à votre .venv
    python -m ipykernel install --user --name=groupe13 --display-name="Python (Groupe13)"
    ```

4.  **Lancer le Notebook** :
    - Lancez Jupyter Notebook ou VS Code.
    - Ouvrez `stable_marriage_analysis.ipynb`.
    - Si vous y êtes invité ou si vous rencontrez des erreurs de module, assurez-vous de sélectionner le noyau **"Python (Groupe13)"**. (Dans Jupyter : `Kernel > Change kernel` ; Dans VS Code : cliquez sur le sélecteur de noyau en haut à droite).
    - Exécutez les cellules.

### Tests

Un test unitaire a été ajouté pour valider la cohérence entre le modèle CSP et l'algorithme de Gale-Shapley. Pour le lancer :
```shell
# Assurez-vous que l'environnement .venv est activé
python -m pytest Groupe13/tests/test_stable_marriage.py
```