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
        Posiziona la seconda parola in modo che la sua ultima lettera intersechi
        la prima lettera della prima parola. La seconda parola sarà verticale.
        """
        first_word = self.placed_words[0]
        first_letter = first_word.text[0]  # Prima lettera della prima parola

        # Cerca una parola che finisce con la lettera necessaria
        matching_words = []
        min_length = 4  # Lunghezza minima della seconda parola
        max_length = min(10, first_word.y)  # Non deve superare il bordo superiore

        for word in self.word_list:
            if (min_length <= len(word['solution']) <= max_length and
                    word['solution'][-1] == first_letter):
                matching_words.append(word)

        if not matching_words:
            logging.warning("No suitable word found for second position")
            return False

        # Sceglie una parola casuale tra quelle trovate
        second_word = random.choice(matching_words)
        word_length = len(second_word['solution'])

        # Calcola la posizione iniziale
        start_row = first_word.y - (word_length - 1)  # Sottrae 1 perché l'ultima lettera deve intersecare
        start_col = first_word.x

        # Verifica se la posizione è valida
        if start_row < 0:
            logging.warning("Word too long for available space")
            return False

        # Tenta di posizionare la parola
        return self.place_word(second_word, start_row, start_col, vertical=True)

    def place_third_word(self):
        """
        Posiziona la terza parola verticalmente, intersecando la prima parola circa a metà.
        La parola deve avere una lunghezza tra 6 e 10 lettere e l'intersezione deve avvenire
        nelle prime tre posizioni della terza parola.
        """
        first_word = self.placed_words[0]

        # Calcola il punto di intersezione sulla prima parola (circa a metà)
        intersection_index = len(first_word.text) // 2
        intersection_letter = first_word.text[intersection_index]

        # Cerca parole adatte (lunghezza 6-10) che hanno la lettera di intersezione
        # in una delle prime tre posizioni
        matching_words = []

        for word in self.word_list:
            word_length = len(word['solution'])
            if 6 <= word_length <= 10:
                # Controlla se la lettera di intersezione appare nelle prime tre posizioni
                for pos in range(min(3, word_length)):
                    if word['solution'][pos] == intersection_letter:
                        matching_words.append((word, pos))

        if not matching_words:
            logging.warning("No suitable word found for third position")
            return False

        # Prova a posizionare una delle parole trovate
        random.shuffle(matching_words)  # Randomizza l'ordine per varietà

        for word_info, intersection_pos in matching_words:
            # Calcola la posizione di partenza
            start_row = first_word.y - intersection_pos
            start_col = first_word.x + intersection_index

            # Verifica che la parola non esca dalla griglia
            word_length = len(word_info['solution'])
            if (start_row >= 0 and
                    start_row + word_length <= self.grid_size and
                    start_col >= 0 and
                    start_col < self.grid_size):

                # Tenta di posizionare la parola
                if self.place_word(word_info, start_row, start_col, vertical=True):
                    logging.info(f"Third word placed: {word_info['solution']} at ({start_row}, {start_col})")
                    return True

        logging.warning("Could not place any matching word in third position")
        return False

    def place_fourth_word(self):
        """
        Posiziona la quarta parola verticalmente, intersecando la prima parola nella sua ultima posizione.
        La parola deve avere una lunghezza tra 6 e 10 lettere e l'intersezione deve avvenire
        nelle prime tre posizioni della quarta parola.
        """
        first_word = self.placed_words[0]

        # Calcola il punto di intersezione sulla prima parola (ultima lettera)
        intersection_index = len(first_word.text) - 1
        intersection_letter = first_word.text[intersection_index]

        # Cerca parole adatte (lunghezza 6-10) che hanno la lettera di intersezione
        # in una delle prime tre posizioni
        matching_words = []

        for word in self.word_list:
            word_length = len(word['solution'])
            if 6 <= word_length <= 10:
                # Controlla se la lettera di intersezione appare nelle prime tre posizioni
                for pos in range(min(3, word_length)):
                    if word['solution'][pos] == intersection_letter:
                        matching_words.append((word, pos))

        if not matching_words:
            logging.warning("No suitable word found for fourth position")
            return False

        # Prova a posizionare una delle parole trovate
        random.shuffle(matching_words)  # Randomizza l'ordine per varietà

        for word_info, intersection_pos in matching_words:
            # Calcola la posizione di partenza
            start_row = first_word.y - intersection_pos
            start_col = first_word.x + intersection_index

            # Verifica che la parola non esca dalla griglia
            word_length = len(word_info['solution'])
            if (start_row >= 0 and
                    start_row + word_length <= self.grid_size and
                    start_col >= 0 and
                    start_col < self.grid_size):

                # Tenta di posizionare la parola
                if self.place_word(word_info, start_row, start_col, vertical=True):
                    logging.info(f"Fourth word placed: {word_info['solution']} at ({start_row}, {start_col})")
                    return True

        logging.warning("Could not place any matching word in fourth position")
        return False

    def place_fifth_word(self):
        """
        Posiziona la quinta parola orizzontalmente, intersecando sia la terza che la quarta parola.
        La parola deve essere posizionata ad almeno una riga di distanza dalla prima parola.
        """
        first_word = self.placed_words[0]
        third_word = self.placed_words[2]
        fourth_word = self.placed_words[3]

        # Trova tutte le possibili righe per il posizionamento
        min_row = first_word.y + 2  # Almeno una riga di distanza dalla prima parola
        max_row = self.grid_size - 1

        # Trova le intersezioni possibili con la terza e quarta parola
        possible_intersections = []

        for row in range(min_row, max_row + 1):
            # Trova le lettere disponibili sulla terza e quarta parola in questa riga
            third_word_letter = None
            fourth_word_letter = None
            third_word_col = None
            fourth_word_col = None

            # Controlla se la riga interseca la terza parola
            if (third_word.y <= row < third_word.y + len(third_word.text)):
                pos_in_word = row - third_word.y
                third_word_letter = third_word.text[pos_in_word]
                third_word_col = third_word.x

            # Controlla se la riga interseca la quarta parola
            if (fourth_word.y <= row < fourth_word.y + len(fourth_word.text)):
                pos_in_word = row - fourth_word.y
                fourth_word_letter = fourth_word.text[pos_in_word]
                fourth_word_col = fourth_word.x

            # Se abbiamo entrambe le intersezioni, aggiungi alla lista
            if third_word_letter and fourth_word_letter:
                possible_intersections.append({
                    'row': row,
                    'third_word': {
                        'letter': third_word_letter,
                        'col': third_word_col
                    },
                    'fourth_word': {
                        'letter': fourth_word_letter,
                        'col': fourth_word_col
                    }
                })

        # Prova ogni possibile intersezione
        random.shuffle(possible_intersections)  # Randomizza per varietà

        for intersection in possible_intersections:
            # Calcola la distanza tra le intersezioni
            distance = abs(intersection['fourth_word']['col'] - intersection['third_word']['col'])

            # Cerca parole che possano adattarsi
            matching_words = []
            for word in self.word_list:
                word_text = word['solution']
                word_length = len(word_text)

                # La parola deve essere abbastanza lunga da coprire entrambe le intersezioni
                if word_length < distance + 1:
                    continue

                # Controlla tutte le possibili posizioni della parola
                for start_col in range(max(0, intersection['third_word']['col'] - word_length + 1),
                                       min(self.grid_size - word_length + 1, intersection['third_word']['col'] + 1)):

                    # Calcola le posizioni relative nella parola
                    third_pos = intersection['third_word']['col'] - start_col
                    fourth_pos = intersection['fourth_word']['col'] - start_col

                    # Verifica se le lettere corrispondono in entrambe le posizioni
                    if (0 <= third_pos < word_length and
                            0 <= fourth_pos < word_length and
                            word_text[third_pos] == intersection['third_word']['letter'] and
                            word_text[fourth_pos] == intersection['fourth_word']['letter']):
                        matching_words.append((word, start_col))

            # Prova a posizionare una delle parole trovate
            random.shuffle(matching_words)  # Randomizza per varietà
            for word_info, start_col in matching_words:
                if self.place_word(word_info, intersection['row'], start_col, vertical=False):
                    logging.info(f"Fifth word placed: {word_info['solution']} at ({intersection['row']}, {start_col})")
                    return True

        logging.warning("Could not place fifth word")
        return False

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
                    self.place_first_word,
                    self.place_second_word,
                    self.place_third_word,
                    self.place_fourth_word,
                    self.place_fifth_word
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

    def load_from_json(self, json_file):
        """
        Carica un cruciverba da un file JSON.

        Args:
            json_file (str): Percorso del file JSON da caricare

        Returns:
            bool: True se il caricamento è avvenuto con successo, False altrimenti
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Carica i metadata
            self.guid = uuid.UUID(data['metadata']['guid'])
            self.timestamp = data['metadata']['timestamp']
            self.grid_size = data['metadata']['grid_size']
            self.cell_size = data['metadata']['cell_size']

            # Carica la griglia
            self.grid = data['grid']

            # Ricostruisci le parole
            self.placed_words = [
                Word(
                    text=word_data['text'],
                    x=word_data['x'],
                    y=word_data['y'],
                    is_horizontal=word_data['is_horizontal'],
                    clue=word_data['clue'],
                    word_pattern=word_data['word_pattern'],
                    num_words=word_data['num_words']
                )
                for word_data in data['words']
            ]

            logging.info(f"Crossword loaded from JSON: {json_file}")
            return True

        except Exception as e:
            logging.error(f"Error loading JSON file: {str(e)}")
            return False

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
