import os
import uuid
from datetime import datetime
import random
from dataclasses import dataclass, asdict
import json
from PIL import Image, ImageDraw, ImageFont
import mysql.connector
import logging


@dataclass
class Word:
    text: str
    x: int
    y: int
    is_horizontal: bool
    clue: str = ""
    word_pattern: str = ""
    num_words: str = ""

    def to_dict(self):
        """
        Converte l'oggetto Word in un dizionario.
        Utile per la serializzazione JSON.
        """
        return asdict(self)


class CrosswordGenerator:
    def __init__(self, grid_size=15, cell_size=75, db_config=None, max_attempts=3):
        """
        Inizializza il generatore di cruciverba

        Args:
            grid_size (int): Dimensione della griglia
            cell_size (int): Dimensione di ogni cella in pixel
            db_config (dict): Configurazione del database
            max_attempts (int): Numero massimo di tentativi di generazione
        """
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.grid = [['_' for _ in range(grid_size)] for _ in range(grid_size)]
        self.placed_words = []
        self.db_config = db_config
        self.max_attempts = max_attempts

        self.guid = uuid.uuid4()
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        self.output_dir = os.path.join("output", f"{self.timestamp}-{self.guid}")
        os.makedirs(self.output_dir, exist_ok=True)

        logging.basicConfig(
            filename=os.path.join(self.output_dir, 'crossword.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        if db_config:
            self.word_list = self.get_word_list_from_db()
        else:
            raise ValueError("Database configuration is required.")

    def get_word_list_from_db(self):
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor(dictionary=True)

            query = """
            SELECT solution, clue, word_pattern, num_words 
            FROM crossword_entries
            WHERE LENGTH(solution) <= %s
            """
            cursor.execute(query, (self.grid_size,))
            word_list = cursor.fetchall()

            cursor.close()
            connection.close()

            logging.info(f"Retrieved {len(word_list)} words from database")
            return word_list

        except mysql.connector.Error as err:
            logging.error(f"Database error: {err}")
            raise

    def find_word(self, length_range, pattern=None):
        """
        Cerca una parola dalla lista che soddisfa i criteri specificati.
        """
        matching_words = [
            word for word in self.word_list
            if length_range[0] <= len(word['solution']) <= length_range[1]
        ]

        if pattern:
            matching_words = [
                word for word in matching_words
                if all(word['solution'][i] == pattern[i]
                       for i in range(min(len(word['solution']), len(pattern)))
                       if pattern[i] != '_')
            ]

        return random.choice(matching_words) if matching_words else None

    def find_word_with_letter(self, length_range, letter, positions):
        """
        Trova una parola che contiene una lettera specifica in una delle posizioni date.
        """
        for pos in positions:
            for length in range(length_range[0], length_range[1] + 1):
                if pos < length:
                    pattern = ['_'] * length
                    pattern[pos] = letter
                    word = self.find_word((length, length), ''.join(pattern))
                    if word:
                        return word
        return None

    def can_place_word(self, word, start_row, start_col, vertical=False):
        """
        Verifica se una parola può essere piazzata in una posizione specifica.
        """
        if vertical:
            if start_row < 0 or start_row + len(word) > self.grid_size:
                return False
            return all(self.grid[start_row + i][start_col] in ('_', word[i])
                       for i in range(len(word)))
        else:
            if start_col < 0 or start_col + len(word) > self.grid_size:
                return False
            return all(self.grid[start_row][start_col + i] in ('_', word[i])
                       for i in range(len(word)))

    def place_word(self, word_info, start_row, start_col, vertical=False):
        """
        Posiziona una parola nella griglia.
        """
        word = word_info['solution']
        if not self.can_place_word(word, start_row, start_col, vertical):
            return False

        is_horizontal = not vertical
        for i, letter in enumerate(word):
            if vertical:
                self.grid[start_row + i][start_col] = letter
            else:
                self.grid[start_row][start_col + i] = letter

        self.placed_words.append(Word(
            word,
            start_col,
            start_row,
            is_horizontal,
            word_info['clue'],
            word_info['word_pattern'],
            word_info['num_words']
        ))

        logging.info(f"Placed word: {word} at ({start_row}, {start_col}), vertical={vertical}")
        return True

    def place_first_word(self):
        """
        Posiziona la prima parola al centro della griglia.
        """
        first_word_info = self.find_word((8, 12))
        if not first_word_info:
            logging.warning("Could not find suitable first word")
            return False

        start_row = self.grid_size // 2
        start_col = (self.grid_size - len(first_word_info['solution'])) // 2
        return self.place_word(first_word_info, start_row, start_col)

    def place_second_word(self):
        """
        Posiziona la seconda parola intersecando la prima.
        """
        return self.place_intersecting_word(0, 0, len(self.placed_words[0].text) // 2 - 1)

    def place_third_word(self):
        """
        Posiziona la terza parola intersecando la prima.
        """
        return self.place_intersecting_word(0, len(self.placed_words[0].text) // 2 + 1,
                                            len(self.placed_words[0].text) - 1)

    def place_intersecting_word(self, word_index, start, end):
        """
        Posiziona una parola che interseca una parola esistente.
        """
        extracted_letter_index = random.randint(start, end)
        extracted_letter = self.placed_words[word_index].text[extracted_letter_index]

        new_word = self.find_word_with_letter((6, 8), extracted_letter, [3, 4])
        if not new_word:
            return False

        new_word_col = self.placed_words[word_index].x + extracted_letter_index
        new_word_start_row = self.placed_words[word_index].y - new_word['solution'].index(extracted_letter)

        return self.place_word(new_word, new_word_start_row, new_word_col, vertical=True)

    def place_fourth_word(self):
        """
        Posiziona la quarta parola collegando la seconda e la terza.
        """
        intersections = self.find_intersections_fourth_word()
        if not intersections:
            return False

        for intersection in random.sample(intersections, len(intersections)):
            fourth_word, start_col = self.find_fourth_word(intersection)
            if fourth_word and start_col is not None:
                if self.place_word(fourth_word, intersection['row'], start_col):
                    return True
        return False

    def find_intersections_fourth_word(self):
        """
        Trova le possibili intersezioni per la quarta parola.
        """
        second_word = self.placed_words[1]
        third_word = self.placed_words[2]
        start_row_1 = self.placed_words[0].y

        same_row_letters = []
        for i in range(len(second_word.text)):
            second_word_row = second_word.y + i
            if (second_word_row != start_row_1 and
                    second_word_row >= third_word.y and
                    second_word_row < third_word.y + len(third_word.text) and
                    abs(second_word_row - start_row_1) > 1):
                third_word_index = second_word_row - third_word.y
                same_row_letters.append({
                    'second_word_letter': second_word.text[i],
                    'third_word_letter': third_word.text[third_word_index],
                    'row': second_word_row,
                    'second_word_col': second_word.x,
                    'third_word_col': third_word.x,
                    'distance': abs(second_word.x - third_word.x)
                })
        return same_row_letters

    def find_fourth_word(self, selected_intersection):
        """
        Trova una parola adatta per la quarta posizione.
        """
        distance = selected_intersection['distance']
        min_length = max(3, distance + 1)
        max_length = min(15, distance + 5)

        left_col = min(selected_intersection['second_word_col'],
                       selected_intersection['third_word_col'])
        right_col = max(selected_intersection['second_word_col'],
                        selected_intersection['third_word_col'])

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
        """
        Posiziona la quinta parola trovando spazi liberi nella terza parola.
        """
        free_letters = self.find_free_letters_in_vertical_word(self.placed_words[2])

        for letter_info in free_letters:
            available_space = letter_info['left_spaces'] + letter_info['right_spaces'] + 1
            min_length = max(3, 3)
            max_length = min(available_space, self.grid_size)

            for length in range(min_length, max_length + 1):
                matching_words = [
                    word for word in self.word_list
                    if len(word['solution']) == length and
                       letter_info['letter'] in word['solution']
                ]

                for word in matching_words:
                    intersection_index = word['solution'].index(letter_info['letter'])
                    start_col = letter_info['col'] - intersection_index

                    if self.place_word(word, letter_info['row'], start_col):
                        return True

        return False

    def find_free_letters_in_vertical_word(self, vertical_word):
        """
        Trova lettere utilizzabili per intersezioni nella parola verticale.
        """
        free_letters = []
        for i, letter in enumerate(vertical_word.text):
            row = vertical_word.y + i
            col = vertical_word.x

            left_spaces = 0
            for j in range(col - 1, -1, -1):
                if (self.grid[row][j] == '_' and
                        self.grid[row - 1][j] == '_' and
                        self.grid[row + 1][j] == '_'):
                    left_spaces += 1
                else:
                    break

            right_spaces = 0
            for j in range(col + 1, self.grid_size):
                if (self.grid[row][j] == '_' and
                        self.grid[row - 1][j] == '_' and
                        self.grid[row + 1][j] == '_'):
                    right_spaces += 1
                else:
                    break

            if left_spaces > 0 and right_spaces > 0:
                total_spaces = min(left_spaces + right_spaces,
                                   len(self.placed_words[0].text))

                if total_spaces >= 3:
                    other_letters = [
                        (j, self.grid[row][j])
                        for j in range(self.grid_size)
                        if j != col and self.grid[row][j] != '_'
                    ]
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

    def reset_grid(self):
        """
        Resetta la griglia e le parole piazzate.
        """
        self.grid = [['_' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.placed_words = []
        logging.info("Grid reset")

    def generate_crossword(self):
        """
        Genera il cruciverba completo con esattamente 5 parole.
        """
        attempts = 0
        while attempts < self.max_attempts:
            try:
                logging.info(f"Starting attempt {attempts + 1}")
                self.reset_grid()

                # Sequenza fissa di 5 posizionamenti
                placement_sequence = [
                    self.place_first_word,    # Prima parola al centro
                    self.place_second_word,   # Seconda parola che interseca la prima
                    self.place_third_word,    # Terza parola che interseca la prima
                    self.place_fourth_word,   # Quarta parola che collega seconda e terza
                    self.place_fifth_word     # Quinta parola nella terza parola
                ]

                success = True
                for i, place_func in enumerate(placement_sequence, 1):
                    if not place_func():
                        logging.warning(f"Failed to place word {i}")
                        success = False
                        break

                if success:
                    logging.info("Successfully generated crossword with 5 words")
                    return self.format_result()

            except Exception as e:
                logging.error(f"Error during attempt {attempts + 1}: {str(e)}")

            attempts += 1

        logging.error("Failed to generate crossword after all attempts")
        return "Unable to generate crossword after multiple attempts"

    def optimize_grid(self):
        """
        Rimuove le righe e colonne vuote dalla griglia e aggiorna le coordinate delle parole.
        Restituisce una nuova griglia ottimizzata e aggiorna le coordinate delle parole piazzate.
        """
        # Trova le righe e colonne non vuote
        non_empty_rows = self._get_non_empty_rows()
        non_empty_cols = self._get_non_empty_cols()

        if not non_empty_rows or not non_empty_cols:
            logging.warning("No non-empty rows or columns found")
            return

        # Crea la nuova griglia con solo le righe/colonne non vuote
        new_grid = self._create_optimized_grid(non_empty_rows, non_empty_cols)

        # Crea il mapping delle vecchie coordinate alle nuove
        row_mapping = self._create_coordinate_mapping(non_empty_rows)
        col_mapping = self._create_coordinate_mapping(non_empty_cols)

        # Aggiorna le coordinate delle parole
        self._update_word_coordinates(row_mapping, col_mapping)

        # Aggiorna la griglia e le dimensioni
        self.grid = new_grid
        self.grid_size = len(new_grid)

        logging.info(f"Grid optimized: new size {self.grid_size}x{self.grid_size}")

    def _get_non_empty_rows(self):
        """
        Trova gli indici delle righe che contengono almeno una lettera.
        """
        return [i for i, row in enumerate(self.grid)
                if any(cell != '_' for cell in row)]

    def _get_non_empty_cols(self):
        """
        Trova gli indici delle colonne che contengono almeno una lettera.
        """
        return [j for j in range(len(self.grid[0]))
                if any(self.grid[i][j] != '_' for i in range(len(self.grid)))]

    def _create_optimized_grid(self, non_empty_rows, non_empty_cols):
        """
        Crea una nuova griglia contenente solo le righe e colonne non vuote.
        """
        return [[self.grid[i][j] for j in non_empty_cols]
                for i in non_empty_rows]

    def _create_coordinate_mapping(self, non_empty_indices):
        """
        Crea un dizionario che mappa le vecchie coordinate alle nuove.
        """
        return {old_idx: new_idx
                for new_idx, old_idx in enumerate(non_empty_indices)}

    def _update_word_coordinates(self, row_mapping, col_mapping):
        """
        Aggiorna le coordinate delle parole piazzate in base alla nuova griglia.
        """
        for word in self.placed_words:
            word.x = col_mapping[word.x]
            word.y = row_mapping[word.y]

    def save_to_json(self):
        """
        Salva il cruciverba in formato JSON con tutte le informazioni necessarie
        per la ricostruzione.
        """
        crossword_data = {
            'metadata': {
                'guid': str(self.guid),
                'timestamp': self.timestamp,
                'grid_size': self.grid_size,
                'cell_size': self.cell_size
            },
            'grid': self.grid,
            'words': [word.to_dict() for word in self.placed_words]
        }

        json_file = os.path.join(self.output_dir, 'crossword.json')
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(crossword_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Crossword saved to JSON: {json_file}")
        except Exception as e:
            logging.error(f"Error saving JSON file: {str(e)}")
            raise

    def format_result(self):
        """
        Formatta il risultato del cruciverba.
        """
        self.optimize_grid()
        self.print_crossword()
        self.print_placed_words()
        self.save_to_file()
        self.save_to_json()  # Aggiungi il salvataggio JSON
        return "Crossword generated successfully"

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

    def print_placed_words(self):
        """
        Stampa le parole posizionate con le informazioni aggiuntive.
        """
        print("\nParole posizionate:")
        for i, word in enumerate(self.placed_words, 1):
            direction = "Orizzontale" if word.is_horizontal else "Verticale"
            print(f"{i}. Parola: {word.text}")
            print(f"   Posizione: ({word.x}, {word.y})")
            print(f"   Direzione: {direction}")
            print(f"   Definizione: {word.clue}")
            print(f"   Pattern: {word.word_pattern}")
            print(f"   Num. Parole: {word.num_words}\n")

    def save_to_file(self):
        """
        Salva il cruciverba generato su file.
        """
        output_file = os.path.join(self.output_dir, 'crossword.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            # Salva la griglia
            f.write("Griglia del cruciverba:\n\n")
            for row in self.grid:
                f.write(' '.join(cell for cell in row) + '\n')

            # Salva le definizioni
            f.write("\nDefinizioni:\n\n")
            for i, word in enumerate(self.placed_words, 1):
                direction = "Orizzontale" if word.is_horizontal else "Verticale"
                f.write(f"{i}. {word.text} ({direction})\n")
                f.write(f"   Definizione: {word.clue}\n")
                f.write(f"   Coordinate: ({word.x}, {word.y})\n\n")

        logging.info(f"Crossword saved to {output_file}")

def main():
    """
    Funzione principale per l'esecuzione del generatore di cruciverba.
    """
    db_config = {
        'user': 'crossword',
        'password': 'crossword',
        'host': 'localhost',
        'database': 'crossword'
    }

    try:
        generator = CrosswordGenerator(
            grid_size=15,
            cell_size=75,
            db_config=db_config,
            max_attempts=3
        )

        result = generator.generate_crossword()
        print(result)

    except Exception as e:
        print(f"Errore durante la generazione del cruciverba: {str(e)}")
        logging.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()
