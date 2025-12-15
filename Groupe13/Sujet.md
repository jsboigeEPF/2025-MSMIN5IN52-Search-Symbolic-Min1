### 13. Problème des mariages stables (Stable Marriage)

**Description du problème et contexte**
L'appariement bipartite entre deux ensembles (étudiants et postes, ou hommes et femmes dans le problème classique) sur la base de préférences de classement mutuelles. Un matching est stable s'il n'existe pas deux agents qui se préfèreraient mutuellement à leurs attributions actuelles. L'algorithme de Gale & Shapley (1962) garantit une solution stable en temps polynomial via les propositions différées. On peut aussi formuler le problème en CSP : rechercher une affectation (bijection) sans paire bloquante.

**Références multiples**
- **Article fondateur** : Gale & Shapley (1962), _College Admissions and Stability_ - Algorithme des propositions différées
- **Modélisation CP** : Manlove & O'Malley (CP 2008), [Modelling Stable Marriage with CP](https://www.dcs.gla.ac.uk/~davidm/pubs/7981.pdf) - Deux encodages CSP et lien avec Gale-Shapley
- **Ouvrage de référence** : Gusfield & Irving (1989), _The Stable Marriage Problem: Structure and Algorithms_ - Théorie complète
- **Applications réelles** : Hospital-Resident matching utilisé pour l'affectation des internes en médecine

**Approches suggérées**
- Modéliser comme un CSP avec variables d'affectation et contraintes de stabilité
- Implémenter l'algorithme de Gale-Shapley pour comparaison avec approche CP
- Établir l'arc-consistance équivalent à l'élimination des paires incompatibles
- Explorer les variantes (capacités multiples, listes incomplètes, liens indifférents)

**Technologies pertinentes**
- Python avec implémentation classique de Gale-Shapley pour référence
- OR-Tools ou MiniZinc pour la modélisation CSP alternative
- NetworkX pour visualiser les préférences et appariements
- Jupyter Notebook pour analyses comparatives des différentes approches

---