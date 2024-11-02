from typing import List, Dict, Tuple, Optional
import mysql.connector
import logging

class DatabaseUtils:
    @staticmethod
    def get_word_list_from_db(db_config: Dict, grid_size: int) -> List[Dict]:
        """
        Recupera la lista di parole dal database.
        """
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)

            query = """
            SELECT solution, clue, word_pattern, num_words 
            FROM crossword_entries
            WHERE LENGTH(solution) <= %s
            """
            cursor.execute(query, (grid_size,))
            word_list = cursor.fetchall()

            cursor.close()
            connection.close()

            logging.info(f"Retrieved {len(word_list)} words from database")
            return word_list

        except mysql.connector.Error as err:
            logging.error(f"Database error: {err}")
            raise

    @staticmethod
    def find_word(word_list: List[Dict],
                 length_range: Tuple[int, int],
                 pattern: Optional[str] = None) -> Optional[Dict]:
        """
        Cerca una parola dalla lista che soddisfa i criteri specificati.
        """
        matching_words = [
            word for word in word_list
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