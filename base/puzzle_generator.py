from abc import ABC, abstractmethod
from base.base_generator import BaseCrosswordGenerator
import logging


class PuzzleCrosswordGenerator(BaseCrosswordGenerator):
    """Classe base per i cruciverba puzzle standard."""
    def __init__(self, grid_size=15, cell_size=75, db_config=None, max_attempts=3):
        super().__init__(grid_size, cell_size, db_config, max_attempts)

    @abstractmethod
    def place_first_word(self) -> bool:
        """Posiziona la prima parola. Da implementare nelle sottoclassi."""
        pass

    @abstractmethod
    def place_second_word(self) -> bool:
        """Posiziona la seconda parola. Da implementare nelle sottoclassi."""
        pass

    @abstractmethod
    def place_third_word(self) -> bool:
        """Posiziona la terza parola. Da implementare nelle sottoclassi."""
        pass

    @abstractmethod
    def place_fourth_word(self) -> bool:
        """Posiziona la quarta parola. Da implementare nelle sottoclassi."""
        pass

    @abstractmethod
    def place_fifth_word(self) -> bool:
        """Posiziona la quinta parola. Da implementare nelle sottoclassi."""
        pass

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
