import urllib.request

# URL d'une liste de mots complète fiable
url = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"

print("Téléchargement et traitement en cours...")

try:
    response = urllib.request.urlopen(url)
    data = response.read().decode('utf-8')
    
    count = 0
    with open("mots_5_lettres.txt", "w", encoding="utf-8") as f:
        for word in data.splitlines():
            # On garde seulement les mots de 5 lettres
            if len(word.strip()) == 5:
                # On écrit en majuscules
                f.write(word.strip().upper() + "\n")
                count += 1
                
    print(f"Terminé ! Le fichier 'mots_5_lettres.txt' a été créé avec {count} mots.")

except Exception as e:
    print(f"Une erreur est survenue : {e}")