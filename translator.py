import unittest
from typing import List, Tuple

# Function to test
def process_arrays(collis: List[float], gross: List[float]) -> Tuple[List[float], List[float]]:
    collis = [value for value in collis if value]
    gross = [value for value in gross if value]

    if len(collis) != len(gross):
        return [], []
            
    if len(collis) <= 4:
        collis = collis[-1]
        gross = gross[-1]
    elif len(collis) >= 5:
        if sum(collis[:4]) == collis[-1] :
            collis = collis[-1]
            gross = gross[-1] 
        else :
            collis = sum(collis)
            gross = sum(gross)
                      
    return collis, gross

collis = [10.0, 0, 0, 0, 0]
gross = [15.0, 0, 0, 0, 0]

collis = [10.0, 20.0, 30.0, 0, 0]
gross = [15.0, 25.0, 40.0, 0, 0]

print(process_arrays(collis, gross))








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
        expected_collis = [30.0]
        expected_gross = [80.0]
        self.assertEqual(process_arrays(collis, gross), (expected_collis, expected_gross))

    def test_three_items_no_sum_match(self):
        collis = [10.0, 20.0, 35.0, 0, 0]
        gross = [15.0, 25.0, 50.0, 0, 0]
        expected_collis = [65.0]
        expected_gross = [90.0]
        self.assertEqual(process_arrays(collis, gross), (expected_collis, expected_gross))

    def test_five_items_sum_match(self):
        collis = [10.0, 20.0, 15.0, 25.0, 30.0]
        gross = [15.0, 25.0, 20.0, 30.0, 40.0]
        expected_collis = [30.0]
        expected_gross = []
        self.assertEqual(process_arrays(collis, gross), (expected_collis, expected_gross))

    def test_five_items_no_sum_match(self):
        collis = [10.0, 20.0, 15.0, 25.0, 50.0]
        gross = [15.0, 25.0, 20.0, 30.0, 60.0]
        expected_collis = [120.0]
        expected_gross = [150.0]
        self.assertEqual(process_arrays(collis, gross), (expected_collis, expected_gross))

    def test_empty_items_removed(self):
        collis = [0, 10.0, 0, 20.0, 0]
        gross = [0, 15.0, 0, 25.0, 0]
        expected_collis = [30.0]
        expected_gross = [40.0]
        self.assertEqual(process_arrays(collis, gross), (expected_collis, expected_gross))

    def test_mismatched_lengths(self):
        collis = [10.0, 20.0, 30.0, 0, 0]
        gross = [15.0, 25.0, 40.0, 0]
        with self.assertRaises(ValueError):
            process_arrays(collis, gross)


