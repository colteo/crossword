# generators/type_b.py

from typing import List, Dict, Tuple, Optional
import random
import logging
from base.base_generator import BaseCrosswordGenerator


class TypeBCrossword(BaseCrosswordGenerator):
    """
    Implementazione del generatore di cruciverba con strategia verticale centrica.
    La prima parola viene posizionata verticalmente al centro della griglia.
    """

    def place_first_word(self) -> bool:
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

        # Posiziona la parola verticalmente
        return self.place_word(first_word_info, start_row, start_col, vertical=True)

    def place_second_word(self) -> bool:
        """
        Posiziona la seconda parola orizzontalmente, intersecando la prima parola verticale.
        """
        return self.place_intersecting_word(0, 0, len(self.placed_words[0].text) // 2 - 1, vertical=False)

    def place_third_word(self) -> bool:
        """
        Posiziona la terza parola verticalmente, intersecando la seconda parola orizzontale.
        """
        # Otteniamo la seconda parola
        second_word = self.placed_words[1]

        # Scegliamo un punto di intersezione nelle prime tre posizioni della seconda parola
        intersection_index_second = random.randint(0, 2)
        intersection_letter = second_word.text[intersection_index_second]

        # Cerchiamo una parola che contenga la lettera di intersezione in una delle prime 5 posizioni
        new_word = self.find_word_with_letter_in_range((5, 8), intersection_letter, list(range(5)))
        if not new_word:
            logging.warning(f"Could not find suitable third word with letter {intersection_letter}")
            return False

        # Troviamo tutte le possibili posizioni della lettera di intersezione nella nuova parola
        possible_positions = [i for i, char in enumerate(new_word['solution'])
                              if char == intersection_letter and i < 5]

        # Scegliamo casualmente una delle posizioni valide
        intersection_index_third = random.choice(possible_positions)

        # Calcoliamo le coordinate di posizionamento
        new_word_col = second_word.x + intersection_index_second
        new_word_start_row = second_word.y - intersection_index_third

        return self.place_word(new_word, new_word_start_row, new_word_col, vertical=True)

    def place_fourth_word(self) -> bool:
        """
        Posiziona la quarta parola verticalmente, intersecando la seconda parola.
        """
        # Otteniamo la seconda parola
        second_word = self.placed_words[1]

        # Calcoliamo le ultime tre posizioni della seconda parola
        word_length = len(second_word.text)
        last_positions = range(word_length - 3, word_length)

        # Scegliamo un punto di intersezione nelle ultime tre posizioni
        intersection_index_second = random.choice(list(last_positions))
        intersection_letter = second_word.text[intersection_index_second]

        # Cerchiamo una parola che contenga la lettera di intersezione in una delle prime 3 posizioni
        new_word = self.find_word_with_letter_in_range((5, 8), intersection_letter, list(range(3)))
        if not new_word:
            logging.warning(f"Could not find suitable fourth word with letter {intersection_letter}")
            return False

        # Troviamo le posizioni valide per l'intersezione
        possible_positions = [i for i, char in enumerate(new_word['solution'])
                              if char == intersection_letter and i < 3]

        intersection_index_fourth = random.choice(possible_positions)

        # Calcoliamo le coordinate di posizionamento
        new_word_col = second_word.x + intersection_index_second
        new_word_start_row = second_word.y - intersection_index_fourth

        return self.place_word(new_word, new_word_start_row, new_word_col, vertical=True)

    def place_fifth_word(self) -> bool:
        """
        Posiziona la quinta parola orizzontalmente, intersecando la prima e la quarta parola.
        Mantiene una distanza minima di una riga dalla seconda parola orizzontale.
        """
        first_word = self.placed_words[0]
        second_word = self.placed_words[1]  # la parola orizzontale esistente
        fourth_word = self.placed_words[3]

        # Calcola la zona di sicurezza intorno alla seconda parola
        safety_zone_start = second_word.y - 1  # una riga sopra
        safety_zone_end = second_word.y + 1  # una riga sotto

        # Trova le possibili righe per la quinta parola
        min_row = first_word.y + 2  # Almeno una riga di distanza dalla prima parola
        max_row = self.grid_size - 1

        # Trova le intersezioni possibili
        for row in range(min_row, max_row + 1):
            # Verifica che la riga corrente non sia nella zona di sicurezza
            if safety_zone_start <= row <= safety_zone_end:
                continue

            # Trova le lettere disponibili sulla prima e quarta parola in questa riga
            first_word_letter = None
            fourth_word_letter = None
            first_word_col = None
            fourth_word_col = None

            # Controlla le intersezioni con la prima parola
            if (first_word.y <= row < first_word.y + len(first_word.text)):
                pos_in_word = row - first_word.y
                first_word_letter = first_word.text[pos_in_word]
                first_word_col = first_word.x

            # Controlla le intersezioni con la quarta parola
            if (fourth_word.y <= row < fourth_word.y + len(fourth_word.text)):
                pos_in_word = row - fourth_word.y
                fourth_word_letter = fourth_word.text[pos_in_word]
                fourth_word_col = fourth_word.x

            # Se abbiamo entrambe le intersezioni, cerca una parola adatta
            if first_word_letter and fourth_word_letter:
                distance = abs(fourth_word_col - first_word_col)
                word = self.find_double_intersection_word(
                    first_word_letter, fourth_word_letter,
                    distance, first_word_col, fourth_word_col
                )

                if word:
                    # Verifica che la parola non interferisca con la zona di sicurezza
                    start_col = min(first_word_col, fourth_word_col)
                    if self.can_place_word(word['solution'], row, start_col, vertical=False):
                        return self.place_word(word, row, start_col, vertical=False)

        return False

    def find_word_with_letter_in_range(self, length_range: Tuple[int, int],
                                       letter: str,
                                       position_range: List[int]) -> Optional[Dict]:
        """
        Trova una parola che contiene una lettera in una delle posizioni specificate.
        """
        matching_words = []
        for word in self.word_list:
            if not (length_range[0] <= len(word['solution']) <= length_range[1]):
                continue

            positions = [i for i, char in enumerate(word['solution']) if char == letter]
            if any(pos in position_range for pos in positions):
                matching_words.append(word)

        return random.choice(matching_words) if matching_words else None

    def find_double_intersection_word(self, first_letter: str,
                                      second_letter: str,
                                      distance: int,
                                      first_col: int,
                                      second_col: int) -> Optional[Dict]:
        """
        Trova una parola che interseca due punti specifici.
        """
        for length in range(distance + 1, min(15, distance + 5)):
            pattern = ['_'] * length
            first_pos = first_col - min(first_col, second_col)
            second_pos = first_pos + distance

            if 0 <= first_pos < length and 0 <= second_pos < length:
                pattern[first_pos] = first_letter
                pattern[second_pos] = second_letter

                word = self.find_word((length, length), ''.join(pattern))
                if word:
                    return word

        return None

    def place_intersecting_word(self, word_index: int, start: int, end: int,
                                vertical: bool = True) -> bool:
        """
        Posiziona una parola che interseca una parola esistente.
        """

        def is_within_grid(start_pos: int, word_length: int, max_size: int) -> bool:
            return 0 <= start_pos and start_pos + word_length <= max_size

        extracted_letter_index = random.randint(start, end)
        extracted_letter = self.placed_words[word_index].text[extracted_letter_index]

        new_word = self.find_word_with_letter((12, 14), extracted_letter, [6, 7])
        if not new_word:
            return False

        word_length = len(new_word['solution'])
        word_center = word_length // 2

        if vertical:
            new_word_col = self.placed_words[word_index].x + extracted_letter_index
            new_word_start_row = self.placed_words[word_index].y - word_center

            if not is_within_grid(new_word_start_row, word_length, self.grid_size):
                return False

            if new_word_col < 0 or new_word_col >= self.grid_size:
                return False

            return self.place_word(new_word, new_word_start_row, new_word_col, vertical=True)
        else:
            new_word_row = self.placed_words[word_index].y + extracted_letter_index
            new_word_start_col = self.placed_words[word_index].x - word_center

            if not is_within_grid(new_word_start_col, word_length, self.grid_size):
                return False

            if new_word_row < 0 or new_word_row >= self.grid_size:
                return False

            return self.place_word(new_word, new_word_row, new_word_start_col, vertical=False)

    def find_word_with_letter(self, length_range: Tuple[int, int],
                              letter: str,
                              positions: List[int]) -> Optional[Dict]:
        """
        Trova una parola che contiene una lettera in una delle posizioni specificate.
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