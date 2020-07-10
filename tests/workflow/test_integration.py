#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest

import numpy as np
import pandas as pd

from hadar.workflow.pipeline import Rename, RepeatScenario, Fault, Clip, ToShuffler
from hadar.workflow.shuffler import Shuffler


def range_sampler(low, high, size):
    n = np.math.ceil(size / (high - low))
    sample = np.arange(low, high)
    return np.tile(sample, n)[:size]


class TestPipeline(unittest.TestCase):
    def test_pipeline(self):
        # Input
        i = pd.DataFrame(data={'data': np.ones(1000) * 100})

        pipe = RepeatScenario(n=500) + \
               Rename(data='quantity') + \
               Fault(loss=10, occur_freq=0.1, downtime_min=5, downtime_max=10) +\
               Clip(lower=80)

        # Test
        o = pipe(i)

        # Verify io interfaces
        self.assertEqual(['data'], pipe.plug.inputs)
        self.assertEqual(['quantity'], pipe.plug.outputs)

        # Verify fault generator
        self.assertFalse((o.values == 100).all())
        self.assertTrue((80 <= o.values).all())

        # Verify columns
        np.testing.assert_array_equal(np.arange(500), o.columns.get_level_values(0).unique().sort_values())
        self.assertEqual(['quantity'], o.columns.get_level_values(1).unique())


class TestShuffler(unittest.TestCase):
    def test_shuffle(self):
        # Input
        shuffler = Shuffler(sampler=range_sampler)
        shuffler.add_data(name='solar', data=np.array([[1, 2, 3], [5, 6, 7]]))

        i = pd.DataFrame({(0, 'a'): [3, 4, 5], (1, 'a'): [7, 8, 9]})
        pipe = RepeatScenario(2) + ToShuffler('a')
        shuffler.add_pipeline(name='load', data=i, pipeline=pipe)

        # Expected
        exp = {'solar': np.array([[1, 2, 3], [5, 6, 7], [1, 2, 3]]),
               'load': np.array([[3, 4, 5], [7, 8, 9], [3, 4, 5]])}

        # Test & Verify
        res = shuffler.shuffle(3)
        for name, array in res.items():
            np.testing.assert_equal(exp[name], array)