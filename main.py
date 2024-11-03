# main.py

from generators.type_a import TypeACrossword
from generators.type_b import TypeBCrossword
from generators.type_c import TypeCCrossword
from generators.hidden_word_a import HiddenWordAGenerator

def main():
    # Configurazione del database
    db_config = {
        'user': 'crossword',
        'password': 'crossword',
        'host': 'localhost',
        'database': 'crossword'
    }

    try:
        # generator = TypeACrossword(
        generator = HiddenWordAGenerator(
            grid_size=15,
            cell_size=75,
            db_config=db_config
        )

        # Genera il cruciverba
        result = generator.generate_crossword()
        print(result)

        # Il generatore creerà una directory 'output' con:
        # - crossword.json: il cruciverba in formato JSON
        # - crossword.txt: il cruciverba in formato testuale
        # - crossword.log: il log della generazione

    except Exception as e:
        print(f"Errore durante la generazione del cruciverba: {str(e)}")

if __name__ == "__main__":
    main()