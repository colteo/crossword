from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class Word:
    text: str
    x: int
    y: int
    is_horizontal: bool
    clue: str = ""
    word_pattern: str = ""
    num_words: str = ""

    def to_dict(self) -> Dict:
        """
        Converte l'oggetto Word in un dizionario.
        Include il word_pattern tra parentesi tonde nel campo clue solo se presente.
        """
        base_dict = asdict(self)
        # Modifica il campo clue per includere il word_pattern tra parentesi solo se presente
        if self.word_pattern:
            base_dict['clue'] = f"{self.clue} ({self.word_pattern})"
        else:
            base_dict['clue'] = self.clue
        return base_dict