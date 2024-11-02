from typing import List, Dict, Tuple, Optional
import random
import logging
from base.puzzle_generator import PuzzleCrosswordGenerator


class TypeCCrossword(PuzzleCrosswordGenerator):
    """
    Implementazione del generatore di cruciverba con strategia mista.
    Utilizza una combinazione di posizionamenti orizzontali e verticali
    con vincoli specifici per le intersezioni.
    """

    def place_first_word(self) -> bool:
        """
        Posiziona la prima parola al centro della griglia orizzontalmente.
        """
        first_word_info = self.find_word((8, 12))
        if not first_word_info:
            logging.warning("Could not find suitable first word")
            return False

        start_row = self.grid_size // 2
        start_col = (self.grid_size - len(first_word_info['solution'])) // 2
        return self.place_word(first_word_info, start_row, start_col)

    def place_second_word(self) -> bool:
        """
        Posiziona la seconda parola verticalmente, in modo che la sua ultima lettera
        intersechi la prima lettera della prima parola.
        """
        first_word = self.placed_words[0]
        first_letter = first_word.text[0]

        # Cerca una parola che finisce con la lettera necessaria
        matching_words = []
        min_length = 4
        max_length = min(10, first_word.y)

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
        start_row = first_word.y - (word_length - 1)
        start_col = first_word.x

        if start_row < 0:
            logging.warning("Word too long for available space")
            return False

        return self.place_word(second_word, start_row, start_col, vertical=True)

    def place_third_word(self) -> bool:
        """
        Posiziona la terza parola verticalmente, intersecando la prima parola circa a metà.
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
        random.shuffle(matching_words)

        for word_info, intersection_pos in matching_words:
            start_row = first_word.y - intersection_pos
            start_col = first_word.x + intersection_index

            word_length = len(word_info['solution'])
            if (start_row >= 0 and
                    start_row + word_length <= self.grid_size and
                    start_col >= 0 and
                    start_col < self.grid_size):

                if self.place_word(word_info, start_row, start_col, vertical=True):
                    return True

        return False

    def place_fourth_word(self) -> bool:
        """
        Posiziona la quarta parola verticalmente, intersecando la prima parola
        nella sua ultima posizione.
        """
        first_word = self.placed_words[0]

        intersection_index = len(first_word.text) - 1
        intersection_letter = first_word.text[intersection_index]

        matching_words = []

        for word in self.word_list:
            word_length = len(word['solution'])
            if 6 <= word_length <= 10:
                for pos in range(min(3, word_length)):
                    if word['solution'][pos] == intersection_letter:
                        matching_words.append((word, pos))

        if not matching_words:
            logging.warning("No suitable word found for fourth position")
            return False

        random.shuffle(matching_words)

        for word_info, intersection_pos in matching_words:
            start_row = first_word.y - intersection_pos
            start_col = first_word.x + intersection_index

            word_length = len(word_info['solution'])
            if (start_row >= 0 and
                    start_row + word_length <= self.grid_size and
                    start_col >= 0 and
                    start_col < self.grid_size):

                if self.place_word(word_info, start_row, start_col, vertical=True):
                    return True

        return False

    def place_fifth_word(self) -> bool:
        """
        Posiziona la quinta parola orizzontalmente, intersecando sia la terza che la quarta parola.
        """
        first_word = self.placed_words[0]
        third_word = self.placed_words[2]
        fourth_word = self.placed_words[3]

        # Trova tutte le possibili righe per il posizionamento
        min_row = first_word.y + 2  # Almeno una riga di distanza dalla prima parola
        max_row = self.grid_size - 1

        # Trova le intersezioni possibili
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

            # Se abbiamo entrambe le intersezioni, cerca una parola adatta
            if third_word_letter and fourth_word_letter:
                matching_words = []
                distance = abs(fourth_word_col - third_word_col)

                for word in self.word_list:
                    word_text = word['solution']
                    word_length = len(word_text)

                    # La parola deve essere abbastanza lunga da coprire entrambe le intersezioni
                    if word_length < distance + 1:
                        continue

                    # Controlla tutte le possibili posizioni della parola
                    for start_col in range(max(0, third_word_col - word_length + 1),
                                           min(self.grid_size - word_length + 1, third_word_col + 1)):

                        # Calcola le posizioni relative nella parola
                        third_pos = third_word_col - start_col
                        fourth_pos = fourth_word_col - start_col

                        # Verifica se le lettere corrispondono in entrambe le posizioni
                        if (0 <= third_pos < word_length and
                                0 <= fourth_pos < word_length and
                                word_text[third_pos] == third_word_letter and
                                word_text[fourth_pos] == fourth_word_letter):
                            matching_words.append((word, start_col))

                # Prova a posizionare una delle parole trovate
                random.shuffle(matching_words)
                for word_info, start_col in matching_words:
                    if self.place_word(word_info, row, start_col, vertical=False):
                        return True

        return False

    def find_word_with_letter(self, length_range: Tuple[int, int],
                              letter: str,
                              positions: List[int]) -> Optional[Dict]:
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