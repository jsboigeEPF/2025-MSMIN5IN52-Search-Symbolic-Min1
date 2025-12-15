# Explication Détaillée du Notebook : Analyse du Problème des Mariages Stables

Ce document détaille le fonctionnement, les algorithmes et la logique du notebook `stable_marriage_analysis.ipynb`.

## Objectif du Notebook

L'objectif principal est de résoudre le **problème des mariages stables** en utilisant deux approches distinctes et de les comparer :
1.  L'algorithme classique et déterministe de **Gale-Shapley**.
2.  Une modélisation en **Programmation par Contraintes (CSP)**, résolue avec le solveur CP-SAT de la bibliothèque **Google OR-Tools**.

Le notebook compare ces deux méthodes en termes de correction (stabilité de la solution) et de performance (temps d'exécution).

---

## Structure et Déroulement

Le notebook est divisé en quatre phases principales.

### Phase 1 : Algorithme de Gale-Shapley (Solution de Référence)

Cette phase implémente l'algorithme de Gale-Shapley, qui sert de "vérité terrain" (ground truth) grâce à sa garantie de produire toujours une solution stable.

#### 1.1. Génération des Préférences (`generate_preferences`)

-   **But :** Créer les données d'entrée pour le problème.
-   **Fonctionnement :** La fonction `generate_preferences(n)` génère deux matrices NumPy de taille `n x n` : `men_prefs` et `women_prefs`.
-   Chaque ligne de ces matrices représente les préférences d'un individu (homme ou femme).
-   Une ligne est une permutation aléatoire des indices des membres du sexe opposé. Par exemple, `men_prefs[0] = [1, 4, 2, 0, 3]` signifie que l'homme `0` préfère la femme `1` en premier, puis la `4`, et ainsi de suite.

#### 1.2. Implémentation de Gale-Shapley (`gale_shapley`)

-   **But :** Trouver un appariement stable en utilisant l'approche "les hommes proposent" (men-proposing).
-   **Logique de l'algorithme :**
    1.  On initialise une liste d'hommes "libres" (`free_men`). Tous les hommes le sont au départ.
    2.  Tant qu'il y a des hommes libres, on en choisit un (`man`).
    3.  L'homme `man` propose à la femme (`woman`) qu'il préfère le plus parmi celles à qui il n'a pas encore fait de proposition.
    4.  La femme `woman` reçoit la proposition :
        -   Si elle est libre, elle accepte provisoirement et forme un couple avec `man`.
        -   Si elle est déjà en couple avec un autre homme (`current_husband`), elle compare `man` à `current_husband`. Si elle préfère le nouvel arrivant (`man`), elle rompt avec `current_husband` (qui redevient libre) et se met en couple avec `man`. Sinon, elle rejette `man`, qui reste libre.
    5.  L'homme `man`, s'il est rejeté, continue de proposer à la femme suivante dans sa liste de préférences.
-   **Optimisation :** Pour comparer rapidement les préférences des femmes, une **matrice de rangs** (`ranking_w`) est pré-calculée. `ranking_w[w][m]` donne le rang de l'homme `m` dans les préférences de la femme `w`. Cela permet des comparaisons en O(1) au lieu d'une recherche en O(n).
-   **Garantie :** L'algorithme se termine toujours et produit un appariement stable, optimal pour le groupe qui propose (ici, les hommes). Sa complexité est de O(n²).

---

### Phase 2 : Approche par Programmation par Contraintes (CSP)

Cette phase modélise le problème de manière déclarative en utilisant le solveur CP-SAT de Google OR-Tools.

#### 2.1. Modélisation du Problème (`solve_stable_marriage_csp`)

-   **But :** Définir le problème non pas par un algorithme, mais par un ensemble de variables et de contraintes que la solution doit respecter.
-   **Variables de Décision :**
    -   La variable principale est un tableau `wife_of` de taille `n`. `wife_of[m]` est une variable entière dont la valeur (entre 0 et n-1) représentera la femme assignée à l'homme `m`.

-   **Contraintes :**
    1.  **Contrainte de Bijection :** `model.AddAllDifferent(wife_of)`
        -   Cette contrainte fondamentale assure que chaque homme est assigné à une femme unique, et donc que chaque femme est assignée à un homme unique. C'est la définition d'un appariement parfait.

    2.  **Contrainte de Stabilité (la plus complexe) :**
        -   Le but est d'interdire les **paires bloquantes**.
        -   Une paire `(m, w)` est bloquante si :
            -   L'homme `m` préfère la femme `w` à sa partenaire assignée (`wife_of[m]`).
            -   ET la femme `w` préfère l'homme `m` à son partenaire assigné.
        -   **Implémentation :** Le code itère sur toutes les paires possibles d'hommes et de femmes `(m, w)` qui ne sont pas appariés. Pour chaque paire, il ajoute une contrainte qui interdit la situation où `m` et `w` se préfèrent mutuellement à leurs partenaires respectifs. La méthode `AddForbiddenAssignments` est utilisée pour implémenter cette logique de manière efficace. Elle interdit au solveur d'assigner à `wife_of[m]` et `husband_of[w]` des partenaires qui rendraient la paire `(m, w)` bloquante.

-   **Résolution :** Le solveur `cp_model.CpSolver()` explore l'espace des solutions possibles pour trouver un assignement des variables qui satisfait toutes les contraintes.

---

### Phase 3 : Validation de la Stabilité

-   **But :** Vérifier que les solutions trouvées par les deux algorithmes sont bien stables.
-   **Fonction `is_stable` :**
    -   Elle prend en entrée un appariement et les matrices de préférences.
    -   Elle itère sur **toutes les paires possibles** d'un homme `m` et d'une femme `w`.
    -   Pour chaque paire, elle vérifie si elle constitue une "paire bloquante" en appliquant la définition : l'homme `m` préfère-t-il `w` à sa partenaire actuelle, ET la femme `w` préfère-t-elle `m` à son partenaire actuel ?
    -   Si au moins une paire bloquante est trouvée, l'appariement est déclaré instable. Sinon, il est stable.

---

### Phase 4 : Analyse Comparative et Visualisation

-   **But :** Comparer les performances et visualiser les résultats.
-   **Benchmarking (`benchmark_algorithms`) :**
    -   Cette fonction mesure le temps d'exécution moyen des deux algorithmes (`gale_shapley` et `solve_stable_marriage_csp`) sur plusieurs essais et pour différentes tailles de problème `n` (ex: 10, 50, 100).
-   **Visualisation (`plot_benchmark_results`, `visualize_bipartite_matching`) :**
    -   Un graphique linéaire compare l'évolution des temps d'exécution.
    -   Un diagramme en barres montre le ratio de performance (CSP vs. Gale-Shapley).
    -   Pour les petites instances, un **graphe bipartite** montre visuellement l'appariement final entre les hommes et les femmes.

## Conclusion et Observations

-   **Gale-Shapley** est un algorithme spécialisé, extrêmement rapide et efficace (O(n²)), mais rigide.
-   L'approche **CSP** est beaucoup plus lente, car elle utilise un solveur générique qui explore un vaste espace de recherche. Sa performance se dégrade rapidement avec `n`. Dans les tests du notebook, le CSP devient inutilisable pour n=50 ou n=100 à cause du temps ou de la mémoire.
-   Cependant, l'avantage du CSP est sa **flexibilité**. On pourrait facilement ajouter des contraintes supplémentaires (par exemple, "l'homme 2 et la femme 3 ne peuvent pas être ensemble") sans changer l'algorithme, simplement en ajoutant une ligne au modèle.

En résumé, le notebook démontre de manière pratique le compromis classique en informatique entre un **algorithme spécialisé rapide** et une **approche déclarative plus lente mais plus flexible**.
