# -*- coding: utf-8 -*-
"""
Service de définitions pour les mots-croisés.
Utilise Wiktionnaire et Dicolink pour récupérer les définitions.
"""

from typing import List, Dict, Optional
import os
import json
import re
import time
import urllib.request
import urllib.parse


class DefinitionService:
    """
    Service pour récupérer les définitions de mots français.
    
    Utilise plusieurs sources:
    - Wiktionnaire français (API MediaWiki) - gratuit, illimité
    - Dicolink API - gratuit avec limite
    - Cache local pour éviter les requêtes répétées
    
    Exemple d'utilisation:
        service = DefinitionService()
        definition = service.get_definition("MAISON")
        # -> "Bâtiment servant d'habitation aux personnes"
    """
    
    # URLs des APIs
    WIKTIONARY_API = "https://fr.wiktionary.org/api/rest_v1/page/definition/{word}"
    WIKTIONARY_PARSE_API = "https://fr.wiktionary.org/w/api.php"
    DICOLINK_API = "https://api.dicolink.com/v1/mot/{word}/definitions"
    
    def __init__(self, cache_definitions: bool = True):
        """
        Initialise le service de définitions.
        
        Args:
            cache_definitions: Si True, met en cache les définitions récupérées
        """
        self.cache: Dict[str, List[str]] = {}
        self.cache_enabled = cache_definitions
        self.cache_dir = os.path.join(os.path.dirname(__file__) or '.', '..', '.dict_cache')
        self.definitions_cache_file = os.path.join(self.cache_dir, 'definitions_cache.json')
        self._load_cache()
    
    def _load_cache(self):
        """Charge le cache des définitions depuis le fichier"""
        if self.cache_enabled and os.path.exists(self.definitions_cache_file):
            try:
                with open(self.definitions_cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}
    
    def _save_cache(self):
        """Sauvegarde le cache des définitions dans un fichier"""
        if self.cache_enabled:
            try:
                os.makedirs(self.cache_dir, exist_ok=True)
                with open(self.definitions_cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.cache, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
    
    def get_definition(self, word: str, max_length: int = 100) -> Optional[str]:
        """
        Récupère la première définition d'un mot.
        
        Args:
            word: Le mot à définir
            max_length: Longueur maximale de la définition (pour l'affichage)
            
        Returns:
            La définition du mot ou None si non trouvée
        """
        definitions = self.get_definitions(word)
        if definitions:
            definition = definitions[0]
            if len(definition) > max_length:
                definition = definition[:max_length-3] + "..."
            return definition
        return None
    
    def _generate_accent_variants(self, word: str) -> List[str]:
        """
        Génère des variantes d'un mot avec différents accents.
        Utile car le dictionnaire stocke les mots sans accents mais
        le Wiktionnaire nécessite les accents pour trouver les définitions.
        """
        word_lower = word.lower()
        variants = [word_lower]
        
        # Générer les variantes les plus courantes (pas toutes les combinaisons)
        # On se concentre sur les patterns fréquents en français
        common_patterns = [
            ('e', 'é'), ('e', 'è'), ('e', 'ê'),
            ('a', 'à'), ('a', 'â'),
            ('u', 'ù'), ('u', 'û'),
            ('i', 'î'),
            ('o', 'ô'),
            ('c', 'ç'),
        ]
        
        for old, new in common_patterns:
            if old in word_lower:
                # Remplacer la première occurrence
                variant = word_lower.replace(old, new, 1)
                if variant not in variants:
                    variants.append(variant)
                
                # Remplacer la dernière occurrence
                idx = word_lower.rfind(old)
                if idx != -1:
                    variant = word_lower[:idx] + new + word_lower[idx+1:]
                    if variant not in variants:
                        variants.append(variant)
        
        # Patterns spécifiques très courants
        specific_replacements = {
            'ee': 'ée', 'er': 'ér', 'es': 'és', 'et': 'ét',
            'ere': 'ère', 'ete': 'ête', 'ege': 'ège',
            'eur': 'eur', 'ier': 'ier',
        }
        
        for pattern, replacement in specific_replacements.items():
            if pattern in word_lower:
                variant = word_lower.replace(pattern, replacement)
                if variant not in variants:
                    variants.append(variant)
        
        return variants[:10]  # Limiter à 10 variantes max
    
    def get_definitions(self, word: str) -> List[str]:
        """
        Récupère toutes les définitions d'un mot.
        
        Args:
            word: Le mot à définir
            
        Returns:
            Liste des définitions trouvées
        """
        word = word.upper().strip()
        word_lower = word.lower()
        
        # Vérifier le cache
        if word in self.cache:
            return self.cache[word]
        
        definitions = []
        
        # Générer les variantes avec accents
        variants = self._generate_accent_variants(word_lower)
        
        for variant in variants:
            # 1. Essayer Wiktionnaire (API REST)
            definitions = self._fetch_wiktionary_rest(variant)
            
            # 2. Si échec, essayer Wiktionnaire (API Parse)
            if not definitions:
                definitions = self._fetch_wiktionary_parse(variant)
            
            # Si on a trouvé des définitions, arrêter
            if definitions:
                break
        
        # 3. Si toujours rien, essayer Dicolink (limité) avec le mot sans accent
        if not definitions:
            definitions = self._fetch_dicolink(word_lower)
        
        # Mettre en cache (même si vide, pour éviter de redemander)
        if self.cache_enabled:
            self.cache[word] = definitions
            # Sauvegarder périodiquement (tous les 50 mots)
            if len(self.cache) % 50 == 0:
                self._save_cache()
        
        return definitions
    
    def _fetch_wiktionary_rest(self, word: str) -> List[str]:
        """Récupère les définitions via l'API REST du Wiktionnaire"""
        try:
            url = self.WIKTIONARY_API.format(word=urllib.parse.quote(word))
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'CrosswordSolver/1.0',
                    'Accept': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            definitions = []
            
            # Parser la réponse du Wiktionnaire
            if 'fr' in data:
                for entry in data['fr']:
                    if 'definitions' in entry:
                        for defn in entry['definitions']:
                            if 'definition' in defn:
                                # Nettoyer le HTML
                                clean_def = self._clean_html(defn['definition'])
                                if clean_def and len(clean_def) > 3:
                                    definitions.append(clean_def)
            
            return definitions[:5]  # Limiter à 5 définitions
            
        except Exception:
            return []
    
    def _fetch_wiktionary_parse(self, word: str) -> List[str]:
        """Récupère les définitions via l'API Parse du Wiktionnaire (wikitext)"""
        try:
            # Utiliser l'API parse pour obtenir le wikitext
            params = {
                'action': 'parse',
                'page': word,
                'prop': 'wikitext',
                'format': 'json'
            }
            
            url = f"{self.WIKTIONARY_PARSE_API}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'CrosswordSolver/1.0'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if 'parse' not in data or 'wikitext' not in data['parse']:
                return []
            
            wikitext = data['parse']['wikitext'].get('*', '')
            
            # Extraire les définitions (lignes commençant par #)
            definitions = []
            in_french_section = False
            
            for line in wikitext.split('\n'):
                # Détecter la section française
                if '{{langue|fr}}' in line or '{{S|nom|fr}}' in line:
                    in_french_section = True
                # Détecter une nouvelle langue (fin de la section française)
                elif '{{langue|' in line and '{{langue|fr}}' not in line:
                    in_french_section = False
                
                # Extraire les définitions (lignes commençant par # mais pas ##)
                if in_french_section and line.startswith('# ') and not line.startswith('##'):
                    # Nettoyer la définition
                    definition = line[2:]  # Enlever "# "
                    definition = self._clean_wikitext(definition)
                    
                    if definition and len(definition) > 5:
                        definitions.append(definition)
                        
                        # Limiter à 5 définitions
                        if len(definitions) >= 5:
                            break
            
            return definitions
            
        except Exception:
            return []
    
    def _clean_wikitext(self, text: str) -> str:
        """Nettoie le wikitext d'une définition"""
        # Supprimer les modèles de type {{exemple|...}}
        text = re.sub(r'\{\{exemple\|[^}]*\}\}', '', text)
        # Supprimer les modèles wiki simples mais garder le contenu utile
        # {{terme|fr}} -> terme
        text = re.sub(r'\{\{([^|}]+)\|[^}]*\}\}', r'\1', text)
        text = re.sub(r'\{\{([^|}]+)\}\}', r'\1', text)
        # Supprimer les liens wiki mais garder le texte: [[mot|texte]] -> texte, [[mot]] -> mot
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        # Supprimer les balises HTML
        text = re.sub(r'<[^>]+>', '', text)
        # Supprimer les références
        text = re.sub(r'\{\{R\|[^}]+\}\}', '', text)
        # Nettoyer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        # Supprimer les crochets restants
        text = re.sub(r'[\[\]]', '', text)
        return text.strip()
    
    def _fetch_dicolink(self, word: str) -> List[str]:
        """Récupère les définitions via l'API Dicolink (limitée)"""
        try:
            url = self.DICOLINK_API.format(word=urllib.parse.quote(word))
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'CrosswordSolver/1.0',
                    'Accept': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            definitions = []
            if isinstance(data, list):
                for item in data[:5]:
                    if 'definition' in item:
                        definitions.append(item['definition'])
            
            return definitions
            
        except Exception:
            return []
    
    def _clean_html(self, text: str) -> str:
        """Nettoie le HTML d'une définition"""
        # Supprimer les balises HTML
        text = re.sub(r'<[^>]+>', '', text)
        # Supprimer les références wiki
        text = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', text)
        # Supprimer les modèles wiki
        text = re.sub(r'\{\{[^}]+\}\}', '', text)
        # Nettoyer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def get_definitions_batch(self, words: List[str], progress_callback=None) -> Dict[str, str]:
        """
        Récupère les définitions pour une liste de mots.
        
        Args:
            words: Liste de mots à définir
            progress_callback: Fonction appelée avec (index, total, word) pour suivre la progression
            
        Returns:
            Dictionnaire {mot: définition}
        """
        results = {}
        total = len(words)
        
        for i, word in enumerate(words):
            if progress_callback:
                progress_callback(i + 1, total, word)
            
            definition = self.get_definition(word)
            if definition:
                results[word] = definition
            
            # Petite pause pour ne pas surcharger les APIs
            if i > 0 and i % 10 == 0:
                time.sleep(0.5)
        
        # Sauvegarder le cache à la fin
        self._save_cache()
        
        return results
    
    def save_cache(self):
        """Force la sauvegarde du cache"""
        self._save_cache()
