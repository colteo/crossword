from abc import ABC, abstractmethod
import os
import uuid
from datetime import datetime
import random
import json
import mysql.connector
import logging
from utils.grid_utils import GridUtils
from utils.db_utils import DatabaseUtils
from base.word import Word


class BaseCrosswordGenerator(ABC):
    """Classe base astratta per il generatore di cruciverba."""
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
            self.word_list = DatabaseUtils.get_word_list_from_db(db_config, grid_size)
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

    def can_place_word(self, word, start_row, start_col, vertical=False):
        return GridUtils.can_place_word(self.grid, word, start_row, start_col, vertical, self.grid_size)

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

    def reset_grid(self):
        """
        Resetta la griglia e le parole piazzate.
        """
        self.grid = [['_' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.placed_words = []
        logging.info("Grid reset")

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

    def optimize_grid(self):
        non_empty_rows = GridUtils.get_non_empty_rows(self.grid)
        non_empty_cols = GridUtils.get_non_empty_cols(self.grid)

        if not non_empty_rows or not non_empty_cols:
            logging.warning("No non-empty rows or columns found")
            return

        new_grid = GridUtils.create_optimized_grid(self.grid, non_empty_rows, non_empty_cols)
        row_mapping = GridUtils.create_coordinate_mapping(non_empty_rows)
        col_mapping = GridUtils.create_coordinate_mapping(non_empty_cols)

        self._update_word_coordinates(row_mapping, col_mapping)
        self.grid = new_grid
        self.grid_size = len(new_grid)

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

    @abstractmethod
    def generate_crossword(self) -> str:
        """
        Genera il cruciverba. Da implementare nelle sottoclassi.
        """
        pass

