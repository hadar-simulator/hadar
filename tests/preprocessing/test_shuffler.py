#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest
import numpy as np
import pandas as pd
import hadar as hd
from hadar import ToShuffler, RepeatScenario

from preprocessing.shuffler import Timeline, TimelinePipeline, Shuffler


def range_sampler(low, high, size):
    n = np.math.ceil(size / (high - low))
    sample = np.arange(low, high)
    return np.tile(sample, n)[:size]


class TestTimeline(unittest.TestCase):
    def test_sample(self):
        # Input
        tl = Timeline(np.arange(0, 15).reshape(5, 3), sampler=range_sampler)

        # Expected
        exp = np.array([[0, 1, 2],
                        [3, 4, 5],
                        [6, 7, 8],
                        [9, 10, 11],
                        [12, 13, 14],
                        [0, 1, 2],
                        [3, 4, 5]])

        # Test & Verify
        res = tl.sample(7)
        np.testing.assert_equal(exp, res)


class TestTimelinePipeline(unittest.TestCase):
    def test_compute(self):
        # Input
        i = pd.DataFrame({(0, 'a'): [1, 2, 3], (0, 'b'): [4, 5, 6],
                          (1, 'a'): [10, 20, 30], (1, 'b'): [40, 50, 60]})
        pipe = hd.RepeatScenario(2) + hd.ToShuffler('a')

        # Expected
        exp = np.array([[1, 2, 3],
                        [10, 20, 30],
                        [1, 2, 3],
                        [10, 20, 30]])

        # Test & Verify
        tl = TimelinePipeline(i, pipe)
        tl.compute()
        np.testing.assert_equal(exp, tl.data)


class TestShuffler(unittest.TestCase):
    def test_shuffle(self):
        # Input
        shuffler = Shuffler(sampler=range_sampler)
        shuffler.add_data(name='solar', data=np.array([[1, 2, 3], [5, 6, 7]]))

        i = pd.DataFrame({(0, 'a'): [3, 4, 5], (0, 'a'): [7, 8, 9]})
        pipe = RepeatScenario(2) + ToShuffler('a')
        shuffler.add_pipeline(name='load', data=i, pipeline=pipe)

        # Expected
        exp = {'solar': np.array([[1, 2, 3], [5, 6, 7], [1, 2, 3]]),
               'load': np.array([[6, 8, 10], [14, 16, 18], [6, 8, 10]])}

        res = shuffler.shuffle(3)
        for name, array in res.items():
            np.testing.assert_equal(exp[name], array)
