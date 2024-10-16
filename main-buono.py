import os
import uuid
from datetime import datetime
import random
# from nltk.corpus import words
# import nltk
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import mysql.connector

# nltk.download('words', quiet=True)

@dataclass
class Word:
    text: str
    x: int
    y: int
    is_horizontal: bool
    clue: str = ""
    word_pattern: str = ""
    num_words: str = ""

class CrosswordGenerator:
    def __init__(self, grid_size=15, cell_size=75, db_config=None):
        # Esistente...
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.grid = [['_' for _ in range(grid_size)] for _ in range(grid_size)]
        self.placed_words = []  # List of placed words with additional info
        self.db_config = db_config  # Configuration for the database connection

        # Crea la directory di output se non esiste
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)

        # Genera un GUID per questa sessione di generazione
        self.guid = uuid.uuid4()

        # Ottieni la data e l'ora corrente
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if db_config:
            self.word_list = self.get_word_list_from_db()
        else:
            raise ValueError("Database configuration is required.")

    def get_word_list_from_db(self):
        """
        Recupera le parole dal database MySQL.
        """
        word_list = []

        # Connessione al database MySQL
        connection = mysql.connector.connect(**self.db_config)
        cursor = connection.cursor(dictionary=True)

        # Query per recuperare tutte le parole e le informazioni aggiuntive
        query = """
        SELECT solution, clue, word_pattern, num_words 
        FROM crossword_entries
        WHERE LENGTH(solution) <= %s
        """
        max_word_length = 15  # Limitiamo la lunghezza della parola a 15 caratteri (può essere modificato)
        cursor.execute(query, (max_word_length,))

        # Recuperiamo i risultati e li salviamo nella lista
        for row in cursor.fetchall():
            word_list.append({
                'solution': row['solution'].lower(),
                'clue': row['clue'],
                'word_pattern': row['word_pattern'],
                'num_words': row['num_words']
            })

        cursor.close()
        connection.close()

        return word_list

    # @staticmethod
    # def get_word_list():
    #     return set(word.lower() for word in words.words() if word.isalpha())

    def find_word(self, length_range, pattern=None):
        """
        Cerca una parola dalla lista recuperata dal database, in base alla lunghezza e a un eventuale pattern.
        """
        matching_words = [word for word in self.word_list
                          if length_range[0] <= len(word['solution']) <= length_range[1]]

        if pattern:
            matching_words = [word for word in matching_words if all(
                word['solution'][i] == pattern[i]
                for i in range(min(len(word['solution']), len(pattern))) if pattern[i] != '_')]

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

    def place_word(self, word_info, start_row, start_col, vertical=False):
        """
        Posiziona una parola nella griglia e salva le informazioni relative alla parola.
        """
        word = word_info['solution']
        clue = word_info['clue']
        word_pattern = word_info['word_pattern']
        num_words = word_info['num_words']

        is_horizontal = not vertical
        for i, letter in enumerate(word):
            if vertical:
                self.grid[start_row + i][start_col] = letter
            else:
                self.grid[start_row][start_col + i] = letter

        # Salva le informazioni relative alla parola posizionata
        self.placed_words.append(Word(word, start_col, start_row, is_horizontal, clue, word_pattern, num_words))


    def place_first_word(self):
        """
        Posiziona la prima parola al centro della griglia.
        """
        first_word_info = self.find_word((8, 12))  # Puoi modificare le lunghezze delle parole qui
        if not first_word_info:
            return False

        start_row = self.grid_size // 2
        start_col = (self.grid_size - len(first_word_info['solution'])) // 2
        self.place_word(first_word_info, start_row, start_col)
        return True

    def place_second_word(self):
        return self.place_intersecting_word(0, 0, len(self.placed_words[0].text) // 2 - 1)

    def place_third_word(self):
        return self.place_intersecting_word(0, len(self.placed_words[0].text) // 2 + 1, len(self.placed_words[0].text) - 1)

    def place_intersecting_word(self, word_index, start, end):
        extracted_letter_index = random.randint(start, end)
        extracted_letter = self.placed_words[word_index].text[extracted_letter_index]

        # Trova una nuova parola che contenga la lettera estratta
        new_word = self.find_word_with_letter((6, 8), extracted_letter, [3, 4])

        if not new_word:
            return False

        new_word_col = self.placed_words[word_index].x + extracted_letter_index

        # Qui correggi l'accesso alla parola nel dizionario new_word['solution']
        new_word_start_row = self.placed_words[word_index].y - new_word['solution'].index(extracted_letter)

        # Posiziona la nuova parola in verticale
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

            # Riduciamo il min_length a 3 per avere più parole valide
            min_length = max(3, 3)  # Lunghezza minima di 3
            max_length = min(available_space,
                             self.grid_size)  # Non superare lo spazio disponibile o la dimensione della griglia

            for length in range(min_length, max_length + 1):
                matching_words = [word for word in self.word_list
                                  if len(word['solution']) == length and letter_info['letter'] in word['solution']]

                for word in matching_words:
                    # Trova la posizione della lettera di intersezione nella parola
                    intersection_index = word['solution'].index(letter_info['letter'])

                    # Calcola la colonna di inizio in base alla posizione dell'intersezione
                    start_col = letter_info['col'] - intersection_index

                    # Verifica se la parola si adatta alla griglia senza sovrapporsi ad altre lettere
                    if (start_col >= 0 and
                            start_col + len(word['solution']) <= self.grid_size and
                            all(self.grid[letter_info['row']][j] == '_' or
                                self.grid[letter_info['row']][j] == word['solution'][j - start_col]
                                for j in range(start_col, start_col + len(word['solution'])))):
                        # Posiziona la parola e termina la funzione
                        self.place_word(word, letter_info['row'], start_col)
                        return True

        return False

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
        """
        Stampa le parole posizionate con le informazioni aggiuntive.
        """
        for word in self.placed_words:
            print(f"Parola: {word.text}, Posizione: ({word.x}, {word.y}), "
                  f"{'Orizzontale' if word.is_horizontal else 'Verticale'}, "
                  f"Clue: {word.clue}, Word Pattern: {word.word_pattern}, Num Words: {word.num_words}")

    def print_crossword(self):
        """
        Stampa la griglia del cruciverba.
        """
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
        # self.trim_grid()

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
        new_grid = [[' ' if self.grid[i][j] == '_' else self.grid[i][j]
                     for j in non_empty_cols]
                    for i in non_empty_rows]

        # Aggiorna la griglia e la dimensione
        self.grid = new_grid
        self.grid_size = len(new_grid)

    def generate_html_stages(self):
        html_schema = self.generate_html_schema(len(self.placed_words))
        filename = f"crossword_html_schema.html"
        with open(filename, "w") as f:
            f.write(html_schema)

        # stages = [
        #     self.to_html(1),  # Cruciverba con parola: 1
        # ]
        stages = [
            self.generate_html_word(1),  # Cruciverba con parola: 1
            self.generate_html_word(2),  # Cruciverba con parola: 1, 2
            self.generate_html_word(3),  # Cruciverba con parola: 1, 2, 3
            self.generate_html_word(4),  # Cruciverba con parola: 1, 2, 3, 4
            self.generate_html_word(5),  # Cruciverba con parola: 1, 2, 3, 4, 5
        ]

        for i, html in enumerate(stages):
            filename = f"crossword_stage_{i}.html"
            with open(filename, "w") as f:
                f.write(html)
            print(f"Generated {filename}")

    def generate_html_word(self, num_words_to_show):
        visible_cells = set()
        all_word_cells = set()

        # Raccoglie tutte le celle occupate da parole
        for word in self.placed_words:
            for i in range(len(word.text)):
                if word.is_horizontal:
                    all_word_cells.add((word.x + i, word.y))
                else:
                    all_word_cells.add((word.x, word.y + i))

        # Determina le celle visibili in base al numero di parole da mostrare
        for word in self.placed_words[:num_words_to_show]:
            for i in range(len(word.text)):
                if word.is_horizontal:
                    visible_cells.add((word.x + i, word.y))
                else:
                    visible_cells.add((word.x, word.y + i))

        # Trova le righe e colonne non vuote
        non_empty_rows = set(y for _, y in all_word_cells)
        non_empty_cols = set(x for x, _ in all_word_cells)

        # Crea una mappa delle coordinate originali alle nuove coordinate
        row_map = {orig: new for new, orig in enumerate(sorted(non_empty_rows))}
        col_map = {orig: new for new, orig in enumerate(sorted(non_empty_cols))}

        # Genera l'HTML
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
                }}
                td.empty, td.hidden {{ 
                    background-color: transparent; 
                    border: none;
                }}
                td.visible {{
                    background-color: white;
                    border: 1px solid #000;
                }}
            </style>
        </head>
        <body>
            <table>
        """

        for orig_y in sorted(non_empty_rows):
            html += "<tr>"
            for orig_x in sorted(non_empty_cols):
                if (orig_x, orig_y) in visible_cells:
                    html += f'<td class="visible">{self.grid[orig_y][orig_x]}</td>'
                elif (orig_x, orig_y) in all_word_cells:
                    html += '<td class="hidden"></td>'
                else:
                    html += '<td class="empty"></td>'
            html += "</tr>"

        html += """
            </table>
        </body>
        </html>
        """
        return html

    def generate_html_schema(self, num_words_to_show):
        all_word_cells = set()

        # Raccoglie tutte le celle occupate da parole
        for word in self.placed_words:
            for i in range(len(word.text)):
                if word.is_horizontal:
                    all_word_cells.add((word.x + i, word.y))
                else:
                    all_word_cells.add((word.x, word.y + i))

        # Trova le righe e colonne non vuote
        non_empty_rows = set(y for _, y in all_word_cells)
        non_empty_cols = set(x for x, _ in all_word_cells)

        # Genera l'HTML
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
                td.word {{
                    background-color: white;
                    color: white;
                }}
            </style>
        </head>
        <body>
            <table>
        """

        for orig_y in sorted(non_empty_rows):
            html += "<tr>"
            for orig_x in sorted(non_empty_cols):
                if (orig_x, orig_y) in all_word_cells:
                    html += f'<td class="word">{self.grid[orig_y][orig_x]}</td>'
                else:
                    html += '<td class="empty"></td>'
            html += "</tr>"

        html += """
            </table>
        </body>
        </html>
        """
        return html

    def generate_transparent_image(self):
        min_row = min(word.y for word in self.placed_words)
        max_row = max(word.y + len(word.text) - 1 if not word.is_horizontal else word.y for word in self.placed_words)
        min_col = min(word.x for word in self.placed_words)
        max_col = max(word.x + len(word.text) - 1 if word.is_horizontal else word.x for word in self.placed_words)

        width = ((max_col - min_col + 1) * self.cell_size) + 1
        height = ((max_row - min_row + 1) * self.cell_size) + 1

        image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)

        for word in self.placed_words:
            for i in range(len(word.text)):
                if word.is_horizontal:
                    x = (word.x - min_col + i) * self.cell_size
                    y = (word.y - min_row) * self.cell_size
                else:
                    x = (word.x - min_col) * self.cell_size
                    y = (word.y - min_row + i) * self.cell_size

                draw.rectangle([x, y, x + self.cell_size, y + self.cell_size], fill=(255, 255, 255, 255))
                draw.rectangle([x, y, x + self.cell_size, y + self.cell_size], outline=(0, 0, 0, 255), width=1)

        return image

    def save_transparent_image(self, filename="crossword_structure.png"):
        # Aggiorniamo il nome del file con GUID e timestamp
        filename = f"{self.guid}_{self.timestamp}_{filename}"
        filepath = os.path.join(self.output_dir, filename)

        # Genera e salva l'immagine
        image = self.generate_transparent_image()
        resized_image = self.resize_and_position_image(image)
        resized_image.save(filepath)
        print(f"Immagine salvata come {filepath}")

    def generate_word_image(self, word):
        min_row = min(w.y for w in self.placed_words)
        max_row = max(w.y + len(w.text) - 1 if not w.is_horizontal else w.y for w in self.placed_words)
        min_col = min(w.x for w in self.placed_words)
        max_col = max(w.x + len(w.text) - 1 if w.is_horizontal else w.x for w in self.placed_words)

        width = ((max_col - min_col + 1) * self.cell_size) + 1
        height = ((max_row - min_row + 1) * self.cell_size) + 1

        image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)

        try:
            font_size = int(self.cell_size * 0.6)  # Adatta la dimensione del font alla cella
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        max_height = max(font.getmask(letter).size[1] for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        for i, letter in enumerate(word.text.upper()):
            if word.is_horizontal:
                x = (word.x - min_col + i) * self.cell_size
                y = (word.y - min_row) * self.cell_size
            else:
                x = (word.x - min_col) * self.cell_size
                y = (word.y - min_row + i) * self.cell_size
            #
            # draw.rectangle([x, y, x + self.cell_size, y + self.cell_size], fill=(255, 255, 255, 255))
            # draw.rectangle([x, y, x + self.cell_size, y + self.cell_size], outline=(0, 0, 0, 255), width=1)

            mask = font.getmask(letter)
            text_width, text_height = mask.size

            text_x = x + (self.cell_size - text_width) // 2
            text_y = y + (self.cell_size - max_height) // 2 + (max_height - text_height)

            draw.text((text_x, text_y), letter, fill=(0, 0, 0, 255), font=font)

        return image

    def generate_all_word_images(self):
        images = []
        for i, word in enumerate(self.placed_words):
            image = self.generate_word_image(word)
            resized_image = self.resize_and_position_image(image)

            # Aggiungiamo GUID e timestamp al nome dell'immagine
            filename = f"{self.guid}_{self.timestamp}_crossword_word_{i + 1}.png"
            filepath = os.path.join(self.output_dir, filename)

            resized_image.save(filepath)
            images.append(resized_image)
            print(f"Generated and saved image: {filepath}")

        print(f"Generate {len(images)} immagini per le parole del cruciverba.")
        return images

    def resize_and_position_image(self, image, target_width=1080, target_height=1920, bottom_margin=200):
        # Crea una nuova immagine con sfondo trasparente
        new_image = Image.new('RGBA', (target_width, target_height), (255, 255, 255, 0))

        # Calcola la posizione per centrare l'immagine originale
        x_offset = (target_width - image.width) // 2
        y_offset = target_height - image.height - bottom_margin

        # Incolla l'immagine originale nella nuova immagine
        new_image.paste(image, (x_offset, y_offset), image)

        return new_image

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

        # Alla fine stampa o restituisce il risultato
        # self.print_crossword()
        # self.print_placed_words()

        return self.format_result()

# Esempio di configurazione per il database MySQL
db_config = {
    'user': 'crossword',
    'password': 'crossword',
    'host': 'localhost',
    'database': 'crossword'
}

# Uso della classe
generator = CrosswordGenerator(db_config=db_config)
generator.generate_crossword()
generator.save_transparent_image()
generator.generate_all_word_images()