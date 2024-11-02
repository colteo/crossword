from dataclasses import dataclass, asdict


@dataclass
class Word:
    text: str
    x: int
    y: int
    is_horizontal: bool
    clue: str = ""
    word_pattern: str = ""
    num_words: str = ""

    def to_dict(self):
        return asdict(self)