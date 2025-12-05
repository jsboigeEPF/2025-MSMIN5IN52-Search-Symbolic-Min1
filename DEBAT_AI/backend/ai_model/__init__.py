# On importe ta fonction d'analyse et on la renomme pour que ce soit plus clair
from .argument_mining import analyze_input as analyze_argument

# On importe ta fonction de calcul logique
from .logic_bridge import solve_debate

# On dit à Python que ce sont les seules fonctions accessibles de l'extérieur
__all__ = ["analyze_argument", "solve_debate"]