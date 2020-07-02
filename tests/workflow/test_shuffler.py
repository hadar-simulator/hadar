#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest

import numpy as np
import pandas as pd

from hadar.workflow.pipeline import Pipeline, TO_SHUFFLER
from hadar.workflow.pipeline import ToShuffler
from hadar.workflow.shuffler import Timeline, TimelinePipeline, Shuffler


def range_sampler(low, high, size):
    n = np.math.ceil(size / (high - low))
    sample = np.arange(low, high)
    return np.tile(sample, n)[:size]


class MockPipeline(Pipeline):
    def __init__(self, return_value):
        Pipeline.__init__(self, stages=[ToShuffler('')])
        self.return_value = return_value
        self.input = None

    def __call__(self, timeline):
        self.input = timeline
        return self.return_value

    def assert_computable(self, timeline: pd.DataFrame):
        pass

    def assert_to_shuffler(self):
        pass


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
        i = pd.DataFrame()

        # Mock
        o = pd.DataFrame({(0, TO_SHUFFLER): [1, 2, 3], (0, 'b'): [4, 5, 6],
                          (1, TO_SHUFFLER): [10, 20, 30], (1, 'b'): [40, 50, 60]})

        mock_pipe = MockPipeline(return_value=o)

        # Expected
        exp = np.array([[1, 2, 3],
                        [10, 20, 30]])

        # Test & Verify
        tl = TimelinePipeline(i, mock_pipe)
        data = tl.compute()
        np.testing.assert_equal(exp, data)
        pd.testing.assert_frame_equal(i, mock_pipe.input)


class TestShuffler(unittest.TestCase):
    def test_shuffle(self):
        # Input
        shuffler = Shuffler(sampler=range_sampler)
        shuffler.add_data(name='solar', data=np.array([[1, 2, 3], [5, 6, 7]]))

        i = pd.DataFrame({(0, 'a'): [3, 4, 5], (1, 'a'): [7, 8, 9]})

        # Mock
        o = pd.DataFrame({(0, TO_SHUFFLER): [3, 4, 5],
                          (1, TO_SHUFFLER): [7, 8, 9],
                          (0, TO_SHUFFLER): [3, 4, 5],
                          (1, TO_SHUFFLER): [7, 8, 9]})
        mock_pipe = MockPipeline(return_value=o)
        shuffler.add_pipeline(name='load', data=i, pipeline=mock_pipe)

        # Expected
        exp = {'solar': np.array([[1, 2, 3], [5, 6, 7], [1, 2, 3]]),
               'load': np.array([[3, 4, 5], [7, 8, 9], [3, 4, 5]])}

        # Test & Verify
        res = shuffler.shuffle(3)
        for name, array in res.items():
            np.testing.assert_equal(exp[name], array)
