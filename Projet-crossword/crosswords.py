"""Generer des grilles de mots croises avec la programmation par contraintes.
Utilise Google OR-Tools CP-SAT solver.

"""


import sys

from ortools.sat.python import cp_model


def word_to_numbers(word):
    """Renvoie la liste des nombres associes a un mot."""
    return list(' ABCDEFGHIJKLMNOPQRSTUVWXYZ'.find(letter)
                for letter in word.upper())


def load_words(path):
    """Charge les mots depuis un fichier et renvoie un dictionnaire de mots et leurs indices.

    Le fichier source doit contenir un mot par ligne, avec la possibilite d'ajouter un indice en
    separant le mot et l'indice par le caractere "|".

   
    Remarque : le dernier element de chaque tuple est l'identifiant du mot.
    Cette fonction renvoie un tuple (wordlist, metadata). `metadata` est un dictionnaire
    {id: {"mot": WORD, "indice": INDICE}}.
    """
    with open(path, "r", encoding="utf-8") as f:
        words = list(word.strip() for word in f.readlines())

    wordlist = {}
    metadata = {}

    i = 0  # Compteur d'identifiants.

    for word in words:
        if not word:
            continue

        if "|" in word:
            mot, indice = word.split("|", 1)
            mot = mot.strip()
            indice = indice.strip()
        else:
            mot = word.strip()
            indice = ""

        if not mot:
            continue

        if not indice:
            indice = f"Mot de {len(mot)} lettres."

        word_length = len(mot)

        # On ajoute l'identifiant comme une lettre supplementaire a la fin du mot.
        if word_length in wordlist.keys():
            wordlist[word_length].append(word_to_numbers(mot) + [i])

        else:
            wordlist[word_length] = [word_to_numbers(mot) + [i]]

        metadata[i] = {
            "mot": mot.upper(),
            "indice": indice,
        }

        i += 1  # Incremente l'identifiant pour le mot suivant.

    return wordlist, metadata


def table(model, variables, tuples, option):
    """Ajoute au modele une contrainte TABLE (AddAllowedAssignments()) optionnelle.

    Une contrainte TABLE est appliquee a `model`, ou `variables` prennent les valeurs
    d'un des `tuples`, uniquement lorsque `option` vaut vrai.
    """
    # Une variable booleenne par tuple indique si les valeurs de ce tuple sont assignees ou non.
    b = [model.NewBoolVar(f"b[{i}]") for i in range(len(tuples))]

    # Ensemble des valeurs assignables a chaque variable.
    possible_values = {i: set() for i in range(len(variables))}
    max_value = max(max(t) for t in tuples)
    for t in tuples:
        for i, j in enumerate(t):
            possible_values[i].add(j)

    # is_assigned[i][j] indique si la variable `i` prend la valeur `j`.
    is_assigned = [[model.NewBoolVar(f"is_assigned[{i}][{j}]")
                    for j in range(max_value+1)]
                   for i in range(len(variables))]

    # Certaines affectations sont impossibles car la valeur n'apparait dans aucun tuple.
    for i in range(len(variables)):
        for j in range(max_value+1):
            if j not in possible_values[i]:
                model.Add(is_assigned[i][j] == 0).OnlyEnforceIf(option)

    # Chaque variable doit recevoir exactement une valeur.
    for i in is_assigned:
        model.Add(cp_model.LinearExpr.Sum(i) == 1).OnlyEnforceIf(option)

    # Lie `is_assigned` et `variables`.
    for i in range(len(variables)):
        for j in range(max_value+1):
            model.Add(variables[i] == j).OnlyEnforceIf(is_assigned[i][j])

    # Contrainte TABLE.
    for i, t in enumerate(tuples):
        model.AddBoolAnd([is_assigned[j][t[j]] for j in range(len(t))]).OnlyEnforceIf(b[i])

    # Un seul tuple peut etre assigne aux variables.
    model.Add(cp_model.LinearExpr.Sum(b) == 1).OnlyEnforceIf(option)


DEFAULT_WORDLIST = "wordlist.txt"
DEFAULT_ROWS = 6
DEFAULT_COLUMNS = 8
# Ratio maximum de cases noires dans la grille pour garder des grilles jouables.
MAX_BLACK_RATIO = 0.35


def generer_grille(rows=DEFAULT_ROWS, columns=DEFAULT_COLUMNS, wordlist_path=DEFAULT_WORDLIST):
    """Construit et resout un modele et renvoie le statut, la grille et les indices."""
    wordlist, metadata = load_words(wordlist_path)
    model = cp_model.CpModel()

    # L[r][c] represente la lettre a la ligne `r` et la colonne `c`.
    # A = 1, B = 2, etc., et une case noire vaut 0.
    L = [[model.NewIntVar(0, 26, f"L[{r}][{c}]")
          for c in range(columns)]
         for r in range(rows)]

    # B[r][c] == 1 s'il y a une case noire a la ligne `r` et la colonne `c`, sinon 0.
    B = [[model.NewBoolVar(f"B[{r}][{c}]")
          for c in range(columns)]
         for r in range(rows)]

    # Lie B et L.
    for r in range(rows):
        for c in range(columns):
            model.Add(L[r][c] == 0).OnlyEnforceIf(B[r][c])
            model.Add(L[r][c] != 0).OnlyEnforceIf(B[r][c].Not())

    # A[l][r][c] == 1 si un mot horizontal de longueur `l` commence en (`r`, `c`), sinon 0.
    A = [[[model.NewBoolVar(f"A[{l}][{r}][{c}]")
           for c in range(columns)]
          for r in range(rows)]
         for l in range(columns+1)]

    # IA[r][c] represente l'identifiant du mot horizontal commencant en (`r`, `c`).
    IA = [[model.NewIntVar(0, sum(len(wordlist[l]) for l in wordlist) + rows*columns*2, f"IA[{r}][{c}]")
           for c in range(columns)]
          for r in range(rows)]

    # Contraintes horizontales qui empechent aussi le chevauchement des mots.
    for l in range(columns+1):
        for r in range(rows):
            for c in range(columns):
                # A[l][r][c] == 0 s'il n'existe aucun mot de longueur `l`.
                if l not in wordlist:
                    model.Add(A[l][r][c] == 0)

                # A[l][r][c] == 0 si l'espace restant a droite est insuffisant.
                elif l > columns - c:
                    model.Add(A[l][r][c] == 0)

                # Le mot rentre sur la ligne. S'il commence en (`r`, `c`), aucun autre mot ne peut
                # debuter dedans ou juste a cote. Le mot doit aussi etre borde par le bord ou une case
                # noire.
                else:
                    # Le mot remplit toute la ligne.
                    if l == columns:
                        model.Add(cp_model.LinearExpr.Sum(list(A[i][r][c+j]
                                                               for i in range(columns+1)
                                                               for j in range(columns-c)))
                                  == 1).OnlyEnforceIf(A[l][r][c])

                    # Le mot commence sur le bord gauche sans remplir toute la ligne.
                    elif c == 0:
                        model.Add(cp_model.LinearExpr.Sum(list(A[i][r][c+j]
                                                               for i in range(columns+1)
                                                               for j in range(l+1)))
                                  == 1).OnlyEnforceIf(A[l][r][c])

                    # Le mot termine au bord droit sans remplir toute la ligne.
                    elif c + l == columns:
                        model.Add(cp_model.LinearExpr.Sum(list(A[i][r][c+j]
                                                               for i in range(columns+1)
                                                               for j in range(columns-c)))
                                  == 1).OnlyEnforceIf(A[l][r][c])

                    # Le mot ne commence ni ne finit sur un bord.
                    else:
                        model.Add(cp_model.LinearExpr.Sum(list(A[i][r][c-1+j]
                                                               for i in range(columns+1)
                                                               for j in range(l+2)))
                                  == 1).OnlyEnforceIf(A[l][r][c])

                    # Comme `AddAllowedAssignments().OnlyEnforceIf()` n'est pas supporte, on reproduit
                    # le comportement a la main.
                    table(model, [L[r][c+i] for i in range(l)] + [IA[r][c]], wordlist[l], A[l][r][c])

    # D[l][r][c] == 1 si un mot vertical de longueur `l` commence en (`r`, `c`), sinon 0.
    D = [[[model.NewBoolVar(f"D[{l}][{r}][{c}]")
           for c in range(columns)]
          for r in range(rows)]
         for l in range(rows+1)]

    # ID[r][c] represente l'identifiant du mot vertical commencant en (`r`, `c`).
    ID = [[model.NewIntVar(0, sum(len(wordlist[l]) for l in wordlist) + rows*columns*2, f"ID[{r}][{c}]")
           for c in range(columns)]
          for r in range(rows)]

    # Contraintes verticales qui evitent aussi le chevauchement.
    for l in range(rows+1):
        for r in range(rows):
            for c in range(columns):
                # D[l][r][c] == 0 s'il n'existe aucun mot de longueur `l`.
                if l not in wordlist:
                    model.Add(D[l][r][c] == 0)

                # D[l][r][c] == 0 si l'espace en bas est insuffisant.
                elif l > rows - r:
                    model.Add(D[l][r][c] == 0)

                # Le mot tient dans la colonne. S'il commence en (`r`, `c`), aucun autre mot ne peut
                # debuter dedans ou juste a cote. Le mot doit aussi etre borde par le bord ou une case
                # noire.
                else:
                    # Le mot remplit toute la colonne.
                    if l == rows:
                        model.Add(cp_model.LinearExpr.Sum(list(D[i][r+j][c]
                                                               for i in range(rows+1)
                                                               for j in range(rows-r)))
                                  == 1).OnlyEnforceIf(D[l][r][c])

                    # Le mot commence sur le bord superieur sans remplir toute la colonne.
                    elif r == 0:
                        model.Add(cp_model.LinearExpr.Sum(list(D[i][r+j][c]
                                                               for i in range(rows+1)
                                                               for j in range(l+1)))
                                  == 1).OnlyEnforceIf(D[l][r][c])

                    # Le mot finit sur le bord inferieur sans remplir toute la colonne.
                    elif r + l == rows:
                        model.Add(cp_model.LinearExpr.Sum(list(D[i][r+j][c]
                                                               for i in range(rows+1)
                                                               for j in range(rows-r)))
                                  == 1).OnlyEnforceIf(D[l][r][c])

                    # Le mot ne commence ni ne finit sur un bord.
                    else:
                        model.Add(cp_model.LinearExpr.Sum(list(D[i][r-1+j][c]
                                                               for i in range(rows+1)
                                                               for j in range(l+2)))
                                  == 1).OnlyEnforceIf(D[l][r][c])

                    # Comme `AddAllowedAssignments().OnlyEnforceIf()` n'est pas supporte, on reproduit
                    # le comportement a la main.
                    table(model, [L[r+i][c] for i in range(l)] + [ID[r][c]], wordlist[l], D[l][r][c])

    # Garantit que tous les mots sont differents.
    model.AddAllDifferent([IA[r][c]
                           for r in range(rows)
                           for c in range(columns)] +
                          [ID[r][c]
                           for r in range(rows)
                           for c in range(columns)])

    # LLA[r][c] == 1 si la lettre horizontale en (`r`, `c`) est seule, sinon 0.
    LLA = [[model.NewBoolVar(f"LLA[{r}][{c}]")
            for c in range(columns)]
           for r in range(rows)]

    # Contraintes pour LLA : une lettre est seule si elle est bornee par un bord ou une case noire.
    for r in range(rows):
        # Cases adjacentes au bord.
        model.Add(LLA[r][0] == B[r][1])
        model.Add(LLA[r][columns-1] == B[r][columns-2])

        # Autres cases.
        for c in range(1, columns-1):
            model.Add(B[r][c-1] + B[r][c+1] == 2).OnlyEnforceIf(LLA[r][c])
            model.Add(B[r][c-1] + B[r][c+1] <= 1).OnlyEnforceIf(LLA[r][c].Not())

    # LLAB[r][c] == 1 si la lettre horizontale en (`r`, `c`) est seule ou une case noire, sinon 0.
    LLAB = [[model.NewBoolVar(f"LLAB[{r}][{c}]")
             for c in range(columns)]
            for r in range(rows)]

    # Contraintes pour LLAB.
    for r in range(rows):
        for c in range(columns):
            model.Add(LLA[r][c] + B[r][c] >= 1).OnlyEnforceIf(LLAB[r][c])
            model.Add(LLA[r][c] + B[r][c] == 0).OnlyEnforceIf(LLAB[r][c].Not())

    # Si une case contient une lettre qui n'est pas seule, un mot horizontal couvrant cette case
    # doit etre actif.
    for r in range(rows):
        for c in range(columns):
            model.Add(cp_model.LinearExpr.Sum(list(A[i][r][c-j]
                                                   for i in range(columns+1)
                                                   for j in range(min(i, c+1))))
                      == 1).OnlyEnforceIf(LLAB[r][c].Not())

    # LLD[r][c] == 1 si la lettre verticale en (`r`, `c`) est seule, sinon 0.
    LLD = [[model.NewBoolVar(f"LLD[{r}][{c}]")
            for c in range(columns)]
           for r in range(rows)]

    # Contraintes pour LLD : une lettre est seule si elle est bornee par un bord ou une case noire.
    for c in range(columns):
        # Cases adjacentes au bord.
        model.Add(LLD[0][c] == B[1][c])
        model.Add(LLD[rows-1][c] == B[rows-2][c])

        # Autres cases.
        for r in range(1, rows-1):
            model.Add(B[r-1][c] + B[r+1][c] == 2).OnlyEnforceIf(LLD[r][c])
            model.Add(B[r-1][c] + B[r+1][c] <= 1).OnlyEnforceIf(LLD[r][c].Not())

    # LLDB[r][c] == 1 si la lettre verticale en (`r`, `c`) est seule ou une case noire, sinon 0.
    LLDB = [[model.NewBoolVar(f"LLDB[{r}][{c}]")
             for c in range(columns)]
            for r in range(rows)]

    # Contraintes pour LLDB.
    for r in range(rows):
        for c in range(columns):
            model.Add(LLD[r][c] + B[r][c] >= 1).OnlyEnforceIf(LLDB[r][c])
            model.Add(LLD[r][c] + B[r][c] == 0).OnlyEnforceIf(LLDB[r][c].Not())

    # Si une case contient une lettre qui n'est pas seule, un mot vertical couvrant cette case
    # doit etre actif.
    for r in range(rows):
        for c in range(columns):
            model.Add(cp_model.LinearExpr.Sum(list(D[i][r-j][c]
                                                   for i in range(rows+1)
                                                   for j in range(min(i, r+1))))
                      == 1).OnlyEnforceIf(LLDB[r][c].Not())

    # Une lettre ne doit pas etre seule a la fois horizontalement et verticalement.
    for r in range(rows):
        for c in range(columns):
            model.Add(LLA[r][c] + LLD[r][c] <= 1)

    # Evite que les sous-grilles 3x3 aient trop de cases noires, ce qui empeche aussi
    # les sous-grilles independantes.
    if rows >= 3 and columns >= 3:
        for r in range(0, rows-2):
            for c in range(0, columns-2):
                model.Add(cp_model.LinearExpr.Sum(list(B[i][j]
                                                       for i in range(r, r+3)
                                                       for j in range(c, c+3)))
                          <= 3)

    # Limite le nombre de cases noires.
    max_black_cells = max(1, int(rows * columns * MAX_BLACK_RATIO))
    model.Add(cp_model.LinearExpr.Sum(
        list(cp_model.LinearExpr.Sum(
            list(c for c in row)) for row in B))
              <= max_black_cells)

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 8
    solver.parameters.max_time_in_seconds = 30
    status = solver.Solve(model)
    status_name = solver.StatusName(status)

    grille = None
    indices = {"across": [], "down": []}

    if status_name == "OPTIMAL":
        alphabet = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        grille = []
        for r in range(rows):
            ligne = []
            for c in range(columns):
                ligne.append(alphabet[solver.Value(L[r][c])])
            grille.append(ligne)

        numero_horizontal = 1
        for l in range(1, columns+1):
            for r in range(rows):
                for c in range(columns):
                    if solver.Value(A[l][r][c]) == 1:
                        mot_id = solver.Value(IA[r][c])
                        info = metadata.get(mot_id)
                        if not info:
                            continue
                        indices["across"].append({
                            "numero": numero_horizontal,
                            "ligne": r + 1,
                            "colonne": c + 1,
                            "longueur": l,
                            "mot": info["mot"],
                            "indice": info["indice"],
                        })
                        numero_horizontal += 1

        numero_vertical = 1
        for l in range(1, rows+1):
            for r in range(rows):
                for c in range(columns):
                    if solver.Value(D[l][r][c]) == 1:
                        mot_id = solver.Value(ID[r][c])
                        info = metadata.get(mot_id)
                        if not info:
                            continue
                        indices["down"].append({
                            "numero": numero_vertical,
                            "ligne": r + 1,
                            "colonne": c + 1,
                            "longueur": l,
                            "mot": info["mot"],
                            "indice": info["indice"],
                        })
                        numero_vertical += 1

    return status_name, grille, indices


def afficher_grille(lettres):
    """Affiche la grille sous forme tabulaire."""
    if not lettres:
        print("Grille vide")
        return

    bord = "+" + "+".join(["---"] * len(lettres[0])) + "+"
    for ligne in lettres:
        print(bord)
        contenu = [" " if case == "#" else case for case in ligne]
        print("| " + " | ".join(contenu) + " |")
    print(bord)


if __name__ == "__main__":
    statut, grille, indices = generer_grille()
    print(f"Status: {statut}")
    print()

    if statut != "OPTIMAL":
        print("Un probleme est survenu :(")
        sys.exit()

    afficher_grille(grille)
    print()
    if indices["across"]:
        print("Indices horizontaux :")
        for indice in indices["across"]:
            print(f"  {indice['numero']}. ({indice['longueur']} lettres) {indice['indice']}")
    if indices["down"]:
        print("\nIndices verticaux :")
        for indice in indices["down"]:
            print(f"  {indice['numero']}. ({indice['longueur']} lettres) {indice['indice']}")
