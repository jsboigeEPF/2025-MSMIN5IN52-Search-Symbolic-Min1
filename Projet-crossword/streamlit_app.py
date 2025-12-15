"""Application Streamlit pour jouer avec les grilles de mots croises."""

import random

import streamlit as st

from crosswords import (DEFAULT_COLUMNS, DEFAULT_ROWS, DEFAULT_WORDLIST,
                        generer_grille)


def reinitialiser_entrees():
    """Efface les valeurs saisies par le joueur dans la session."""
    for key in list(st.session_state.keys()):
        if key.startswith("cell_"):
            del st.session_state[key]
    st.session_state["dernier_score"] = None
    st.session_state["revealed_cells"] = []


def reveler_lettre(solution):
    """Remplit une case aleatoire avec la bonne lettre pour aider le joueur."""
    deja_revelees = set(st.session_state.setdefault("revealed_cells", []))
    candidats = []
    for r, ligne in enumerate(solution):
        for c, case in enumerate(ligne):
            if case == "#" or (r, c) in deja_revelees:
                continue
            candidats.append((r, c))

    if not candidats:
        st.info("Toutes les lettres ont deja ete revelees.")
        return False

    r, c = random.choice(candidats)
    st.session_state["revealed_cells"].append((r, c))
    st.session_state[f"cell_{r}_{c}"] = solution[r][c]
    return True


st.set_page_config(page_title="Jeu de mots croises", layout="wide")
st.title("Jeu de mots croises")
st.caption("Generez une grille puis tentez de la remplir. Cliquez sur \"Verifier\" pour connaitre votre score.")

# Initialisation de l'etat de session.
st.session_state.setdefault("solution", None)
st.session_state.setdefault("status", None)
st.session_state.setdefault("dernier_score", None)
st.session_state.setdefault("indices", {"across": [], "down": []})
st.session_state.setdefault("revealed_cells", [])

st.markdown(
    """
    <style>
    .case-noire {
        align-items: center;
        background-color: #1d2330;
        border-radius: 4px;
        color: #fff;
        display: flex;
        font-weight: bold;
        height: 3rem;
        justify-content: center;
        width: 100%;
    }
    .case-lettre input {
        text-align: center;
        font-size: 1.1rem;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Parametres")
    nb_rows = st.number_input("Nombre de lignes", min_value=3, max_value=12,
                               value=DEFAULT_ROWS, step=1)
    nb_columns = st.number_input("Nombre de colonnes", min_value=3, max_value=12,
                                  value=DEFAULT_COLUMNS, step=1)
    wordlist_path = st.text_input("Fichier de mots", value=DEFAULT_WORDLIST)
    generer = st.button("Generer une nouvelle grille", use_container_width=True)

    if generer:
        try:
            with st.spinner("Resolution en cours..."):
                status, grid, clues = generer_grille(rows=int(nb_rows),
                                                     columns=int(nb_columns),
                                                     wordlist_path=wordlist_path)
        except FileNotFoundError:
            st.session_state["status"] = "FICHIER INTROUVABLE"
            st.session_state["solution"] = None
            st.session_state["indices"] = {"across": [], "down": []}
            st.error("Impossible de lire le fichier de mots indique.")
        else:
            st.session_state["status"] = status
            if status == "OPTIMAL" and grid:
                st.session_state["solution"] = grid
                st.session_state["rows"] = int(nb_rows)
                st.session_state["columns"] = int(nb_columns)
                st.session_state["indices"] = clues
                reinitialiser_entrees()
                st.success("Nouvelle grille generee !")
            else:
                st.session_state["solution"] = None
                st.session_state["indices"] = {"across": [], "down": []}
                st.warning("La resolution n'a pas abouti avec ces parametres.")

status = st.session_state.get("status")
if status:
    st.info(f"Statut du solveur : {status}")

solution = st.session_state.get("solution")
if not solution:
    st.write("Utilisez la barre laterale pour generer une grille puis commencez a jouer !")
    st.stop()

nb_lignes = len(solution)
nb_colonnes = len(solution[0]) if solution else 0
nb_lettres = sum(1 for ligne in solution for case in ligne if case != "#")

st.subheader("Remplissez la grille")
st.caption(f"{nb_lettres} lettres a trouver")
hints_restants = max(0, nb_lettres - len(st.session_state["revealed_cells"]))
st.caption(f"{hints_restants} lettres encore revelables")

col_effacer, col_hint = st.columns(2)
with col_effacer:
    if st.button("Effacer mes reponses"):
        reinitialiser_entrees()
        st.rerun()
with col_hint:
    disabled = hints_restants == 0
    if st.button("Reveler une lettre", disabled=disabled):
        if reveler_lettre(solution):
            st.rerun()
    aide = "Plus aucune lettre a reveler." if disabled else "Besoin d'aide ? Cliquez pour remplir une lettre correcte."
    st.caption(aide)

with st.form("grille_form"):
    for r, ligne in enumerate(solution):
        colonnes = st.columns(nb_colonnes)
        for c, case in enumerate(ligne):
            cle = f"cell_{r}_{c}"
            if case == "#":
                colonnes[c].markdown("<div class='case-noire'>&nbsp;</div>", unsafe_allow_html=True)
            else:
                colonnes[c].text_input(
                    label=f"Case {r+1}-{c+1}",
                    value=st.session_state.get(cle, ""),
                    max_chars=1,
                    key=cle,
                    label_visibility="hidden",
                )
    verif = st.form_submit_button("Verifier mes reponses")

if verif:
    total = 0
    correct = 0
    for r, ligne in enumerate(solution):
        for c, case in enumerate(ligne):
            if case == "#":
                continue
            total += 1
            valeur = st.session_state.get(f"cell_{r}_{c}", "").strip().upper()
            if valeur == case:
                correct += 1
    st.session_state["dernier_score"] = (correct, total)

if st.session_state.get("dernier_score"):
    correct, total = st.session_state["dernier_score"]
    pourcentage = int((correct / total) * 100) if total else 0
    st.success(f"Score actuel : {correct}/{total} lettres correctes ({pourcentage}%).")
    st.subheader("Solution apres verification")
    st.caption("Voici la grille complete pour vous corriger.")
    for ligne in solution:
        st.write(" ".join(ligne))
else:
    with st.expander("Besoin d'un indice ? Afficher la solution"):
        for ligne in solution:
            st.write(" ".join(ligne))

st.subheader("Indices")
col_h, col_v = st.columns(2)
with col_h:
    st.markdown("**Horizontaux**")
    if st.session_state["indices"]["across"]:
        for indice in st.session_state["indices"]["across"]:
            st.write(f"{indice['numero']}. ({indice['longueur']} lettres) {indice['indice']}")
    else:
        st.write("Aucun indice disponible.")
with col_v:
    st.markdown("**Verticaux**")
    if st.session_state["indices"]["down"]:
        for indice in st.session_state["indices"]["down"]:
            st.write(f"{indice['numero']}. ({indice['longueur']} lettres) {indice['indice']}")
    else:
        st.write("Aucun indice disponible.")
