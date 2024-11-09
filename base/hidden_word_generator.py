from abc import ABC, abstractmethod
from base.base_generator import BaseCrosswordGenerator
from typing import List, Dict, Tuple, Optional
import logging
import random
import json
import os


class HiddenWordGenerator(BaseCrosswordGenerator):
    """Classe base per i cruciverba con parola nascosta."""
    def __init__(self, grid_size=15, cell_size=75, db_config=None, max_attempts=3):
        super().__init__(grid_size, cell_size, db_config, max_attempts)
        self.key_column = None
        self.hidden_word = None
        self.min_word_length = 5
        self.max_word_length = 8
        self.min_words = 5
        self.max_words = 12

    @abstractmethod
    def set_hidden_word(self, word_length: int) -> bool:
        """Imposta la parola nascosta. Da implementare nelle sottoclassi."""
        pass

    @abstractmethod
    def find_intersecting_word(self, row: int, letter: str) -> Optional[Tuple[Dict, int]]:
        """Trova una parola che interseca. Da implementare nelle sottoclassi."""
        pass

    def print_crossword(self):
        """
        Stampa la griglia del cruciverba evidenziando la colonna della parola nascosta.
        """
        # Stampa i numeri di colonna con la colonna chiave evidenziata
        col_headers = []
        for i in range(self.grid_size):
            if i == self.key_column:
                col_headers.append(f'*{i:2d}*')
            else:
                col_headers.append(f' {i:2d} ')
        print('   ' + ' '.join(col_headers))

        # Stampa una linea separatrice
        separator = '  ' + '-' * (self.grid_size * 4 + 1)
        print(separator)

        # Stampa ogni riga con la colonna chiave evidenziata
        for i, row in enumerate(self.grid):
            row_cells = []
            for j, cell in enumerate(row):
                if j == self.key_column:
                    row_cells.append(f'|{cell}|')
                else:
                    row_cells.append(f' {cell} ')
            print(f'{i:2d}|{"|".join(row_cells)}|')

        print(separator)

    def print_placed_words(self):
        """
        Stampa le parole posizionate raggruppate per tipo (nascosta/intersecanti).
        """
        print("\nParola Nascosta:")
        print(f"Colonna: {self.key_column}")
        print(f"Parola: {self.hidden_word}\n")

        print("Parole Intersecanti:")
        for i, word in enumerate(self.placed_words, 1):
            intersection_point = self.key_column - word.x
            intersection_letter = word.text[intersection_point]

            print(f"{i}. Parola: {word.text}")
            print(f"   Posizione: ({word.x}, {word.y})")
            print(f"   Direzione: Orizzontale")
            print(f"   Punto di intersezione: posizione {intersection_point + 1}, lettera '{intersection_letter}'")
            print(f"   Definizione: {word.clue}")
            print(f"   Pattern: {word.word_pattern}")
            print(f"   Num. Parole: {word.num_words}\n")

    def save_to_file(self):
        """
        Salva il cruciverba su file con informazioni specifiche per il tipo hidden word.
        """
        output_file = os.path.join(self.output_dir, 'crossword.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("CRUCIVERBA CON PAROLA NASCOSTA\n")
            f.write("==============================\n\n")

            f.write("Griglia del cruciverba:\n")
            f.write(f"(La colonna {self.key_column} contiene la parola nascosta)\n\n")

            for row in self.grid:
                row_str = ""
                for j, cell in enumerate(row):
                    if j == self.key_column:
                        row_str += f"|{cell}|"
                    else:
                        row_str += f" {cell} "
                f.write(row_str + "\n")

            f.write("\nParola Nascosta:\n")
            f.write(f"Colonna: {self.key_column}\n")
            f.write(f"Parola: {self.hidden_word}\n")

            f.write("\nParole Intersecanti:\n")
            for i, word in enumerate(self.placed_words, 1):
                intersection_point = self.key_column - word.x
                intersection_letter = word.text[intersection_point]

                f.write(f"\n{i}. {word.text}\n")
                f.write(f"   Definizione: {word.clue}\n")
                f.write(f"   Coordinate: ({word.x}, {word.y})\n")
                f.write(f"   Intersezione: pos. {intersection_point + 1}, lettera '{intersection_letter}'\n")

        logging.info(f"Crossword saved to {output_file}")

    def save_to_json(self):
        """
        Salva il cruciverba in formato JSON con informazioni specifiche per il tipo hidden word.
        """
        crossword_data = {
            'crossword_data': {
                'metadata': {
                    'guid': str(self.guid),
                    'timestamp': self.timestamp,
                    'grid_size': self.grid_size,
                    'cell_size': self.cell_size
                },
                'crossword_type': self.get_crossword_type(),
                'hidden_word': {
                    'word': self.hidden_word,
                    'column': self.key_column
                },
                'grid': self.grid,
                'words': [{
                    **word.to_dict(),
                    'intersection': {
                        'position': self.key_column - word.x,
                        'letter': word.text[self.key_column - word.x]
                    }
                } for word in self.placed_words]
            }
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
        Formatta il risultato del cruciverba con parola nascosta.
        """
        self.optimize_grid()
        self.print_crossword()
        self.print_placed_words()
        self.save_to_file()
        self.save_to_json()
        return "Crossword generated successfully"

    def optimize_grid(self):
        """
        Override del metodo di ottimizzazione della griglia per mantenere traccia
        della colonna della parola nascosta.
        """
        # Prima ottieni gli indici di righe e colonne non vuote
        non_empty_rows = self._get_non_empty_rows()
        non_empty_cols = self._get_non_empty_cols()

        if not non_empty_rows or not non_empty_cols:
            return

        # Crea la nuova griglia ottimizzata
        new_grid = self._create_optimized_grid(non_empty_rows, non_empty_cols)

        # Crea il mapping delle coordinate
        row_mapping = self._create_coordinate_mapping(non_empty_rows)
        col_mapping = self._create_coordinate_mapping(non_empty_cols)

        # Aggiorna le coordinate delle parole
        self._update_word_coordinates(row_mapping, col_mapping)

        # IMPORTANTE: Aggiorna la posizione della colonna della parola nascosta
        self.key_column = col_mapping[self.key_column]

        # Assegna la nuova griglia ottimizzata
        self.grid = new_grid
        self.grid_size = len(new_grid)

        logging.info(
            f"Grid optimized. New size: {self.grid_size}x{self.grid_size}. Hidden word column: {self.key_column}")

    def _update_word_coordinates(self, row_mapping, col_mapping):
        """
        Aggiorna le coordinate delle parole dopo l'ottimizzazione della griglia.
        """
        for word in self.placed_words:
            word.x = col_mapping[word.x]
            word.y = row_mapping[word.y]

    def generate_crossword(self) -> str:
        """
        Genera il cruciverba con parola nascosta.
        """
        attempts = 0
        while attempts < self.max_attempts:
            try:
                self.reset_grid()

                hidden_word_length = random.randint(self.min_word_length, self.max_word_length)
                if not self.set_hidden_word(hidden_word_length):
                    attempts += 1
                    continue

                num_words = random.randint(self.min_words, self.max_words)
                words_placed = 0

                for row, letter in enumerate(self.hidden_word):
                    word_result = self.find_intersecting_word(row, letter)
                    if word_result:
                        word_info, start_col = word_result
                        if self.place_word(word_info, row, start_col, vertical=False):
                            words_placed += 1

                if words_placed >= self.min_words:
                    return self.format_result()

            except Exception as e:
                logging.error(f"Error during generation: {str(e)}")

            attempts += 1

        return "Unable to generate crossword after multiple attempts"

