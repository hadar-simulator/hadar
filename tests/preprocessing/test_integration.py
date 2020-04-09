#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest
import pandas as pd
import numpy as np
from pandas import MultiIndex

from hadar.preprocessing.pipeline import Rename, RepeatScenario, Fault, Clip


class TestPipeline(unittest.TestCase):
    def test_pipeline(self):
        # Input
        i = pd.DataFrame(data={'data': np.ones(1000) * 100})

        pipe = RepeatScenario(n=500) + \
               Rename(rename={'data': 'quantity'}) + \
               Fault(loss=10, occur_freq=0.1, downtime_min=5, downtime_max=10) +\
               Clip(lower=80)

        # Test
        o = pipe.compute(i)

        # Verify io interfaces
        self.assertEqual(['data'], pipe.plug.inputs)
        self.assertEqual(['quantity'], pipe.plug.outputs)

        # Verify fault generator
        self.assertFalse((o.values == 100).all())
        self.assertTrue((80 <= o.values).all())

        # Verify columns
        np.testing.assert_array_equal(np.arange(500), o.columns.get_level_values(0).unique().sort_values())
        self.assertEqual(['quantity'], o.columns.get_level_values(1).unique())
