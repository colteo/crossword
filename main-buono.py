import random
from nltk.corpus import words
import nltk
from dataclasses import dataclass

nltk.download('words', quiet=True)

@dataclass
class Word:
    text: str
    x: int
    y: int
    is_horizontal: bool

class CrosswordGenerator:
    def __init__(self, grid_size=15):
        self.grid_size = grid_size
        self.grid = [['_' for _ in range(grid_size)] for _ in range(grid_size)]
        self.word_list = self.get_word_list()
        self.placed_words = []

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
        is_horizontal = not vertical
        for i, letter in enumerate(word):
            if vertical:
                self.grid[start_row + i][start_col] = letter
            else:
                self.grid[start_row][start_col + i] = letter

        self.placed_words.append(Word(word, start_col, start_row, is_horizontal))

    def place_first_word(self):
        first_word = self.find_word((8, 12))
        if not first_word:
            return False

        start_row = self.grid_size // 2
        start_col = (self.grid_size - len(first_word)) // 2
        self.place_word(first_word, start_row, start_col)
        return True

    def place_second_word(self):
        return self.place_intersecting_word(0, 0, len(self.placed_words[0].text) // 2 - 1)

    def place_third_word(self):
        return self.place_intersecting_word(0, len(self.placed_words[0].text) // 2 + 1, len(self.placed_words[0].text) - 1)

    def place_intersecting_word(self, word_index, start, end):
        extracted_letter_index = random.randint(start, end)
        extracted_letter = self.placed_words[word_index].text[extracted_letter_index]
        new_word = self.find_word_with_letter((6, 8), extracted_letter, [3, 4])

        if not new_word:
            return False

        new_word_col = self.placed_words[word_index].x + extracted_letter_index
        new_word_start_row = self.placed_words[word_index].y - new_word.index(extracted_letter)
        self.place_word(new_word, new_word_start_row, new_word_col, vertical=True)
        return True

    def place_fourth_word(self):
        # Trova le intersezioni e la quarta parola
        same_row_letters = self.find_intersections_fourth_word()
        fourth_word = None
        intersection = None
        fourth_word_start_col = None
        if same_row_letters:
            while not fourth_word:
                intersection = random.choice(same_row_letters) if same_row_letters else None
                fourth_word, fourth_word_start_col = self.find_fourth_word(intersection)

            fourth_word_row = intersection['row']
            self.place_word(fourth_word, fourth_word_row, fourth_word_start_col)

        return True

    def find_intersections_fourth_word(self):
        second_word = self.placed_words[1].text
        third_word = self.placed_words[2].text

        second_word_col = self.placed_words[1].x
        third_word_col = self.placed_words[2].x

        second_word_start_row = self.placed_words[1].y
        third_word_start_row = self.placed_words[2].y

        start_row_1 = self.placed_words[0].y
        # , second_word, third_word, second_word_start_row, third_word_start_row, second_word_col,
        # third_word_col, start_row_1

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

    def place_fifth_word(self):
        free_letters = self.find_free_letters_in_vertical_word(self.placed_words[2])

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
                        # return word, letter_info['row'], start_col
                        self.place_word(word, letter_info['row'], start_col)
                        return True

    def find_free_letters_in_vertical_word(self, vertical_word):
        word = vertical_word.text
        col = vertical_word.x
        start_row = vertical_word.y
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
                if total_spaces > len(self.placed_words[0].text):
                    total_spaces = len(self.placed_words[0].text)

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

    def print_placed_words(self):
        for word in self.placed_words:
            print(
                f"Parola: {word.text}, Posizione: ({word.x}, {word.y}), {'Orizzontale' if word.is_horizontal else 'Verticale'}")

    def print_crossword(self):
        # Stampa i numeri di colonna
        col_numbers = '   ' + '  '.join(f'{i:2d}' for i in range(self.grid_size))
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

    def format_result(self):
        self.trim_grid()

        # crossword = "\n".join(" ".join(row) for row in self.grid)
        # print(crossword)

        self.print_crossword()

        self.print_placed_words()

    def trim_grid(self):
        # Trova le righe non vuote (ora consideriamo '_' come vuoto)
        non_empty_rows = [i for i, row in enumerate(self.grid) if any(cell != '_' for cell in row)]

        # Trova le colonne non vuote
        non_empty_cols = [j for j in range(self.grid_size) if
                          any(self.grid[i][j] != '_' for i in range(self.grid_size))]

        # Crea una nuova griglia con solo le righe e colonne non vuote, sostituendo '_' con ' '
        new_grid = [['_' if self.grid[i][j] == '_' else self.grid[i][j]
                     for j in non_empty_cols]
                    for i in non_empty_rows]

        # Aggiorna la griglia e la dimensione
        self.grid = new_grid
        self.grid_size = len(new_grid)

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

    def generate_crossword(self):
        if not self.place_first_word():
            return "Impossibile trovare una parola adatta per iniziare il cruciverba."

        if not self.place_second_word():
            return "Impossibile trovare una seconda parola adatta."

        if not self.place_third_word():
            return "Impossibile trovare una terza parola adatta."

        if not self.place_fourth_word():
            return "Impossibile trovare una quarta parola adatta."

        if not self.place_fifth_word():
            return "Impossibile trovare una quinta parola adatta."

        return self.format_result()


# Uso della classe
generator = CrosswordGenerator()
print(generator.generate_crossword())
print(generator.to_html())
