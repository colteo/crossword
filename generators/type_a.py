from typing import List, Dict, Tuple, Optional
import random
import logging
from base.puzzle_generator import PuzzleCrosswordGenerator
from base.word import Word


class TypeACrossword(PuzzleCrosswordGenerator):
    """
    Implementazione del generatore di cruciverba con strategia orizzontale centrica.
    La prima parola viene posizionata orizzontalmente al centro della griglia.
    """

    def get_crossword_type(self) -> str:
        return "type-a"

    def place_first_word(self) -> bool:
        """
        Posiziona la prima parola orizzontalmente al centro della griglia.
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
        Posiziona la seconda parola verticalmente, intersecando la prima parola.
        """
        return self.place_intersecting_word(0, 0, len(self.placed_words[0].text) // 2 - 1)

    def place_third_word(self) -> bool:
        """
        Posiziona la terza parola verticalmente, intersecando la prima parola.
        """
        return self.place_intersecting_word(0, len(self.placed_words[0].text) // 2 + 1,
                                            len(self.placed_words[0].text) - 1)

    def place_fourth_word(self) -> bool:
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

    def place_fifth_word(self) -> bool:
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

    def find_intersections_fourth_word(self) -> List[Dict]:
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

    def find_fourth_word(self, selected_intersection: Dict) -> Tuple[Optional[Dict], Optional[int]]:
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

    def find_free_letters_in_vertical_word(self, vertical_word: 'Word') -> List[Dict]:
        """
        Trova lettere utilizzabili per intersezioni nella parola verticale.
        """
        free_letters = []
        for i, letter in enumerate(vertical_word.text):
            row = vertical_word.y + i
            col = vertical_word.x

            # Verifica spazio a sinistra
            left_spaces = 0
            for j in range(col - 1, -1, -1):
                # Controlla se c'è una parola verticale
                if any(word for word in self.placed_words
                       if not word.is_horizontal and word.x == j):
                    # Lascia almeno una cella di spazio
                    if left_spaces == 0:
                        left_spaces = -1  # Invalida questo spazio
                    break
                if (self.grid[row][j] == '_' and
                        self.grid[row - 1][j] == '_' and
                        self.grid[row + 1][j] == '_'):
                    left_spaces += 1
                else:
                    break

            # Verifica spazio a destra
            right_spaces = 0
            for j in range(col + 1, self.grid_size):
                # Controlla se c'è una parola verticale
                if any(word for word in self.placed_words
                       if not word.is_horizontal and word.x == j):
                    # Lascia almeno una cella di spazio
                    if right_spaces == 0:
                        right_spaces = -1  # Invalida questo spazio
                    break
                if (self.grid[row][j] == '_' and
                        self.grid[row - 1][j] == '_' and
                        self.grid[row + 1][j] == '_'):
                    right_spaces += 1
                else:
                    break

            # Considera valido solo se c'è spazio sufficiente sia a destra che a sinistra
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

    def place_intersecting_word(self, word_index: int, start: int, end: int) -> bool:
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

    def find_word_with_letter(self, length_range: Tuple[int, int], letter: str,
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