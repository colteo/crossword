from abc import ABC, abstractmethod
from base.base_generator import BaseCrosswordGenerator
from typing import List, Dict, Tuple, Optional
import logging
import random


class HiddenWordGenerator(BaseCrosswordGenerator):
    """Classe base per i cruciverba con parola nascosta."""
    def __init__(self, grid_size=15, cell_size=75, db_config=None, max_attempts=3):
        super().__init__(grid_size, cell_size, db_config, max_attempts)
        self.key_column = None
        self.hidden_word = None
        self.min_word_length = 5
        self.max_word_length = 8

    @abstractmethod
    def set_hidden_word(self, word_length: int) -> bool:
        """Imposta la parola nascosta. Da implementare nelle sottoclassi."""
        pass

    @abstractmethod
    def find_intersecting_word(self, row: int, letter: str) -> Optional[Tuple[Dict, int]]:
        """Trova una parola che interseca. Da implementare nelle sottoclassi."""
        pass

    def save_hidden_word_info(self):
        """Salva le informazioni sulla parola nascosta."""
        output_file = f"{self.output_dir}/crossword.txt"
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write("\nParola nascosta nella colonna evidenziata:\n")
            f.write(f"Colonna: {self.key_column + 1}\n")
            f.write(f"Parola: {self.hidden_word}\n")


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
                    logging.info(f"Successfully generated crossword with {words_placed} words")
                    self.save_hidden_word_info()
                    return self.format_result()

            except Exception as e:
                logging.error(f"Error during generation: {str(e)}")

            attempts += 1

        logging.error("Failed to generate crossword after all attempts")
        return "Unable to generate crossword after multiple attempts"
