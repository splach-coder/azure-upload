import unittest
from typing import List, Tuple

# Function to test
def process_arrays(collis: List[float], gross: List[float]) -> Tuple[List[float], List[float]]:
    collis = [value for value in collis if value]
    gross = [value for value in gross if value]

    if len(collis) != len(gross):
        raise ValueError("Collis and Gross arrays are not the same length after removing empty items.")

    if len(collis) == 3:
        if collis[0] + collis[1] == collis[2]:
            collis.pop(2)
        if gross[0] + gross[1] == gross[2]:
            gross.pop(2)
    elif len(collis) == 5:
        if collis[0] + collis[1] == collis[4]:
            collis.pop(4)
        if gross[0] + gross[1] == gross[4]:
            gross.pop(4)

    return collis, gross

class TestProcessArrays(unittest.TestCase):

    def test_one_item(self):
        collis = [10.0, 0, 0, 0, 0]
        gross = [15.0, 0, 0, 0, 0]
        expected_collis = [10.0]
        expected_gross = [15.0]
        self.assertEqual(process_arrays(collis, gross), (expected_collis, expected_gross))

    def test_three_items_sum_match(self):
        collis = [10.0, 20.0, 30.0, 0, 0]
        gross = [15.0, 25.0, 40.0, 0, 0]
        expected_collis = [10.0, 20.0]
        expected_gross = [15.0, 25.0]
        self.assertEqual(process_arrays(collis, gross), (expected_collis, expected_gross))

    def test_three_items_no_sum_match(self):
        collis = [10.0, 20.0, 35.0, 0, 0]
        gross = [15.0, 25.0, 50.0, 0, 0]
        expected_collis = [10.0, 20.0, 35.0]
        expected_gross = [15.0, 25.0, 50.0]
        self.assertEqual(process_arrays(collis, gross), (expected_collis, expected_gross))

    def test_five_items_sum_match(self):
        collis = [10.0, 20.0, 15.0, 25.0, 30.0]
        gross = [15.0, 25.0, 20.0, 30.0, 40.0]
        expected_collis = [10.0, 20.0, 15.0, 25.0]
        expected_gross = [15.0, 25.0, 20.0, 30.0]
        self.assertEqual(process_arrays(collis, gross), (expected_collis, expected_gross))

    def test_five_items_no_sum_match(self):
        collis = [10.0, 20.0, 15.0, 25.0, 50.0]
        gross = [15.0, 25.0, 20.0, 30.0, 60.0]
        expected_collis = [10.0, 20.0, 15.0, 25.0, 50.0]
        expected_gross = [15.0, 25.0, 20.0, 30.0, 60.0]
        self.assertEqual(process_arrays(collis, gross), (expected_collis, expected_gross))

    def test_empty_items_removed(self):
        collis = [0, 10.0, 0, 20.0, 0]
        gross = [0, 15.0, 0, 25.0, 0]
        expected_collis = [10.0, 20.0]
        expected_gross = [15.0, 25.0]
        self.assertEqual(process_arrays(collis, gross), (expected_collis, expected_gross))

    def test_mismatched_lengths(self):
        collis = [10.0, 20.0, 30.0, 0, 0]
        gross = [15.0, 25.0, 40.0, 0]
        with self.assertRaises(ValueError):
            process_arrays(collis, gross)

if __name__ == "__main__":
    unittest.main()
