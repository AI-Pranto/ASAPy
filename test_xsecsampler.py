from unittest import TestCase
from ASAPy import XsecSampler
import unittest
import pandas as pd
import numpy as np


class TestMapGroups(TestCase):
    def test_map_groups_to_continuous(self):
        """
        Expect a certain mapping. Points are mapped from e_sigma to high_e_bins based on where e_sigma
        would be if it was inserted into high_e_bins. This is to figure out what energy group # the e sigma lies

        Checks for the cases:
        e to map from is less than min_e -> None
        e to map from is greater than max_e -> None
        e to map from is greater than min_e but less than min bin -> highest e group
        e to map from is less than max_e but greater than max bin -> lowest e group
        e to map from is between known e bins -> get correct e bin

        Returns
        -------

        """
        e_sigma = np.array([1e-22, 1e-8, 1e-3, 1e-2, 0.5, 1, 20, 27, 35]) * 1e6  # eV
        high_e_bins = pd.Series([25, 2.0, 1e-1, 1e-4, 1e-5]) * 1e6  # eV
        multi_group_val = pd.Series([1, 2, 3, 4, 5], index=[1,2,3,4,5])
        max_e = 30e6  # eV
        min_e = 1e-9  # eV
        mapped_values = XsecSampler.map_groups_to_continuous(e_sigma, high_e_bins, multi_group_val, max_e, min_e, value_outside_of_range=-1)


        self.assertListEqual(list(mapped_values), [-1, 5, 3, 3, 2, 2, 1, 1, -1])


if __name__ == "__main__":
    unittest.main()