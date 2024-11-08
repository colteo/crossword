from base.hidden_word_generator import HiddenWordGenerator
import random
import logging
from typing import Dict, Tuple, Optional


class HiddenWordAGenerator(HiddenWordGenerator):
    """Implementazione specifica del generatore di cruciverba con parola nascosta."""

    def __init__(self, grid_size=15, cell_size=75, db_config=None, max_attempts=3):
        super().__init__(grid_size, cell_size, db_config, max_attempts)

    def get_crossword_type(self) -> str:
        return "hidden-word-a"

    def set_hidden_word(self, word_length: int) -> bool:
        """
        Seleziona e posiziona la parola nascosta nella colonna centrale.
        """
        word_info = self.find_word((word_length, word_length))
        if not word_info:
            logging.warning(f"Could not find a suitable hidden word of length {word_length}")
            return False

        self.hidden_word = word_info['solution']
        self.key_column = self.grid_size // 2

        for i, letter in enumerate(self.hidden_word):
            self.grid[i][self.key_column] = letter

        logging.info(f"Hidden word set: {self.hidden_word}")
        return True

    def find_intersecting_word(self, row: int, letter: str) -> Optional[Tuple[Dict, int]]:
        """
        Trova una parola orizzontale che interseca la lettera data nella riga specificata.
        """
        left_space = self.key_column
        right_space = self.grid_size - self.key_column - 1

        min_length = max(3, 2)
        max_length = min(15, left_space + right_space + 1)

        matching_words = []
        for word in self.word_list:
            word_text = word['solution']
            if not (min_length <= len(word_text) <= max_length):
                continue

            for start_col in range(max(0, self.key_column - len(word_text) + 1),
                                   min(self.grid_size - len(word_text) + 1, self.key_column + 1)):
                intersection_pos = self.key_column - start_col
                if (intersection_pos < len(word_text) and
                        word_text[intersection_pos] == letter):
                    matching_words.append((word, start_col))

        return random.choice(matching_words) if matching_words else None
