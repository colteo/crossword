import nltk
from nltk.corpus import words

# Scarica il corpus di parole (esegui solo la prima volta)
nltk.download('words')


def find_words(length=None, pattern=None):
    # Ottieni tutte le parole inglesi
    english_words = set(words.words())

    # Filtra per lunghezza se specificata
    if length:
        english_words = {word for word in english_words if len(word) == length}

    # Filtra per pattern se specificato
    if pattern:
        def match_pattern(word):
            if len(word) != len(pattern):
                return False
            return all(p == '_' or w.lower() == p.lower() for w, p in zip(word, pattern))

        english_words = {word for word in english_words if match_pattern(word)}

    return sorted(english_words)


# Esempio di utilizzo
if __name__ == "__main__":
    # Trova tutte le parole di 5 lettere
    five_letter_words = find_words(length=5)
    print("Parole di 5 lettere:", five_letter_words[:10])  # Mostra solo le prime 10

    # Trova parole di 6 lettere che iniziano con 'a' e finiscono con 'e'
    pattern_words = find_words(length=6, pattern='a____e')
    print("\nParole di 6 lettere che iniziano con 'a' e finiscono con 'e':", pattern_words)

    # Trova parole di 6 lettere che iniziano con 'a' e finiscono con 'e'
    pattern_words = find_words(length=6, pattern='_w____')
    print("\nParole di 6 lettere che iniziano con 'a' e finiscono con 'e':", pattern_words)