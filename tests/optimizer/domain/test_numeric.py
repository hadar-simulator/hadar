#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest
import numpy as np

from hadar.optimizer.domain.numeric import (
    NumericalValueFactory,
    ScalarNumericalValue,
    MatrixNumericalValue,
    RowNumericValue,
    ColumnNumericValue,
)


class TestNumericalValue(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = NumericalValueFactory(5, 3)

    def test_scalar(self):
        v = self.factory.create(42)
        self.assertIsInstance(v, ScalarNumericalValue)
        self.assertEqual(42, v[2, 3])
        self.assertRaises(IndexError, lambda: v[3, 1])
        self.assertRaises(IndexError, lambda: v[1, 5])
        self.assertTrue(v < 50)
        self.assertFalse(v < 30)
        np.testing.assert_array_equal([42] * 15, v.flatten())

    def test_matrix(self):
        v = self.factory.create(np.arange(15).reshape(3, 5))
        self.assertIsInstance(v, MatrixNumericalValue)
        self.assertEqual(13, v[2, 3])
        self.assertRaises(IndexError, lambda: v[3, 1])
        self.assertRaises(IndexError, lambda: v[1, 5])
        self.assertTrue(v < 16)
        self.assertFalse(v < 10)
        np.testing.assert_array_equal(range(15), v.flatten())

    def test_row(self):
        v = self.factory.create(np.arange(5))
        self.assertIsInstance(v, RowNumericValue)
        self.assertEqual(3, v[2, 3])
        self.assertRaises(IndexError, lambda: v[3, 1])
        self.assertRaises(IndexError, lambda: v[1, 5])
        np.testing.assert_array_equal(list(range(5)) * 3, v.flatten())

    def test_column(self):
        v = self.factory.create(np.arange(3).reshape(3, 1))
        self.assertIsInstance(v, ColumnNumericValue)
        self.assertEqual(2, v[2, 3])
        self.assertRaises(IndexError, lambda: v[3, 1])
        self.assertRaises(IndexError, lambda: v[1, 5])
        np.testing.assert_array_equal(
            [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2], v.flatten()
        )
