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

from preprocessing.generator import Timeline, TimelinePipeline


class TestTimeline(unittest.TestCase):
    def test(self):
        # Input
        tl = Timeline(np.ones((5, 4)))

        # Test & Verify
        tl.sample(20)
        self.assertEqual(20, tl.sampling.size)
        self.assertEqual(4, tl[19].size)


class TestTimelinePipeline(unittest.TestCase):
    def test(self):
        # Input
        i = pd.DataFrame({(0, 'a'): [1, 2, 3], (0, 'b'): [4, 5, 6],
                          (1, 'a'): [10, 20, 30], (1, 'b'): [40, 50, 60]})
        pipe = hd.RepeatScenario(2) + hd.ToGenerator('a')

        # Expected
        exp = np.array([[1, 2, 3],
                        [10, 20, 30],
                        [1, 2, 3],
                        [10, 20, 30]])

        # Test & Verify
        tl = TimelinePipeline(i, pipe)
        tl.compute()
        np.testing.assert_equal(exp, tl.data)




class TestGenerator(unittest.TestCase):
    def test_add_pipeline(self):
        pass