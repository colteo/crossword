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
            SELECT c.id, c.solution, c.clue, c.word_pattern, c.num_words,
                   COALESCE(cu.count, 0) as usage_count
            FROM clues c
            LEFT JOIN clues_usage cu ON c.id = cu.clue_id
            WHERE LENGTH(c.solution) <= %s
            ORDER BY COALESCE(cu.count, 0) ASC, RAND()
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
    def update_word_usage(db_config: Dict, clue_id: int) -> None:
        """
        Aggiorna il contatore di utilizzo per una specifica clue.
        """
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            # Prima prova ad aggiornare il contatore se esiste
            update_query = """
                INSERT INTO clues_usage (clue_id, count, last_used)
                VALUES (%s, 1, CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE 
                    count = count + 1,
                    last_used = CURRENT_TIMESTAMP
                """

            cursor.execute(update_query, (clue_id,))
            connection.commit()

            cursor.close()
            connection.close()

            logging.info(f"Updated usage count for clue_id: {clue_id}")

        except mysql.connector.Error as err:
            logging.error(f"Database error updating usage: {err}")
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