import unittest

from open_prices.proofs.ml.receipt_anonymization.ocr import (
    Word,
    get_search_map,
    locate_words,
)

BOUNDING_BOX = (0.1, 0.1, 0.2, 0.2)
WORDS = [
    Word(text="Mr.", bounding_box=BOUNDING_BOX, line_idx=1),
    Word(text=" ", bounding_box=BOUNDING_BOX, line_idx=1),
    Word(text="Dupont", bounding_box=BOUNDING_BOX, line_idx=1),
    Word(text="Reçu", bounding_box=BOUNDING_BOX, line_idx=2),
    Word(text=" ", bounding_box=BOUNDING_BOX, line_idx=2),
    Word(text="n°", bounding_box=BOUNDING_BOX, line_idx=2),
    Word(text=" ", bounding_box=BOUNDING_BOX, line_idx=2),
    Word(text="402852052852", bounding_box=BOUNDING_BOX, line_idx=2),
    Word(text=".", bounding_box=BOUNDING_BOX, line_idx=2),
    Word(text=" ", bounding_box=BOUNDING_BOX, line_idx=2),
]


class TestSearchMap(unittest.TestCase):
    def test_search_map(self):
        search_str, index_map = get_search_map(WORDS)
        self.assertEqual(search_str, "Mr.DupontReçun°402852052852.")
        self.assertEqual(len(index_map), 28)
        expected_index_map = [
            0,
            0,
            0,
            2,
            2,
            2,
            2,
            2,
            2,
            3,
            3,
            3,
            3,
            5,
            5,
            7,
            7,
            7,
            7,
            7,
            7,
            7,
            7,
            7,
            7,
            7,
            7,
            8,
        ]
        self.assertSequenceEqual(index_map.tolist(), expected_index_map)


class TestLocateWord(unittest.TestCase):
    def test_locate_words(self):
        word_indices = locate_words(["Mr.", "Dupont"], WORDS)
        self.assertSequenceEqual(word_indices, [0, 2])

        word_indices = locate_words(["402852052852"], WORDS)
        self.assertSequenceEqual(word_indices, [7])
