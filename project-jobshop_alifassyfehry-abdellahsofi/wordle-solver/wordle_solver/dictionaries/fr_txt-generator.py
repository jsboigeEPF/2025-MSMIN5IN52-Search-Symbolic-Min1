import urllib.request
import os
import unicodedata
import csv
import io

def enlever_accents(texte):
    """Transforme 'Hôtel' en 'Hotel'."""
    nfkd_form = unicodedata.normalize('NFKD', texte)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

# --- Configuration ---
dossier_script = os.path.dirname(os.path.abspath(__file__))
chemin_fichier = os.path.join(dossier_script, "mots_francais_5_lettres.txt")
url = "https://raw.githubusercontent.com/hbenbel/French-Dictionary/master/dictionary/dictionary.csv"

print(f"Téléchargement du fichier CSV depuis : {url}")

try:
    # 1. Téléchargement
    response = urllib.request.urlopen(url)
    # On décode en utf-8
    data = response.read().decode('utf-8')
    
    # 2. Lecture du CSV
    # On utilise io.StringIO pour traiter la chaîne de caractères comme un fichier
    csv_file = io.StringIO(data)
    reader = csv.reader(csv_file)
    
    mots_retenus = set()
    
    print("Traitement en cours...")
    
    # On parcourt chaque ligne du CSV
    for row in reader:
        # La première colonne (index 0) contient le mot
        if not row: continue # Sécurité pour les lignes vides
        
        mot_original = row[0]
        
        # On saute l'en-tête s'il y en a un (ex: "Mot")
        if mot_original.lower() == "mot":
            continue
            
        # On saute les mots composés
        if '-' in mot_original or ' ' in mot_original:
            continue
            
        # Nettoyage : accents -> sans accents, tout en majuscules
        mot_propre = enlever_accents(mot_original).upper()
        
        # Filtre : 5 lettres et uniquement des lettres
        if len(mot_propre) == 5 and mot_propre.isalpha():
            mots_retenus.add(mot_propre)
            
    # 3. Écriture du résultat
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        for mot in sorted(mots_retenus):
            f.write(mot + "\n")
            
    print(f"Terminé ! {len(mots_retenus)} mots ont été sauvegardés dans :")
    print(chemin_fichier)

except Exception as e:
    print(f"Une erreur est survenue : {e}")