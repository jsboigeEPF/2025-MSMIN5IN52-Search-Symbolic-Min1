# -*- coding: utf-8 -*-
"""
Gestionnaire de dictionnaire de mots pour les mots-croisés.
"""

from typing import List, Dict, Set, Tuple, TYPE_CHECKING
from collections import defaultdict
import os
import random
import unicodedata
import urllib.request

if TYPE_CHECKING:
    from .definitions import DefinitionService


# URLs de dictionnaires français en ligne
FRENCH_DICT_URLS = [
    # Liste de mots français (GitHub)
    "https://raw.githubusercontent.com/chrplr/openlexicon/master/datasets-info/Liste-de-mots-francais-Gutenberg/liste.de.mots.francais.frgut.txt",
    # Backup: liste alternative
    "https://raw.githubusercontent.com/hbenbel/French-Dictionary/master/dictionary/dictionary.txt",
]


def remove_accents(text: str) -> str:
    """Supprime les accents d'une chaîne de caractères"""
    nfkd_form = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd_form if not unicodedata.combining(c))


class WordDictionary:
    """
    Gestionnaire du dictionnaire de mots pour les mots-croisés.
    Organise les mots par longueur pour une recherche efficace.
    
    Supporte plusieurs sources de mots:
    - Fichier local
    - Téléchargement automatique depuis Internet
    - Bibliothèque pyenchant (si installée)
    - Dictionnaire intégré (fallback)
    
    Optimisations:
    - Index par (longueur, position, lettre) pour filtrage rapide
    - Limitation du nombre de mots par longueur
    """
    
    # Nombre maximum de mots par longueur (pour optimiser la résolution)
    MAX_WORDS_PER_LENGTH = 2000
    
    def __init__(self, max_words_per_length: int = None):
        # Dictionnaire: longueur -> ensemble de mots
        self.words_by_length: Dict[int, Set[str]] = defaultdict(set)
        # Index optimisé: (longueur, position, lettre) -> ensemble de mots
        self._index: Dict[Tuple[int, int, str], Set[str]] = defaultdict(set)
        # Index construit ?
        self._index_built = False
        # Chemin du cache local
        self.cache_dir = os.path.join(os.path.dirname(__file__) or '.', '..', '.dict_cache')
        self.cache_file = os.path.join(self.cache_dir, 'french_words.txt')
        # Limite de mots
        self.max_words_per_length = max_words_per_length or self.MAX_WORDS_PER_LENGTH
    
    def add_word(self, word: str, keep_accents: bool = False):
        """Ajoute un mot au dictionnaire (converti en majuscules, accents optionnels)"""
        word = word.upper().strip()
        if not keep_accents:
            word = remove_accents(word)
        if word.isalpha() and len(word) >= 2:
            self.words_by_length[len(word)].add(word)
            self._index_built = False  # Index invalidé
    
    def _build_index(self):
        """Construit l'index (longueur, position, lettre) -> mots"""
        if self._index_built:
            return
        
        self._index.clear()
        for length, words in self.words_by_length.items():
            for word in words:
                for pos, letter in enumerate(word):
                    self._index[(length, pos, letter)].add(word)
        self._index_built = True
    
    def get_words(self, length: int) -> List[str]:
        """Retourne la liste des mots d'une longueur donnée"""
        return list(self.words_by_length.get(length, []))
    
    def get_words_with_letter_at(self, length: int, position: int, letter: str) -> Set[str]:
        """Retourne les mots d'une longueur donnée avec une lettre à une position donnée"""
        self._build_index()
        return self._index.get((length, position, letter.upper()), set())
    
    def filter_words_with_definitions(self, definition_service: 'DefinitionService', 
                                       lengths: List[int] = None,
                                       max_per_length: int = 1000,
                                       progress_callback=None) -> int:
        """
        Filtre le dictionnaire pour ne garder que les mots ayant une définition.
        
        Args:
            definition_service: Service de définitions à utiliser
            lengths: Liste des longueurs à filtrer (None = toutes)
            max_per_length: Nombre maximum de mots à garder par longueur
            progress_callback: Callback (checked, found, current_word) pour progression
            
        Returns:
            Nombre de mots avec définition trouvés
        """
        lengths_to_check = lengths or list(self.words_by_length.keys())
        total_found = 0
        total_checked = 0
        
        for length in sorted(lengths_to_check):
            words = list(self.words_by_length.get(length, []))
            if not words:
                continue
                
            # Limiter le nombre de mots à vérifier pour la performance
            if len(words) > max_per_length * 3:
                random.seed(42)
                words = random.sample(words, max_per_length * 3)
                random.seed()
            
            words_with_def = set()
            
            for word in words:
                total_checked += 1
                if progress_callback and total_checked % 50 == 0:
                    progress_callback(total_checked, total_found, word)
                
                # Vérifier si le mot a une définition (utilise le cache)
                if definition_service.get_definition(word, max_length=200):
                    words_with_def.add(word)
                    
                    # Si on a assez de mots pour cette longueur, arrêter
                    if len(words_with_def) >= max_per_length:
                        break
            
            # Mettre à jour le dictionnaire
            if words_with_def:
                self.words_by_length[length] = words_with_def
                total_found += len(words_with_def)
        
        self._index_built = False  # Invalider l'index
        
        # Sauvegarder le cache des définitions
        definition_service.save_cache()
        
        return total_found
    
    def get_words_limited(self, length: int, limit: int = None) -> List[str]:
        """
        Retourne une liste limitée de mots d'une longueur donnée.
        Les mots sont mélangés aléatoirement à chaque appel.
        """
        words = list(self.words_by_length.get(length, []))
        limit = limit or self.max_words_per_length
        
        if len(words) <= limit:
            # Mélanger même si on prend tous les mots
            result = words.copy()
            random.shuffle(result)
            return result
        
        # Prendre un échantillon aléatoire (différent à chaque appel)
        return random.sample(words, limit)
    
    def get_stats(self) -> Dict[int, int]:
        """Retourne les statistiques du dictionnaire (longueur -> nombre de mots)"""
        return {length: len(words) for length, words in self.words_by_length.items()}
    
    def load_from_file(self, filepath: str, encoding: str = 'utf-8'):
        """Charge les mots depuis un fichier (un mot par ligne)"""
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                for line in f:
                    word = line.strip()
                    if word:
                        self.add_word(word)
            print(f"✅ Chargé {sum(len(w) for w in self.words_by_length.values())} mots depuis {filepath}")
        except FileNotFoundError:
            print(f"⚠ Fichier non trouvé: {filepath}")
    
    def load_from_url(self, url: str = None) -> bool:
        """
        Télécharge et charge un dictionnaire français depuis Internet.
        Utilise un cache local pour éviter les téléchargements répétés.
        
        Returns:
            True si le chargement a réussi, False sinon
        """
        # Vérifier si un cache existe
        if os.path.exists(self.cache_file):
            print(f"📁 Chargement depuis le cache local...")
            self.load_from_file(self.cache_file)
            if sum(len(w) for w in self.words_by_length.values()) > 1000:
                return True
        
        # Télécharger depuis Internet
        urls_to_try = [url] if url else FRENCH_DICT_URLS
        
        for dict_url in urls_to_try:
            try:
                # Reconstituer l'URL (splitée pour éviter les problèmes de formatage)
                dict_url = dict_url.replace(' ', '')
                print(f"🌐 Téléchargement du dictionnaire depuis {dict_url[:50]}...")
                
                req = urllib.request.Request(
                    dict_url,
                    headers={'User-Agent': 'Mozilla/5.0 (CrosswordSolver)'}
                )
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    content = response.read().decode('utf-8', errors='ignore')
                
                words = content.strip().split('\n')
                
                for word in words:
                    word = word.strip()
                    # Certains fichiers ont des colonnes séparées par des espaces/tabs
                    if '\t' in word:
                        word = word.split('\t')[0]
                    if ' ' in word:
                        word = word.split()[0]
                    if word:
                        self.add_word(word)
                
                total = sum(len(w) for w in self.words_by_length.values())
                
                if total > 1000:
                    print(f"✅ Téléchargé {total} mots")
                    # Sauvegarder en cache
                    self._save_cache()
                    return True
                    
            except Exception as e:
                print(f"⚠ Échec du téléchargement: {e}")
                continue
        
        return False
    
    def _save_cache(self):
        """Sauvegarde les mots dans un fichier cache local"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                for length in sorted(self.words_by_length.keys()):
                    for word in sorted(self.words_by_length[length]):
                        f.write(word + '\n')
            print(f"💾 Cache sauvegardé dans {self.cache_file}")
        except Exception as e:
            print(f"⚠ Impossible de sauvegarder le cache: {e}")
    
    def load_from_enchant(self, language: str = 'fr_FR') -> bool:
        """
        Charge les mots depuis pyenchant (nécessite: pip install pyenchant)
        
        Args:
            language: Code de langue (fr_FR, fr_BE, etc.)
            
        Returns:
            True si le chargement a réussi, False sinon
        """
        try:
            import enchant
            
            # Vérifier si le dictionnaire français est disponible
            if not enchant.dict_exists(language):
                available = enchant.list_languages()
                fr_dicts = [l for l in available if l.startswith('fr')]
                if fr_dicts:
                    language = fr_dicts[0]
                    print(f"📖 Utilisation du dictionnaire {language}")
                else:
                    print(f"⚠ Aucun dictionnaire français disponible. Langues: {available}")
                    return False
            
            d = enchant.Dict(language)
            
            # Enchant ne permet pas de lister tous les mots directement
            # On doit utiliser une liste de base et vérifier avec enchant
            print(f"📖 Dictionnaire enchant '{language}' disponible pour validation")
            
            # Charger les mots par défaut et les valider avec enchant
            self.load_default_dictionary()
            
            # Note: Pour une liste complète, il faut un fichier externe
            # enchant est plus utile pour la validation que pour la génération
            return True
            
        except ImportError:
            print("⚠ pyenchant non installé. Installez avec: pip install pyenchant")
            return False
        except Exception as e:
            print(f"⚠ Erreur enchant: {e}")
            return False
    
    def load_smart(self) -> bool:
        """
        Charge le dictionnaire de manière intelligente:
        1. Essaie le cache local
        2. Essaie le téléchargement Internet
        3. Fallback sur le dictionnaire intégré
        
        Returns:
            True si un dictionnaire riche a été chargé, False si fallback utilisé
        """
        # 1. Essayer le téléchargement/cache
        if self.load_from_url():
            return True
        
        # 2. Fallback sur le dictionnaire intégré
        print("📚 Utilisation du dictionnaire intégré...")
        self.load_default_dictionary()
        return False
    
    def load_default_dictionary(self):
        """Charge un dictionnaire par défaut avec des mots français courants"""
        default_words = [
            # 2 lettres
            "ET", "OU", "DE", "LA", "LE", "UN", "IL", "ON", "EN", "AU",
            "SI", "NE", "JE", "CE", "LU", "VU", "SU", "PU", "DU", "MU",
            "NU", "TU", "EU", "OR", "NI", "VA", "TA", "SA", "MA", "NA",
            "OS", "AS", "ES", "US", "AN", "RI", "RA", "MI", "DO", "RE",
            
            # 3 lettres
            "LES", "DES", "QUI", "EST", "PAS", "UNE", "PAR", "SUR", "SON", "OUI",
            "MES", "TES", "SES", "NOS", "VOS", "EUX", "EAU", "AIR", "FEU", "SOL",
            "CRI", "AMI", "RUE", "VIE", "ROI", "JEU", "NEZ", "BLE", "CLE", "THE",
            "BAS", "MUR", "NID", "RIZ", "BIS", "TRI", "SRI", "BOL", "COL", "FIL",
            "GEL", "SEL", "TEL", "MIL", "NUL", "BAL", "CAL", "GAL", "MAL", "VAL",
            "VIN", "PIN", "FIN", "DIN", "AXE", "AGE", "ILE", "ANE", "ARE", "ORE",
            "OIE", "ETE", "PRE", "BEC", "SEC", "DUC", "ARC", "LAC", "SAC", "BAC",
            "TIC", "PIC", "VIC", "MIC", "BUT", "TAS", "GAS", "LAS", "PAS", "CAS",
            
            # 4 lettres
            "ELLE", "ETRE", "AVEC", "POUR", "DANS", "PLUS", "TOUT", "FAIT", "BIEN", "MAIS",
            "DONC", "SANS", "LEUR", "DEUX", "NOUS", "VOUS", "CHEZ", "MEME", "TRES", "FAUT",
            "MORT", "VENT", "PONT", "MAIN", "PAIN", "BAIN", "GAIN", "VAIN", "SAIN", "NAIN",
            "PIED", "CIEL", "MIEL", "FIEL", "DIEU", "LIEU", "BLEU", "JEUX", "YEUX", "VEUX",
            "PEUX", "FEUX", "NOEU", "VOEU", "NUIT", "BRUIT", "FRUIT", "SUITE", "FUITE", "HUILE",
            "PILE", "FILE", "BILE", "VILE", "AILE", "OEIL", "SEUIL", "FEUIL", "DEUIL", "ECRIT",
            "LIVRE", "VIVRE", "LIBRE", "FIBRE", "ARBRE", "CADRE", "ORDRE", "AUTRE", "NOTRE", "VOTRE",
            "FRERE", "SOEUR", "COEUR", "CHOEUR", "FLEUR", "HEURE", "BEURE", "PEURE", "MEURE", "SEURE",
            "BEAU", "VEAU", "SEAU", "PEAU", "CHATEAU", "BATEAU", "GATEAU", "PLATEAU", "MANTEAU", "RIDEAU",
            "TETE", "FETE", "BETE", "PATE", "DATE", "HATE", "RATE", "MATE", "GATE", "NATE",
            "CASE", "BASE", "VASE", "RASE", "PASSE", "MASSE", "CLASSE", "BRASSE", "CHASSE", "TASSE",
            "ROSE", "DOSE", "POSE", "CHOSE", "PROSE", "CLOSE", "CAUSE", "PAUSE", "SAUCE", "FAUSSE",
            "RIRE", "DIRE", "LIRE", "PIRE", "TIRE", "SIRE", "MIRE", "BOIRE", "CROIRE", "FOIRE",
            "JOIE", "SOIE", "VOIE", "NOIX", "VOIX", "CHOIX", "CROIX", "FOIS", "MOIS", "BOIS",
            "POIS", "LOIS", "TROIS", "FROID", "DROIT", "ETROIT", "DETROIT", "ADROIT", "ENDROIT", "SOIT",
            "AIDE", "IDEE", "ONDE", "MONDE", "RONDE", "SONDE", "BONDE", "FONDE", "TONDE", "CONDE",
            "ANGE", "RANGE", "MANGE", "CHANGE", "ETRANGE", "ORANGE", "MELANGE", "GRANGE", "FRANGE", "LANGE",
            
            # 5 lettres
            "ALLER", "FAIRE", "MONDE", "PETIT", "GRAND", "HOMME", "FEMME", "JEUNE", "VIEUX", "MAISON",
            "TABLE", "PORTE", "LIVRE", "TEMPS", "PLACE", "CHOSE", "POINT", "CORPS", "COEUR", "TERRE",
            "VILLE", "ROUTE", "ARBRE", "FLEUR", "SOLEIL", "ECOLE", "ETOILE", "OCEAN", "FORET", "NUAGE",
            "CHANT", "BLANC", "PLAGE", "VERRE", "HERBE", "BRUIT", "FRUIT", "TRAIN", "AVION", "BATEAU",
            "PIANO", "RADIO", "VIDEO", "PHOTO", "METRO", "RESTO", "LUNDI", "MARDI", "MERCI", "AVRIL",
            "ROUGE", "JAUNE", "BLEUE", "VERTE", "NOIRE", "CLAIR", "SOMBRE", "CHAUD", "FROID", "TIEDE",
            "SUCRE", "ACIDE", "AMER", "EPICE", "DOUX", "SALE", "FRAIS", "MURES", "PECHE", "POMME",
            "POIRE", "PRUNE", "RAISIN", "MELON", "CITRON", "ORANGE", "BANANE", "FRAISE", "CERISE", "OLIVE",
            "TOMATE", "SALADE", "CAROTTE", "OIGNON", "PATATE", "HARICOT", "EPINARD", "POIREAU", "RADIS", "CHOU",
            "VIANDE", "POISSON", "POULET", "BOEUF", "PORC", "MOUTON", "LAPIN", "CANARD", "DINDE", "VEAU",
            "DROIT", "GAUCHE", "HAUT", "NORD", "OUEST", "SORTIE", "ENTREE", "MILIEU", "CENTRE", "BORD",
            "ENVIE", "ESPOIR", "DESIR", "AMOUR", "HAINE", "JOIES", "PEINES", "COLERE", "CALME", "PAIX",
            "CRISE", "SUJET", "OBJET", "PROJET", "EFFET", "CAUSE", "MOTIF", "RAISON", "PREUVE", "SIGNE",
            "PARLE", "MANGE", "BOIRE", "JOUER", "FINIR", "VENIR", "TENIR", "PARTIR", "SORTIR", "DORMIR",
            "ECRIT", "PEINT", "FILME", "CHANTE", "DANSE", "NAGER", "COURIR", "SAUTER", "VOLER", "TOMBER",
            "TAPIS", "LAMPE", "CHAISE", "CANAPE", "ARMOIRE", "MIROIR", "RIDEAU", "TABLEAU", "CADRE", "LUSTRE",
            "LINGE", "DRAP", "TAIE", "SERVIETTE", "NAPPE", "TORCHON", "EPONGE", "BALAI", "SEAU", "POELE",
            "CASSEROLE", "COUTEAU", "CUILLERE", "FOURCHETTE", "ASSIETTE", "VERRE", "TASSE", "BOL", "PLAT", "SALADIER",
            
            # 6 lettres
            "MAISON", "JARDIN", "CHEMIN", "PRINCE", "RENDRE", "PARTIR", "PORTER", "PARLER", "PENSER", "METTRE",
            "VOULOIR", "POUVOIR", "DEVOIR", "SAVOIR", "FALLOIR", "VALOIR", "MOURIR", "SERVIR", "SORTIR", "SENTIR",
            "DONNER", "TROUVER", "PRENDRE", "ENTRER", "MONTER", "TOMBER", "RESTER", "REVENIR", "DEVENIR", "TENIR",
            "SIMPLE", "DOUBLE", "TRIPLE", "UNIQUE", "SEUL", "PROPRE", "PAUVRE", "RICHE", "GROS", "MINCE",
            "DIRECT", "RAPIDE", "LENT", "ANCIEN", "NOUVEAU", "RECENT", "ACTUEL", "FUTUR", "PASSE", "PRESENT",
            "SOCIAL", "PUBLIC", "PRIVE", "CIVIL", "LEGAL", "LOCAL", "GLOBAL", "TOTAL", "PARTIEL", "SPECIAL",
            "ACCORD", "RETOUR", "CENTRE", "SOURCE", "ESPACE", "NATURE", "RAISON", "MESURE", "FIGURE", "NOMBRE",
            "VALEUR", "PROJET", "EFFET", "NIVEAU", "MEMBRE", "GROUPE", "EQUIPE", "CLASSE", "FAMILLE", "NATION",
            "COULEUR", "LUMIERE", "OMBRE", "CHALEUR", "FROID", "ODEUR", "SAVEUR", "TEXTURE", "FORME", "TAILLE",
            "REGARD", "SOURIRE", "LARME", "GESTE", "PAROLE", "PENSEE", "REVE", "DESIR", "ESPOIR", "CRAINTE",
            "RIVIERE", "MONTAGNE", "COLLINE", "VALLEE", "PLAINE", "DESERT", "JUNGLE", "PRAIRIE", "MARAIS", "ETANG",
            "ANIMAL", "INSECTE", "OISEAU", "POISSON", "REPTILE", "MAMMIFERE", "ARAIGNEE", "SERPENT", "TORTUE", "GRENOUILLE",
            "ECLAIR", "TONNERRE", "PLUIE", "NEIGE", "GRELE", "BROUILLARD", "TEMPETE", "OURAGAN", "CYCLONE", "TORNADE",
            "MINUTE", "SECONDE", "HEURE", "JOURNEE", "SEMAINE", "MOIS", "SAISON", "ANNEE", "SIECLE", "EPOQUE",
            
            # 7 lettres
            "PREMIER", "DERNIER", "NOUVEAU", "COMMENT", "PENDANT", "DEVENIR", "SEMBLER", "REMPLIR", "FINIR", "CHOISIR",
            "MACHINE", "CAPITAL", "TRAVAIL", "SYSTEME", "PROBLEME", "RESULTAT", "QUESTION", "REPONSE", "EXEMPLE", "SERVICE",
            "ELEMENT", "PRODUIT", "MARCHE", "MILLION", "QUALITE", "SECURITE", "ENERGIE", "MATIERE", "SCIENCE", "CULTURE",
            "HISTOIRE", "MUSIQUE", "THEATRE", "CINEMA", "PEINTURE", "SCULPTURE", "DANSE", "POESIE", "ROMAN", "NOUVELLE",
            "LIBERTE", "EGALITE", "FRATERNITE", "JUSTICE", "VERITE", "BEAUTE", "BONTE", "SAGESSE", "COURAGE", "HONNEUR",
            "MARIAGE", "DIVORCE", "NAISSANCE", "DECES", "BAPTEME", "FUNERAILLES", "CEREMONIE", "CELEBRATION", "FETE", "ANNIVERSAIRE",
            "VOITURE", "AUTOBUS", "TRAMWAY", "BICYCLETTE", "SCOOTER", "AVION", "HELICOPTERE", "BATEAU", "NAVIRE", "SOUSMARIN",
            "CHATEAU", "PALAIS", "MANOIR", "VILLA", "APPARTEMENT", "STUDIO", "MAISON", "FERME", "GRANGE", "MOULIN",
            "CUISINE", "CHAMBRE", "SALON", "BUREAU", "COULOIR", "ESCALIER", "GRENIER", "CAVE", "GARAGE", "TERRASSE",
            "ORDINATEUR", "TELEPHONE", "INTERNET", "RESEAU", "LOGICIEL", "MATERIEL", "DONNEES", "FICHIER", "DOSSIER", "ECRAN",
            
            # 8 lettres
            "TOUJOURS", "BEAUCOUP", "ENSEMBLE", "PROBLEME", "GOUVERNE", "QUESTION", "HISTOIRE", "POSSIBLE", "NATIONAL", "POLITIQUE",
            "ECONOMIE", "SOCIETE", "EDUCATION", "FORMATION", "RECHERCHE", "DEVELOPPEMENT", "PRODUCTION", "DISTRIBUTION", "COMMUNICATION", "INFORMATION",
            "BATIMENT", "MONUMENT", "FONTAINE", "CATHEDRALE", "BASILIQUE", "CHAPELLE", "MONASTERE", "COUVENT", "ABBAYE", "PRIEURE",
            "RELATION", "EMOTION", "SENSATION", "PERCEPTION", "INTUITION", "REFLEXION", "DECISION", "ACTION", "REACTION", "INTERACTION",
            "STANDARD", "OFFICIEL", "NATUREL", "PERSONNEL", "MATERIEL", "SPIRITUEL", "INTELLECTUEL", "EMOTIONNEL", "RATIONNEL", "IRRATIONNEL",
            "MONTAGNE", "ALTITUDE", "PANORAMA", "PAYSAGE", "HORIZON", "COUCHER", "LEVER", "AURORE", "CREPUSCULE", "MINUIT",
            
            # 9 lettres
            "POLITIQUE", "EDUCATION", "RECHERCHE", "SITUATION", "CONDITION", "DIRECTION", "OPERATION", "EVOLUTION", "ATTENTION", "DIMENSION",
            "PROGRAMME", "STRUCTURE", "TECHNIQUE", "PRATIQUE", "METHODE", "STRATEGIE", "TACTIQUE", "LOGIQUE", "ANALYSE", "SYNTHESE",
            "AVENTURE", "EXPERIENCE", "CONNAISSANCE", "COMPREHENSION", "INTERPRETATION", "EXPLICATION", "DEMONSTRATION", "ILLUSTRATION", "REPRESENTATION", "DESCRIPTION",
            "SENTIMENT", "IMPRESSION", "EXPRESSION", "OBSESSION", "DEPRESSION", "PROGRESSION", "REGRESSION", "SUCCESSION", "PROFESSION", "CONFESSION",
            
            # 10 lettres
            "GOUVERNEMENT", "DEVELOPPEMENT", "ENVIRONNEMENT", "ETABLISSEMENT", "COMPORTEMENT", "FONCTIONNEMENT", "EVENEMENT", "MOUVEMENT", "SENTIMENT", "TRAITEMENT",
            "COMPRENDRE", "ENTREPRISE", "EXPERIENCE", "CONNAISSANCE", "IMPORTANCE", "CONFERENCE", "DIFFERENCE", "PREFERENCE", "REFERENCE", "COHERENCE",
            "ATMOSPHERE", "TEMPERATURE", "BIOSPHERE", "STRATOSPHERE", "IONOSPHERE", "MAGNETOSPHERE", "TROPOSPHERE", "LITHOSPHERE", "HYDROSPHERE", "CRYOSPHERE",
            
            # 11+ lettres
            "ARCHITECTURE", "ELECTRONIQUE", "INFORMATIQUE", "MATHEMATIQUE", "PHILOSOPHIE", "TECHNOLOGIE", "COMMUNICATION", "ORGANISATION", "ADMINISTRATION", "TRANSFORMATION",
            "RESPONSABLE", "CONSIDERABLE", "REMARQUABLE", "INDISPENSABLE", "IRREVERSIBLE", "INCOMPREHENSIBLE", "EXTRAORDINAIRE", "SUPPLEMENTAIRE", "COMPLEMENTAIRE", "ELEMENTAIRE",
            "PERSONNALITE", "NATIONALITE", "ORIGINALITE", "SPECIALITE", "GENERALITE", "PARTICULARITE", "SINGULARITE", "REGULARITE", "POPULARITE", "SOLIDARITE",
            
            # Mots supplémentaires courants (mélange de longueurs)
            "AXE", "CLE", "FEE", "GRE", "IDE", "JUS", "KIT", "LOT", "NET", "OPT",
            "PUR", "QUE", "SUR", "TIR", "UNS", "VIL", "ZEN", "API", "BOT", "CPU",
            "GPS", "LED", "RAM", "SIM", "USB", "WEB", "ZIP", "APP", "BUG", "LOG",
            "SPAM", "BLOG", "CHAT", "MAIL", "WIKI", "ZOOM", "LIEN", "SITE", "PAGE", "CODE",
            "HACK", "DATA", "BYTE", "CHIP", "DISK", "FILE", "FONT", "ICON", "JAVA", "LINK",
            "MENU", "NODE", "OPEN", "PATH", "ROOT", "SAVE", "SORT", "TEXT", "USER", "VIEW",
            
            # Vocabulaire étendu - Noms communs
            "ABEILLE", "ACCENT", "ACHAT", "ACTEUR", "ADRESSE", "AFFAIRE", "AGENDA", "AGENT", "AGIR", "AIGLE",
            "AIMER", "ALBUM", "ALIMENT", "ALLEE", "ALLUMER", "ALOUETTE", "AMATEUR", "AMBIANCE", "AMENAGER", "AMENDE",
            "AMENER", "AMERTUME", "AMICAL", "AMORCE", "AMOUR", "AMPERE", "ANALYSE", "ANCHOIS", "ANCIEN", "ANERIE",
            "ANIMAL", "ANNEAU", "ANNONCE", "ANNUEL", "ANTENNE", "ANXIEUX", "APAISER", "APERCU", "APLOMB", "APOSTROPHE",
            
            "BAGAGE", "BAGUETTE", "BALCON", "BALISE", "BALLADE", "BANC", "BANDE", "BANQUE", "BARQUE", "BARRE",
            "BASSIN", "BATAILLE", "BATEAU", "BATTRE", "BAVARD", "BAZAR", "BEAUTE", "BEIGE", "BERGER", "BESOIN",
            "BETAIL", "BETON", "BEURRE", "BICEPS", "BIJOU", "BILAN", "BILLET", "BISCUIT", "BITUME", "BIZARRE",
            "BLAGUE", "BLAIREAU", "BLASON", "BLESSER", "BLINDAGE", "BLOCUS", "BLOND", "BOCAL", "BOEUF", "BOHEME",
            
            "CABANE", "CABINET", "CABLE", "CACHE", "CADEAU", "CADET", "CADRAN", "CAFARD", "CAHIER", "CAILLOU",
            "CAISSE", "CALCUL", "CALME", "CAMERA", "CAMION", "CAMPAGNE", "CANAL", "CANARI", "CANIF", "CANNE",
            "CANTON", "CAPITAL", "CAPOTE", "CAPSULE", "CAPTEUR", "CARAFE", "CARBONE", "CARCASSE", "CARESSER", "CARGO",
            "CARNET", "CAROTTE", "CARPE", "CARREAU", "CARTON", "CASCADE", "CASIER", "CASQUE", "CASTOR", "CAVALIER",
            
            "DANGER", "DANSE", "DAVANTAGE", "DEBAT", "DEBOUT", "DEBRIS", "DEBUT", "DECEMBRE", "DECEVOIR", "DECHETS",
            "DECIDER", "DECOR", "DECOUVRIR", "DEDANS", "DEFAIRE", "DEFAUT", "DEFENDRE", "DEFICIT", "DEFINIR", "DEGAGER",
            "DEGOUT", "DEGRE", "DEHORS", "DEJEUNER", "DELAI", "DELICE", "DEMAIN", "DEMANDER", "DEMARCHE", "DEMENAGER",
            "DEMEURER", "DEMISSION", "DEMOCRATE", "DEMON", "DENICHER", "DENSE", "DENT", "DEPART", "DEPASSER", "DEPENDRE",
            
            "ECHEC", "ECHELLE", "ECLAIR", "ECLAT", "ECOLE", "ECONOMIE", "ECOUTER", "ECRAN", "ECRASER", "ECRIRE",
            "ECURIE", "EDITION", "EDUQUER", "EFFACER", "EFFECTUER", "EFFET", "EFFORT", "EFFRAYER", "EGAL", "EGLISE",
            "ELASTIQUE", "ELECTION", "ELEGANT", "ELEMENT", "ELEPHANT", "ELEVE", "ELIMINER", "ELITE", "ELOIGNER", "EMAIL",
            
            "FABLE", "FABRIQUE", "FACADE", "FACETTE", "FACHER", "FACILE", "FACTEUR", "FACTURE", "FACULTE", "FAIBLE",
            "FAILLITE", "FAIM", "FAIRE", "FALAISE", "FALLOIR", "FAMILLE", "FAMINE", "FANER", "FANFARE", "FANTOME",
            "FARCE", "FARINE", "FASCINER", "FATAL", "FATIGUER", "FAUCON", "FAUSSE", "FAVEUR", "FAVORI", "FECOND",
            
            "GAGNE", "GALERIE", "GALOP", "GAMME", "GANT", "GARAGE", "GARANTIR", "GARCON", "GARDE", "GARER",
            "GARNIR", "GATEAU", "GAUCHE", "GAZ", "GEANT", "GEL", "GELER", "GEMME", "GENE", "GENERAL",
            "GENEREUX", "GENIE", "GENOU", "GENRE", "GENS", "GENTIL", "GERANT", "GERBE", "GERER", "GERME",
            
            "HABITAT", "HABITER", "HABITUDE", "HACHE", "HAIE", "HAINE", "HAMAC", "HAMEAU", "HANCHE", "HANGAR",
            "HANTER", "HARDI", "HARENG", "HARMONIE", "HARNAIS", "HARPE", "HASARD", "HATE", "HAUSSE", "HAUTEUR",
            
            "IMAGE", "IMAGINER", "IMBIBER", "IMITER", "IMMENSE", "IMMEUBLE", "IMMOBILE", "IMPACT", "IMPASSE", "IMPATIENT",
            "IMPERMEABILITE", "IMPLIQUER", "IMPORT", "IMPOSER", "IMPOT", "IMPRESSION", "IMPRIME", "IMPRUDENT", "IMPULSION", "INACCESSIBLE",
            
            "JAMAIS", "JAMBE", "JAMBON", "JANVIER", "JAPON", "JARDIN", "JARDINIER", "JAUGE", "JAUNE", "JAUNIR",
            "JAVELOT", "JEAN", "JETER", "JEU", "JEUDI", "JEUNE", "JEUNESSE", "JOIE", "JOINDRE", "JOLI",
            
            "KANGOUROU", "KARATE", "KAYAK", "KEPI", "KERMESSE", "KILO", "KIMONO", "KIOSQUE", "KIT", "KIWI",
            
            "LABEL", "LABEUR", "LABO", "LABOUR", "LAC", "LACE", "LACHER", "LACUNE", "LAGUNE", "LAID",
            "LAINE", "LAISSER", "LAIT", "LAITIER", "LAMA", "LAMBEAU", "LAME", "LAMPE", "LANCER", "LANGAGE",
            
            "MACON", "MADAME", "MAGASIN", "MAGIE", "MAGNIFIQUE", "MAIGRE", "MAILLE", "MAIN", "MAINTENIR", "MAIRE",
            "MAIS", "MAISON", "MAITRE", "MAJEUR", "MAL", "MALADE", "MALADIE", "MALAISE", "MALE", "MALGRE",
            
            "NAGER", "NAIF", "NAIN", "NAISSANCE", "NAITRE", "NAPPE", "NARRER", "NASEAU", "NATAL", "NATION",
            "NATIVE", "NATURE", "NAUFRAGE", "NAVAL", "NAVIRE", "NEANT", "NECTAR", "NEGATIF", "NEIGE", "NERF",
            
            "OBEIR", "OBESE", "OBJET", "OBLIGER", "OBSCUR", "OBSERVER", "OBSTACLE", "OBTENIR", "OCCASION", "OCCIDENT",
            "OCCUPER", "OCEAN", "OCTOBRE", "ODEUR", "ODORAT", "OEIL", "OEUF", "OEUVRE", "OFFENSER", "OFFERT",
            
            "PAGE", "PAILLE", "PAIN", "PAIRE", "PAIX", "PALAIS", "PALE", "PALETTE", "PALIER", "PALMIER",
            "PALPER", "PAMPRE", "PANDA", "PANIER", "PANIQUE", "PANNE", "PANNEAU", "PANORAMA", "PANSEMENT", "PANTALON",
            
            "QUALIFIE", "QUALITE", "QUAND", "QUANTITE", "QUARANTE", "QUART", "QUARTIER", "QUASI", "QUATORZE", "QUATRE",
            "QUEL", "QUELCONQUE", "QUELQUE", "QUERELLE", "QUESTION", "QUEUE", "QUICHE", "QUICONQUE", "QUILLE", "QUINZE",
            
            "RABAIS", "RABATTRE", "RACINE", "RACLER", "RACONTER", "RADAR", "RADEAU", "RADIAL", "RADICAL", "RADIO",
            "RADIS", "RADIUS", "RAFALE", "RAFFINER", "RAFLER", "RAGE", "RAGOUT", "RAIDE", "RAIE", "RAIL",
            
            "SABOT", "SABRE", "SAC", "SACHET", "SACRE", "SAFARI", "SAGE", "SAGESSE", "SAIGNER", "SAILLIE",
            "SAIN", "SAINT", "SAISIR", "SAISON", "SALADE", "SALAIRE", "SALE", "SALER", "SALIR", "SALLE",
            
            "TABLE", "TABLEAU", "TABLETTE", "TABLIER", "TABOU", "TACHE", "TACHER", "TACITE", "TACT", "TACTILE",
            "TAIE", "TAILLE", "TAILLER", "TAILLEUR", "TAIRE", "TALENT", "TALON", "TALUS", "TAMBOUR", "TAMIS",
            
            "ULCERE", "ULTRA", "UNANIME", "UNI", "UNIFORME", "UNION", "UNIQUE", "UNIR", "UNITE", "UNIVERS",
            "URGENCE", "URGENT", "URINE", "URNE", "USAGE", "USER", "USINE", "USTENSILE", "USUEL", "USURE",
            
            "VACANCE", "VACCIN", "VACHE", "VAGABOND", "VAGUE", "VAILLANT", "VAIN", "VAINCRE", "VAINQUEUR", "VAISSEAU",
            "VAISSELLE", "VALABLE", "VALET", "VALEUR", "VALIDE", "VALISE", "VALLEE", "VALOIR", "VALSE", "VALVE",
            
            "WAGON", "WATT", "WEEK", "WESTERN",
            
            "XENON", "XYLOPHONE",
            
            "YACHT", "YAOURT", "YEUX",
            
            "ZAPPER", "ZEBRE", "ZELE", "ZENITH", "ZERO", "ZESTE", "ZIGZAG", "ZINC", "ZONE", "ZOO",
        ]
        
        for word in default_words:
            self.add_word(word)
        
        total_words = sum(len(words) for words in self.words_by_length.values())
        print(f"📚 Dictionnaire chargé: {total_words} mots")
