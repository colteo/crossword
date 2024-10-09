import random
from nltk.corpus import words
import nltk

nltk.download('words', quiet=True)


class CrosswordGenerator:
    def __init__(self, grid_size=15):
        self.grid_size = grid_size
        self.grid = [['_' for _ in range(grid_size)] for _ in range(grid_size)]
        self.word_list = self.get_word_list()

    @staticmethod
    def get_word_list():
        return set(word.lower() for word in words.words() if word.isalpha())

    def find_word(self, length_range, pattern=None):
        matching_words = [word for word in self.word_list if length_range[0] <= len(word) <= length_range[1]]
        if pattern:
            matching_words = [word for word in matching_words if all(
                word[i] == pattern[i] for i in range(min(len(word), len(pattern))) if pattern[i] != '_')]
        return random.choice(matching_words) if matching_words else None

    def find_word_with_letter(self, length_range, letter, positions):
        for pos in positions:
            for length in range(length_range[0], length_range[1] + 1):
                if pos < length:
                    pattern = ['_'] * length
                    pattern[pos] = letter
                    word = self.find_word((length, length), ''.join(pattern))
                    if word:
                        return word
        return None

    def place_word(self, word, start_row, start_col, vertical=False):
        for i, letter in enumerate(word):
            if vertical:
                self.grid[start_row + i][start_col] = letter
            else:
                self.grid[start_row][start_col + i] = letter

    def find_intersections(self, second_word, third_word, second_word_start_row, third_word_start_row, second_word_col,
                           third_word_col, start_row_1):
        same_row_letters = []
        for i in range(len(second_word)):
            second_word_row = second_word_start_row + i
            if (second_word_row != start_row_1 and
                    second_word_row >= third_word_start_row and
                    second_word_row < third_word_start_row + len(third_word) and
                    abs(second_word_row - start_row_1) > 1):  # Aggiungiamo questa condizione
                third_word_index = second_word_row - third_word_start_row
                same_row_letters.append({
                    'second_word_letter': second_word[i],
                    'third_word_letter': third_word[third_word_index],
                    'row': second_word_row,
                    'second_word_col': second_word_col,
                    'third_word_col': third_word_col,
                    'distance': abs(second_word_col - third_word_col)
                })
        return same_row_letters

    def find_fourth_word(self, selected_intersection):
        distance = selected_intersection['distance']
        min_length = max(3, distance + 1)  # Aumentiamo la lunghezza minima
        max_length = min(15, distance + 5)  # Aumentiamo la lunghezza massima

        left_col = min(selected_intersection['second_word_col'], selected_intersection['third_word_col'])
        right_col = max(selected_intersection['second_word_col'], selected_intersection['third_word_col'])

        for length in range(min_length, max_length + 1):
            pattern = ['_'] * length
            left_index = 0 if left_col == selected_intersection['second_word_col'] else distance
            right_index = distance if right_col == selected_intersection['third_word_col'] else 0

            pattern[left_index] = selected_intersection['second_word_letter']
            pattern[right_index] = selected_intersection['third_word_letter']

            word = self.find_word((length, length), ''.join(pattern))
            if word:
                return word, left_col - left_index

        return None, None

    def find_free_letters_in_vertical_word(self, word, start_row, col):
        free_letters = []
        for i, letter in enumerate(word):
            row = start_row + i

            # Contiamo gli spazi liberi a sinistra della lettera
            left_spaces = 0
            for j in range(col - 1, -1, -1):
                if self.grid[row][j] == '_' and self.grid[row - 1][j] == '_' and self.grid[row + 1][j] == '_':
                    left_spaces += 1
                else:
                    break

            # Contiamo gli spazi liberi a destra della lettera
            right_spaces = 0
            for j in range(col + 1, self.grid_size):
                if self.grid[row][j] == '_' and self.grid[row - 1][j] == '_' and self.grid[row + 1][j] == '_':
                    right_spaces += 1
                else:
                    break

            if left_spaces > 0 and right_spaces > 0:
                total_spaces = left_spaces + right_spaces
                if total_spaces > len(self.first_word):
                    total_spaces = len(self.first_word)

                # Se c'è abbastanza spazio per una parola (diciamo, almeno 5 lettere in totale)
                if total_spaces >= 3:
                    other_letters = [(j, self.grid[row][j]) for j in range(self.grid_size) if
                                     j != col and self.grid[row][j] != '_']
                    free_letters.append({
                        'letter': letter,
                        'row': row,
                        'col': col,
                        'index': i,
                        'other_letters': other_letters,
                        'left_spaces': left_spaces,
                        'right_spaces': right_spaces
                    })

        return free_letters

    def find_fifth_word(self, third_word, third_word_start_row, third_word_col):
        free_letters = self.find_free_letters_in_vertical_word(third_word, third_word_start_row, third_word_col)

        for letter_info in free_letters:
            available_space = letter_info['left_spaces'] + letter_info['right_spaces'] + 1
            min_length = max(5, 3)  # Lunghezza minima di 5 o 3, quale sia maggiore
            max_length = min(available_space,
                             self.grid_size)  # Non superare lo spazio disponibile o la dimensione della griglia

            for length in range(min_length, max_length + 1):
                matching_words = [word for word in self.word_list
                                  if len(word) == length and letter_info['letter'] in word]

                for word in matching_words:
                    # Trova la posizione della lettera di intersezione nella parola
                    intersection_index = word.index(letter_info['letter'])

                    # Calcola la colonna di inizio in base alla posizione dell'intersezione
                    start_col = letter_info['col'] - intersection_index

                    # Verifica se la parola si adatta alla griglia senza sovrapporsi ad altre lettere
                    if (start_col >= 0 and
                            start_col + len(word) <= self.grid_size and
                            all(self.grid[letter_info['row']][j] == '_' or
                                self.grid[letter_info['row']][j] == word[j - start_col]
                                for j in range(start_col, start_col + len(word)))):
                        return word, letter_info['row'], start_col

        return None, None, None

    def generate_crossword(self):
        # Trova e posiziona la prima parola
        self.first_word = self.find_word((8, 12))
        if not self.first_word:
            return "Non è possibile trovare una parola adatta per iniziare il cruciverba."

        self.start_row_1 = self.grid_size // 2
        self.start_col_1 = (self.grid_size - len(self.first_word)) // 2
        self.place_word(self.first_word, self.start_row_1, self.start_col_1)

        # Trova e posiziona la seconda parola
        extracted_letter_2_index = random.randint(0, len(self.first_word) // 2 - 1)
        extracted_letter_2 = self.first_word[extracted_letter_2_index]
        second_word = self.find_word_with_letter((6, 8), extracted_letter_2, [3, 4])

        if not second_word:
            return "Non è possibile trovare una seconda parola adatta."

        second_word_col = self.start_col_1 + extracted_letter_2_index
        second_word_start_row = self.start_row_1 - second_word.index(extracted_letter_2)
        self.place_word(second_word, second_word_start_row, second_word_col, vertical=True)

        # Trova e posiziona la terza parola
        extracted_letter_3_index = random.randint(len(self.first_word) // 2 + 1, len(self.first_word) - 1)
        extracted_letter_3 = self.first_word[extracted_letter_3_index]
        third_word = self.find_word_with_letter((6, 8), extracted_letter_3, [3, 4])

        if not third_word:
            return "Non è possibile trovare una terza parola adatta."

        third_word_col = self.start_col_1 + extracted_letter_3_index
        third_word_start_row = self.start_row_1 - third_word.index(extracted_letter_3)
        self.place_word(third_word, third_word_start_row, third_word_col, vertical=True)

        # Trova le intersezioni e la quarta parola
        same_row_letters = self.find_intersections(second_word, third_word, second_word_start_row, third_word_start_row,
                                                   second_word_col, third_word_col, self.start_row_1)

        fourth_word = None
        selected_intersection = None
        if same_row_letters:
            # Ordiniamo le intersezioni per distanza dalla prima parola
            same_row_letters.sort(key=lambda x: abs(x['row'] - self.start_row_1), reverse=True)

            for intersection in same_row_letters:
                fourth_word, fourth_word_start_col = self.find_fourth_word(intersection)
                if fourth_word:
                    selected_intersection = intersection
                    break

            if fourth_word:
                fourth_word_row = selected_intersection['row']
                self.place_word(fourth_word, fourth_word_row, fourth_word_start_col)

        # Aggiungi la quinta parola
        fifth_word, fifth_word_row, fifth_word_start_col = self.find_fifth_word(third_word,
                                                                                third_word_start_row,
                                                                                third_word_col)

        if fifth_word:
            self.place_word(fifth_word, fifth_word_row, fifth_word_start_col)

        if fifth_word:
                self.place_word(fifth_word, fifth_word_row, fifth_word_start_col)

        self.trim_grid()

        return self.format_result(self.first_word, second_word, third_word, fourth_word, fifth_word,
                                  extracted_letter_2, extracted_letter_2_index,
                                  extracted_letter_3, extracted_letter_3_index,
                                  same_row_letters, selected_intersection,
                                  fifth_word_row, fifth_word_start_col, third_word_col)

    def print_crossword(self):
        # Stampa i numeri di colonna
        col_numbers = '    ' + '  '.join(f'{i:2d}' for i in range(self.grid_size))
        print(col_numbers)

        # Stampa una linea separatrice
        separator = '  ' + '-' * (self.grid_size * 3 + 1)
        print(separator)

        # Stampa ogni riga con il suo numero
        for i, row in enumerate(self.grid):
            row_str = ' '.join(f' {cell} ' for cell in row)
            print(f'{i:2d}|{row_str}|')

        # Stampa un'altra linea separatrice alla fine
        print(separator)

    def trim_grid(self):
        # Trova le righe non vuote (ora consideriamo '_' come vuoto)
        non_empty_rows = [i for i, row in enumerate(self.grid) if any(cell != '_' for cell in row)]

        # Trova le colonne non vuote
        non_empty_cols = [j for j in range(self.grid_size) if
                          any(self.grid[i][j] != '_' for i in range(self.grid_size))]

        # Crea una nuova griglia con solo le righe e colonne non vuote, sostituendo '_' con ' '
        new_grid = [[' ' if self.grid[i][j] == '_' else self.grid[i][j]
                     for j in non_empty_cols]
                    for i in non_empty_rows]

        # Aggiorna la griglia e la dimensione
        self.grid = new_grid
        self.grid_size = len(new_grid)

    def format_result(self, first_word, second_word, third_word, fourth_word, fifth_word,
                      extracted_letter_2, extracted_letter_2_index,
                      extracted_letter_3, extracted_letter_3_index,
                      same_row_letters, selected_intersection,
                      fifth_word_row, fifth_word_start_col, third_word_col):
        crossword = "\n".join(" ".join(row) for row in self.grid)
        print(crossword)

        # self.print_crossword()

        result = f"Prima parola: {first_word}\n"
        result += f"Seconda parola: {second_word}\n"
        result += f"Lettera di incrocio: {extracted_letter_2} (posizione {extracted_letter_2_index + 1} nella prima parola, "
        result += f"posizione {second_word.index(extracted_letter_2) + 1} nella seconda parola)\n"
        result += f"Terza parola: {third_word}\n"
        result += f"Lettera di incrocio: {extracted_letter_3} (posizione {extracted_letter_3_index + 1} nella prima parola, "
        result += f"posizione {third_word.index(extracted_letter_3) + 1} nella terza parola)\n"

        if same_row_letters:
            result += "Intersezioni trovate (escludendo la riga della prima parola):\n"
            for info in same_row_letters:
                result += f"- Riga {info['row']}: '{info['second_word_letter']}' (seconda parola) e '{info['third_word_letter']}' (terza parola), "
                result += f"distanza: {info['distance']} colonne\n"

            if selected_intersection:
                result += f"\nIntersezione selezionata casualmente: Riga {selected_intersection['row']}\n"

            if fourth_word:
                result += f"Quarta parola: {fourth_word}\n"
                result += f"Inserita tra '{selected_intersection['second_word_letter']}' della seconda parola e "
                result += f"'{selected_intersection['third_word_letter']}' della terza parola\n"
            else:
                result += "Non è stato possibile trovare una quarta parola adatta.\n"
        else:
            result += "Non ci sono intersezioni valide tra la seconda e la terza parola.\n"

        if fifth_word:
            result += f"\nQuinta parola: {fifth_word}\n"
            result += f"Inserita alla riga {fifth_word_row}, colonna di inizio {fifth_word_start_col}\n"
            intersection_index = third_word_col - fifth_word_start_col
            result += f"Interseca con la terza parola alla lettera '{fifth_word[intersection_index]}' (posizione {intersection_index + 1} nella quinta parola)\n"
        else:
            result += "\nNon è stato possibile trovare una quinta parola adatta.\n"

        return result

    def to_html(self):
        html = f"""
        <html>
        <head>
            <style>
                table {{ border-collapse: collapse; }}
                td {{ 
                    width: 30px; 
                    height: 30px; 
                    text-align: center; 
                    vertical-align: middle; 
                    font-size: 20px;
                    font-weight: bold;
                    border: 1px solid #000;
                }}
                td.empty {{ 
                    background-color: transparent; 
                    border: none;
                }}
            </style>
        </head>
        <body>
            <table>
        """

        for row in self.grid:
            html += "<tr>"
            for cell in row:
                if cell == ' ':
                    html += '<td class="empty"></td>'
                else:
                    html += f'<td>{cell}</td>'
            html += "</tr>"

        html += """
            </table>
        </body>
        </html>
        """
        return html

# Uso della classe
generator = CrosswordGenerator()
print(generator.generate_crossword())
print(generator.to_html())
