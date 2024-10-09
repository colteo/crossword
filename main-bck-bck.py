import random
from nltk.corpus import words
import nltk

nltk.download('words', quiet=True)


def get_word_list():
    return set(word.lower() for word in words.words() if word.isalpha())


word_list = get_word_list()  # Carichiamo la lista di parole una sola volta


def find_word(length_range, pattern=None):
    matching_words = [word for word in word_list if length_range[0] <= len(word) <= length_range[1]]
    if pattern:
        pattern_length = len(pattern)
        matching_words = [word for word in matching_words if len(word) == pattern_length and all(
            word[i] == pattern[i] for i in range(len(pattern)) if pattern[i] != '_')]
    return random.choice(matching_words) if matching_words else None


def find_word_with_letter(length_range, letter, positions):
    for pos in positions:
        for length in range(length_range[0], length_range[1] + 1):
            if pos < length:
                pattern = ['_'] * length
                pattern[pos] = letter
                word = find_word((length, length), pattern)
                if word:
                    return word
    return None


def create_thematic_crossword():
    # Trova la prima parola (8-10 caratteri)
    first_word = find_word((8, 10))
    if not first_word:
        return "Non è possibile trovare una parola adatta per iniziare il cruciverba."

    extracted_letter_2 = first_word[1]
    extracted_letter_6 = first_word[5] if len(first_word) > 5 else None

    # Cerca la seconda parola (6-8 caratteri)
    second_word = find_word_with_letter((6, 8), extracted_letter_2, [3, 4])
    if not second_word:
        return f"Non è possibile trovare una parola adatta con la lettera '{extracted_letter_2}' in posizione 4 o 5."

    # Cerca la terza parola (6-8 caratteri)
    if extracted_letter_6:
        third_word = find_word_with_letter((6, 8), extracted_letter_6, [3, 4])
        if not third_word:
            return f"Non è possibile trovare una terza parola adatta con la lettera '{extracted_letter_6}'."
    else:
        return "La prima parola è troppo corta per estrarre la sesta lettera."

    # Calcola la dimensione della griglia
    grid_size = max(len(first_word) + 6, len(second_word) + len(third_word) + 4)

    # Crea la griglia del cruciverba
    grid = [[' ' for _ in range(grid_size)] for _ in range(grid_size)]

    # Posiziona la prima parola orizzontalmente al centro
    start_row_1 = grid_size // 2
    start_col_1 = (grid_size - len(first_word)) // 2
    for i, letter in enumerate(first_word):
        grid[start_row_1][start_col_1 + i] = letter

    # Posiziona la seconda parola verticalmente
    intersection_index_2 = second_word.index(extracted_letter_2)
    start_row_2 = start_row_1 - intersection_index_2
    start_col_2 = start_col_1 + 1  # Seconda lettera della prima parola

    # Posiziona la terza parola verticalmente
    intersection_index_3 = third_word.index(extracted_letter_6)
    start_row_3 = start_row_1 - intersection_index_3
    start_col_3 = start_col_1 + 5  # Sesta lettera della prima parola

    # Inserisci le parole nella griglia
    for i, letter in enumerate(second_word):
        grid[start_row_2 + i][start_col_2] = letter
    for i, letter in enumerate(third_word):
        grid[start_row_3 + i][start_col_3] = letter

    # Trova le righe comuni tra la seconda e la terza parola
    rows_second = {start_row_2 + i: i for i in range(len(second_word))}
    rows_third = {start_row_3 + i: i for i in range(len(third_word))}
    common_rows = set(rows_second.keys()).intersection(rows_third.keys())

    fourth_word = None
    for row in common_rows:
        i_second = rows_second[row]
        i_third = rows_third[row]
        letter_second = second_word[i_second]
        letter_third = third_word[i_third]

        # Calcola la posizione orizzontale della quarta parola
        start_col_4 = min(start_col_2, start_col_3)
        length_fourth_word = abs(start_col_3 - start_col_2) + 1

        # Calcola le posizioni delle lettere delle parole verticali nella quarta parola
        pos_second = start_col_2 - start_col_4
        pos_third = start_col_3 - start_col_4

        pattern = ['_'] * length_fourth_word
        pattern[pos_second] = letter_second
        pattern[pos_third] = letter_third

        # Cerca una parola che corrisponda al pattern
        fourth_word = find_word((length_fourth_word, length_fourth_word), pattern)
        if fourth_word:
            start_row_4 = row
            # Inserisci la quarta parola nella griglia
            for idx, letter in enumerate(fourth_word):
                grid[start_row_4][start_col_4 + idx] = letter
            break

    if not fourth_word:
        return "Non è stato possibile trovare una quarta parola che interseca la seconda e la terza parola."

    # Rimuovi le righe e colonne vuote
    grid = [row for row in grid if set(row) != {' '}]
    grid = list(map(list, zip(*[col for col in zip(*grid) if set(col) != {' '}])))

    # Genera il cruciverba come stringa
    crossword = "\n".join(" ".join(row) for row in grid)

    return f"Cruciverba generato:\n\n{crossword}\n\nParola orizzontale: {first_word}\nSeconda parola verticale: {second_word}\nTerza parola verticale: {third_word}\nQuarta parola orizzontale: {fourth_word}"


# Esegui il generatore di cruciverba
print(create_thematic_crossword())
