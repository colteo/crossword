import random
from nltk.corpus import words
import nltk

nltk.download('words', quiet=True)


class CrosswordGenerator:
    def __init__(self, grid_size=15):
        self.grid_size = grid_size
        self.grid = [['_' for _ in range(grid_size)] for _ in range(grid_size)]
        self.word_list = self.get_word_list()

    @staticmethod
    def get_word_list():
        return set(word.lower() for word in words.words() if word.isalpha())

    def find_word(self, length_range, pattern=None):
        matching_words = [word for word in self.word_list if length_range[0] <= len(word) <= length_range[1]]
        if pattern:
            matching_words = [word for word in matching_words if all(
                word[i] == pattern[i] for i in range(min(len(word), len(pattern))) if pattern[i] != '_')]
        return random.choice(matching_words) if matching_words else None

    def find_word_with_letter(self, length_range, letter, positions):
        for pos in positions:
            for length in range(length_range[0], length_range[1] + 1):
                if pos < length:
                    pattern = ['_'] * length
                    pattern[pos] = letter
                    word = self.find_word((length, length), ''.join(pattern))
                    if word:
                        return word
        return None

    def place_word(self, word, start_row, start_col, vertical=False):
        for i, letter in enumerate(word):
            if vertical:
                self.grid[start_row + i][start_col] = letter
            else:
                self.grid[start_row][start_col + i] = letter

    def find_intersections(self, second_word, third_word, second_word_start_row, third_word_start_row, second_word_col,
                           third_word_col, start_row_1):
        same_row_letters = []
        for i in range(len(second_word)):
            second_word_row = second_word_start_row + i
            if (second_word_row != start_row_1 and
                    second_word_row >= third_word_start_row and
                    second_word_row < third_word_start_row + len(third_word)):
                third_word_index = second_word_row - third_word_start_row
                same_row_letters.append({
                    'second_word_letter': second_word[i],
                    'third_word_letter': third_word[third_word_index],
                    'row': second_word_row,
                    'second_word_col': second_word_col,
                    'third_word_col': third_word_col,
                    'distance': abs(second_word_col - third_word_col)
                })
        return same_row_letters

    def find_fourth_word(self, selected_intersection):
        distance = selected_intersection['distance']
        min_length = max(3, distance + 1)  # Aumentiamo la lunghezza minima
        max_length = min(15, distance + 5)  # Aumentiamo la lunghezza massima

        left_col = min(selected_intersection['second_word_col'], selected_intersection['third_word_col'])
        right_col = max(selected_intersection['second_word_col'], selected_intersection['third_word_col'])

        for length in range(min_length, max_length + 1):
            pattern = ['_'] * length
            left_index = 0 if left_col == selected_intersection['second_word_col'] else distance
            right_index = distance if right_col == selected_intersection['third_word_col'] else 0

            pattern[left_index] = selected_intersection['second_word_letter']
            pattern[right_index] = selected_intersection['third_word_letter']

            word = self.find_word((length, length), ''.join(pattern))
            if word:
                return word, left_col - left_index

        return None, None

    def generate_crossword(self):
        # Trova e posiziona la prima parola
        first_word = self.find_word((8, 12))
        if not first_word:
            return "Non è possibile trovare una parola adatta per iniziare il cruciverba."

        start_row_1 = self.grid_size // 2
        start_col_1 = (self.grid_size - len(first_word)) // 2
        self.place_word(first_word, start_row_1, start_col_1)

        # Trova e posiziona la seconda parola
        extracted_letter_2_index = random.randint(0, len(first_word) // 2 - 1)
        extracted_letter_2 = first_word[extracted_letter_2_index]
        second_word = self.find_word_with_letter((6, 8), extracted_letter_2, [3, 4])

        if not second_word:
            return "Non è possibile trovare una seconda parola adatta."

        second_word_col = start_col_1 + extracted_letter_2_index
        second_word_start_row = start_row_1 - second_word.index(extracted_letter_2)
        self.place_word(second_word, second_word_start_row, second_word_col, vertical=True)

        # Trova e posiziona la terza parola
        extracted_letter_3_index = random.randint(len(first_word) // 2 + 1, len(first_word) - 1)
        extracted_letter_3 = first_word[extracted_letter_3_index]
        third_word = self.find_word_with_letter((6, 8), extracted_letter_3, [3, 4])

        if not third_word:
            return "Non è possibile trovare una terza parola adatta."

        third_word_col = start_col_1 + extracted_letter_3_index
        third_word_start_row = start_row_1 - third_word.index(extracted_letter_3)
        self.place_word(third_word, third_word_start_row, third_word_col, vertical=True)

        # Trova le intersezioni e la quarta parola
        same_row_letters = self.find_intersections(second_word, third_word, second_word_start_row, third_word_start_row,
                                                   second_word_col, third_word_col, start_row_1)

        fourth_word = None
        selected_intersection = None
        if same_row_letters:
            selected_intersection = random.choice(same_row_letters)
            fourth_word, fourth_word_start_col = self.find_fourth_word(selected_intersection)

            if fourth_word:
                fourth_word_row = selected_intersection['row']
                self.place_word(fourth_word, fourth_word_row, fourth_word_start_col)

        return self.format_result(first_word, second_word, third_word, fourth_word, extracted_letter_2,
                                  extracted_letter_2_index, extracted_letter_3, extracted_letter_3_index,
                                  same_row_letters, selected_intersection)

    def format_result(self, first_word, second_word, third_word, fourth_word, extracted_letter_2,
                      extracted_letter_2_index, extracted_letter_3, extracted_letter_3_index, same_row_letters,
                      selected_intersection):
        crossword = "\n".join(" ".join(row) for row in self.grid)
        print(crossword)

        result = f"Prima parola: {first_word}\n"
        result += f"Seconda parola: {second_word}\n"
        result += f"Lettera di incrocio: {extracted_letter_2} (posizione {extracted_letter_2_index + 1} nella prima parola, "
        result += f"posizione {second_word.index(extracted_letter_2) + 1} nella seconda parola)\n"
        result += f"Terza parola: {third_word}\n"
        result += f"Lettera di incrocio: {extracted_letter_3} (posizione {extracted_letter_3_index + 1} nella prima parola, "
        result += f"posizione {third_word.index(extracted_letter_3) + 1} nella terza parola)\n"

        if same_row_letters:
            result += "Intersezioni trovate (escludendo la riga della prima parola):\n"
            for info in same_row_letters:
                result += f"- Riga {info['row']}: '{info['second_word_letter']}' (seconda parola) e '{info['third_word_letter']}' (terza parola), "
                result += f"distanza: {info['distance']} colonne\n"

            if selected_intersection:
                result += f"\nIntersezione selezionata casualmente: Riga {selected_intersection['row']}\n"

            if fourth_word:
                result += f"Quarta parola: {fourth_word}\n"
                result += f"Inserita tra '{selected_intersection['second_word_letter']}' della seconda parola e "
                result += f"'{selected_intersection['third_word_letter']}' della terza parola\n"
            else:
                result += "Non è stato possibile trovare una quarta parola adatta.\n"
        else:
            result += "Non ci sono intersezioni valide tra la seconda e la terza parola.\n"

        return result


# Uso della classe
generator = CrosswordGenerator()
print(generator.generate_crossword())