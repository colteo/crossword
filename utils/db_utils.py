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
    def update_word_usage(db_config: Dict, clue_id: int, output_path: str) -> None:
        """
        Aggiorna il contatore di utilizzo per una specifica clue e salva il percorso di output.
        """
        connection = None
        cursor = None
        try:
            logging.info(f"Attempting to update usage for clue_id: {clue_id}")
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            # Verifica se esiste già un record
            check_query = "SELECT count FROM clues_usage WHERE clue_id = %s"
            cursor.execute(check_query, (clue_id,))
            result = cursor.fetchone()

            if result is None:
                # Insert new record
                logging.info(f"Inserting new usage record for clue_id: {clue_id}")
                insert_query = """
                INSERT INTO clues_usage (clue_id, count, last_used, output_path)
                VALUES (%s, 1, CURRENT_TIMESTAMP, %s)
                """
                cursor.execute(insert_query, (clue_id, output_path))
            else:
                # Update existing record
                logging.info(f"Updating existing usage record for clue_id: {clue_id}")
                update_query = """
                UPDATE clues_usage
                SET count = count + 1,
                    last_used = CURRENT_TIMESTAMP,
                    output_path = %s
                WHERE clue_id = %s
                """
                cursor.execute(update_query, (output_path, clue_id))

            connection.commit()
            logging.info(f"Successfully updated usage for clue_id: {clue_id}")

        except mysql.connector.Error as err:
            logging.error(f"Database error updating usage: {err}")
            if connection:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

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