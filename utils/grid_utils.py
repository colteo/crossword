from typing import List, Dict, Tuple
import logging

class GridUtils:
    @staticmethod
    def get_non_empty_rows(grid: List[List[str]]) -> List[int]:
        """
        Trova gli indici delle righe che contengono almeno una lettera.
        """
        return [i for i, row in enumerate(grid)
                if any(cell != '_' for cell in row)]

    @staticmethod
    def get_non_empty_cols(grid: List[List[str]]) -> List[int]:
        """
        Trova gli indici delle colonne che contengono almeno una lettera.
        """
        return [j for j in range(len(grid[0]))
                if any(grid[i][j] != '_' for i in range(len(grid)))]

    @staticmethod
    def create_optimized_grid(grid: List[List[str]],
                            non_empty_rows: List[int],
                            non_empty_cols: List[int]) -> List[List[str]]:
        """
        Crea una nuova griglia contenente solo le righe e colonne non vuote.
        """
        return [[grid[i][j] for j in non_empty_cols]
                for i in non_empty_rows]

    @staticmethod
    def create_coordinate_mapping(non_empty_indices: List[int]) -> Dict[int, int]:
        """
        Crea un dizionario che mappa le vecchie coordinate alle nuove.
        """
        return {old_idx: new_idx
                for new_idx, old_idx in enumerate(non_empty_indices)}

    @staticmethod
    def can_place_word(grid: List[List[str]],
                      word: str,
                      start_row: int,
                      start_col: int,
                      vertical: bool = False,
                      grid_size: int = None) -> bool:
        """
        Verifica se una parola può essere piazzata in una posizione specifica.
        """
        if grid_size is None:
            grid_size = len(grid)

        if vertical:
            if start_row < 0 or start_row + len(word) > grid_size:
                return False
            return all(grid[start_row + i][start_col] in ('_', word[i])
                      for i in range(len(word)))
        else:
            if start_col < 0 or start_col + len(word) > grid_size:
                return False
            return all(grid[start_row][start_col + i] in ('_', word[i])
                      for i in range(len(word)))