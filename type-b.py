import os
import uuid
from datetime import datetime
import random
from dataclasses import dataclass, asdict
import json
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

        # Genera un GUID per questa sessione di generazione
        self.guid = uuid.uuid4()
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        # Crea la directory di output
        self.output_dir = os.path.join("output", f"{self.timestamp}-{self.guid}")
        os.makedirs(self.output_dir, exist_ok=True)

        # Configura il logging
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
        """
        Recupera le parole dal database MySQL.
        """
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
        Posiziona la prima parola verticalmente al centro della griglia.
        """
        first_word_info = self.find_word((8, 12))
        if not first_word_info:
            logging.warning("Could not find suitable first word")
            return False

        # Calcola la posizione centrale per il posizionamento verticale
        start_col = self.grid_size // 2
        start_row = (self.grid_size - len(first_word_info['solution'])) // 2

        # Posiziona la parola verticalmente (vertical=True)
        return self.place_word(first_word_info, start_row, start_col, vertical=True)

    def place_second_word(self):
        """
        Posiziona la seconda parola orizzontalmente, intersecando la prima parola verticale.
        """
        return self.place_intersecting_word(0, 0, len(self.placed_words[0].text) // 2 - 1, vertical=False)

    def find_word_with_letter_in_range(self, length_range, letter, position_range):
        """
        Trova una parola che contiene una lettera in una delle posizioni specificate nel range.

        Args:
            length_range: tupla (min_length, max_length)
            letter: lettera da cercare
            position_range: lista di posizioni valide per la lettera
        """
        matching_words = []

        for word in self.word_list:
            # Verifica la lunghezza
            if not (length_range[0] <= len(word['solution']) <= length_range[1]):
                continue

            # Trova tutte le posizioni della lettera nella parola
            positions = [i for i, char in enumerate(word['solution']) if char == letter]

            # Verifica se almeno una posizione è nel range richiesto
            if any(pos in position_range for pos in positions):
                matching_words.append(word)

        return random.choice(matching_words) if matching_words else None

    def place_third_word(self):
        """
        Posiziona la terza parola verticalmente, intersecando la seconda parola orizzontale.
        La parola deve essere lunga 5-8 caratteri e deve intersecare la seconda parola
        nelle sue prime tre posizioni. La lettera di intersezione della terza parola
        deve trovarsi nelle prime 5 posizioni.
        """
        # Otteniamo la seconda parola
        second_word = self.placed_words[1]

        # Scegliamo un punto di intersezione nelle prime tre posizioni della seconda parola
        intersection_index_second = random.randint(0, 2)
        intersection_letter = second_word.text[intersection_index_second]

        # Cerchiamo una parola che:
        # - sia lunga 5-8 caratteri
        # - contenga la lettera di intersezione in una delle prime 5 posizioni
        new_word = self.find_word_with_letter_in_range((5, 8), intersection_letter, list(range(5)))
        if not new_word:
            logging.warning(f"Could not find suitable third word with letter {intersection_letter} "
                            f"in first 5 positions, length 5-8")
            return False

        # Troviamo tutte le possibili posizioni della lettera di intersezione nella nuova parola
        possible_positions = [i for i, char in enumerate(new_word['solution'])
                              if char == intersection_letter and i < 5]

        # Scegliamo casualmente una delle posizioni valide
        intersection_index_third = random.choice(possible_positions)

        # Calcoliamo le coordinate di posizionamento
        new_word_col = second_word.x + intersection_index_second
        new_word_start_row = second_word.y - intersection_index_third

        # Verifichiamo che la parola rimanga nei limiti della griglia
        word_length = len(new_word['solution'])
        if (new_word_start_row < 0 or
                new_word_start_row + word_length > self.grid_size or
                new_word_col < 0 or
                new_word_col >= self.grid_size):
            logging.warning(f"Third word '{new_word['solution']}' would exceed grid bounds: "
                            f"start_row={new_word_start_row}, col={new_word_col}, length={word_length}")
            return False

        # Proviamo a posizionare la parola
        return self.place_word(new_word, new_word_start_row, new_word_col, vertical=True)

    def place_intersecting_word(self, word_index, start, end, vertical=True):
        """
        Posiziona una parola che interseca una parola esistente.
        La seconda parola interseca con il suo punto centrale e viene verificato
        che rimanga all'interno della griglia.

        Args:
            word_index: indice della parola da intersecare
            start: indice iniziale per la ricerca dell'intersezione
            end: indice finale per la ricerca dell'intersezione
            vertical: True per posizionamento verticale, False per orizzontale
        """

        def is_within_grid(start_pos, word_length, max_size):
            """
            Verifica se una parola rimane all'interno dei limiti della griglia.
            """
            return 0 <= start_pos and start_pos + word_length <= max_size

        extracted_letter_index = random.randint(start, end)
        extracted_letter = self.placed_words[word_index].text[extracted_letter_index]

        # Cerchiamo una parola di lunghezza 12-14 che contenga la lettera
        new_word = self.find_word_with_letter((12, 14), extracted_letter, [6, 7])
        if not new_word:
            logging.warning(
                f"Could not find word of length 12-14 containing letter {extracted_letter} in center position")
            return False

        # Calcoliamo il centro della nuova parola
        word_length = len(new_word['solution'])
        word_center = word_length // 2

        if vertical:
            # Calcolo posizione per parola verticale
            new_word_col = self.placed_words[word_index].x + extracted_letter_index
            new_word_start_row = self.placed_words[word_index].y - word_center

            # Verifica dei limiti per posizionamento verticale
            if not is_within_grid(new_word_start_row, word_length, self.grid_size):
                logging.warning(f"Word '{new_word['solution']}' would exceed grid bounds vertically: "
                                f"start={new_word_start_row}, length={word_length}, grid_size={self.grid_size}")
                return False

            # Verifica che la colonna sia valida
            if new_word_col < 0 or new_word_col >= self.grid_size:
                logging.warning(f"Word would exceed grid bounds horizontally: column={new_word_col}")
                return False

        else:
            # Calcolo posizione per parola orizzontale
            new_word_row = self.placed_words[word_index].y + extracted_letter_index
            new_word_start_col = self.placed_words[word_index].x - word_center

            # Verifica dei limiti per posizionamento orizzontale
            if not is_within_grid(new_word_start_col, word_length, self.grid_size):
                logging.warning(f"Word '{new_word['solution']}' would exceed grid bounds horizontally: "
                                f"start={new_word_start_col}, length={word_length}, grid_size={self.grid_size}")
                return False

            # Verifica che la riga sia valida
            if new_word_row < 0 or new_word_row >= self.grid_size:
                logging.warning(f"Word would exceed grid bounds vertically: row={new_word_row}")
                return False

        # Se tutti i controlli sono passati, posiziona la parola
        if vertical:
            return self.place_word(new_word, new_word_start_row, new_word_col, vertical=True)
        else:
            return self.place_word(new_word, new_word_row, new_word_start_col, vertical=False)

    def place_fourth_word(self):
        """
        Posiziona la quarta parola verticalmente, intersecando la seconda parola orizzontale.
        La parola deve essere lunga 5-8 caratteri e deve intersecare la seconda parola
        nelle sue ultime tre posizioni. La lettera di intersezione della quarta parola
        deve trovarsi nelle prime 3 posizioni.
        """
        # Otteniamo la seconda parola
        second_word = self.placed_words[1]

        # Calcoliamo le ultime tre posizioni della seconda parola
        word_length = len(second_word.text)
        last_positions = range(word_length - 3, word_length)

        # Scegliamo un punto di intersezione nelle ultime tre posizioni della seconda parola
        intersection_index_second = random.choice(list(last_positions))
        intersection_letter = second_word.text[intersection_index_second]

        # Cerchiamo una parola che:
        # - sia lunga 5-8 caratteri
        # - contenga la lettera di intersezione in una delle prime 3 posizioni
        new_word = self.find_word_with_letter_in_range((5, 8), intersection_letter, list(range(3)))
        if not new_word:
            logging.warning(f"Could not find suitable fourth word with letter {intersection_letter} "
                            f"in first 3 positions, length 5-8")
            return False

        # Troviamo tutte le possibili posizioni della lettera di intersezione nella nuova parola
        # (solo nelle prime 3 posizioni)
        possible_positions = [i for i, char in enumerate(new_word['solution'])
                              if char == intersection_letter and i < 3]

        # Scegliamo casualmente una delle posizioni valide
        intersection_index_fourth = random.choice(possible_positions)

        # Calcoliamo le coordinate di posizionamento
        new_word_col = second_word.x + intersection_index_second
        new_word_start_row = second_word.y - intersection_index_fourth

        # Verifichiamo che la parola rimanga nei limiti della griglia
        word_length = len(new_word['solution'])
        if (new_word_start_row < 0 or
                new_word_start_row + word_length > self.grid_size or
                new_word_col < 0 or
                new_word_col >= self.grid_size):
            logging.warning(f"Fourth word '{new_word['solution']}' would exceed grid bounds: "
                            f"start_row={new_word_start_row}, col={new_word_col}, length={word_length}")
            return False

        # Verifichiamo che non ci siano sovrapposizioni con altre parole
        # (oltre al punto di intersezione con la seconda parola)
        if not self.can_place_word(new_word['solution'], new_word_start_row, new_word_col, vertical=True):
            logging.warning(f"Fourth word '{new_word['solution']}' would overlap with existing words")
            return False

        # Proviamo a posizionare la parola
        return self.place_word(new_word, new_word_start_row, new_word_col, vertical=True)

    def reset_grid(self):
        """
        Resetta la griglia e le parole piazzate.
        """
        self.grid = [['_' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.placed_words = []
        logging.info("Grid reset")

    def generate_crossword(self):
        """
        Genera il cruciverba completo.
        """
        attempts = 0
        while attempts < self.max_attempts:
            try:
                logging.info(f"Starting attempt {attempts + 1}")
                self.reset_grid()

                # Sequenza fissa di posizionamento delle parole
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
                    logging.info(f"Successfully placed word {i}")

                if success:
                    logging.info("Successfully generated crossword")
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

    def place_fifth_word(self):
        """
        Posiziona la quinta parola orizzontalmente, intersecando la prima e la quarta parola.

        Criteri di ricerca:
        1. Lunghezza: 8-12 caratteri
        2. Deve essere almeno una riga sopra o sotto la seconda parola
        3. La prima intersezione deve essere nelle prime 4 posizioni della parola
        4. La seconda intersezione deve essere nelle ultime 4 posizioni della parola
        5. Le intersezioni devono essere distanti almeno 4 caratteri tra loro

        Returns:
            bool: True se il posizionamento ha successo, False altrimenti
        """
        # Otteniamo le parole rilevanti
        first_word = self.placed_words[0]  # verticale
        second_word = self.placed_words[1]  # orizzontale
        fourth_word = self.placed_words[3]  # verticale

        # Verifichiamo che abbiamo tutte le parole necessarie
        if len(self.placed_words) < 4:
            logging.warning("Non ci sono abbastanza parole posizionate per aggiungere la quinta")
            return False

        # Troviamo le possibili righe per la quinta parola
        possible_rows = []
        second_word_row = second_word.y

        # Controlliamo le righe sopra la seconda parola (minimo 1 riga di distanza)
        for row in range(0, second_word_row - 1):
            possible_rows.append(row)

        # Controlliamo le righe sotto la seconda parola (minimo 1 riga di distanza)
        for row in range(second_word_row + 2, self.grid_size):
            possible_rows.append(row)

        # Per ogni riga possibile, analizziamo le potenziali intersezioni
        for row in possible_rows:
            # Troviamo le lettere e le posizioni di intersezione
            first_intersection_col = first_word.x
            first_intersection_row_pos = row - first_word.y

            fourth_intersection_col = fourth_word.x
            fourth_intersection_row_pos = row - fourth_word.y

            # Verifichiamo che le intersezioni cadano all'interno delle parole verticali
            if not (0 <= first_intersection_row_pos < len(first_word.text) and
                    0 <= fourth_intersection_row_pos < len(fourth_word.text)):
                continue

            first_intersection_letter = first_word.text[first_intersection_row_pos]
            fourth_intersection_letter = fourth_word.text[fourth_intersection_row_pos]

            # Calcoliamo la distanza tra le intersezioni
            distance = abs(fourth_intersection_col - first_intersection_col)

            # Verifichiamo che la distanza sia sufficiente (minimo 4 caratteri)
            if distance < 4:
                logging.debug(f"Distanza tra intersezioni troppo piccola: {distance}")
                continue

            # Per ogni possibile lunghezza della parola (8-12 caratteri)
            for word_length in range(8, 13):
                # La parola deve essere abbastanza lunga da coprire entrambe le intersezioni
                if word_length <= distance:
                    continue

                # Calcoliamo le possibili posizioni di inizio della parola
                max_start_shift = min(3, first_intersection_col)  # massimo 3 caratteri prima della prima intersezione

                for start_shift in range(max_start_shift + 1):
                    start_col = first_intersection_col - start_shift

                    # Verifichiamo che la parola rimanga nei limiti della griglia
                    if start_col + word_length > self.grid_size:
                        continue

                    # Creiamo il pattern per la ricerca della parola
                    pattern = ['_'] * word_length
                    first_pos = start_shift
                    fourth_pos = fourth_intersection_col - start_col

                    # Verifichiamo che le posizioni delle intersezioni rispettino i criteri
                    if not (0 <= first_pos < 4 and word_length - 4 <= fourth_pos < word_length):
                        continue

                    pattern[first_pos] = first_intersection_letter
                    pattern[fourth_pos] = fourth_intersection_letter

                    # Cerchiamo una parola che soddisfi il pattern
                    word = self.find_word_with_specific_pattern(
                        min_length=word_length,
                        max_length=word_length,
                        pattern=''.join(pattern)
                    )

                    if word:
                        # Verifichiamo che il posizionamento sia valido
                        if self.can_place_word(word['solution'], row, start_col, vertical=False):
                            # Posizioniamo la parola
                            if self.place_word(word, row, start_col, vertical=False):
                                logging.info(
                                    f"Quinta parola posizionata con successo: {word['solution']} "
                                    f"alla riga {row}, colonna {start_col}"
                                )
                                return True

        logging.warning("Impossibile trovare una posizione valida per la quinta parola")
        return False

    def find_word_with_specific_pattern(self, min_length, max_length, pattern):
        """
        Cerca una parola che soddisfi un pattern specifico e i criteri di lunghezza.

        Args:
            min_length (int): Lunghezza minima della parola
            max_length (int): Lunghezza massima della parola
            pattern (str): Pattern da rispettare ('_' per qualsiasi carattere)

        Returns:
            dict: Informazioni sulla parola trovata o None se non trovata
        """
        matching_words = []

        for word in self.word_list:
            # Verifica la lunghezza
            if not (min_length <= len(word['solution']) <= max_length):
                continue

            # Verifica il pattern
            if len(word['solution']) != len(pattern):
                continue

            # Verifica che tutte le lettere specificate nel pattern corrispondano
            if all(p == '_' or p == w for p, w in zip(pattern, word['solution'])):
                matching_words.append(word)

        return random.choice(matching_words) if matching_words else None

def main():
    """
    Funzione principale per l'esecuzione del generatore di cruciverba.
    """
    # Configurazione del database
    db_config = {
        'user': 'crossword',
        'password': 'crossword',
        'host': 'localhost',
        'database': 'crossword'
    }

    try:
        # Creazione del generatore
        generator = CrosswordGenerator(
            grid_size=15,
            cell_size=75,
            db_config=db_config,
            max_attempts=3
        )

        # Genera il cruciverba
        result = generator.generate_crossword()
        print(result)

    except Exception as e:
        print(f"Errore durante la generazione del cruciverba: {str(e)}")
        logging.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()