#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest

import numpy as np
import pandas as pd
from pandas import MultiIndex

from hadar.workflow.pipeline import Stage, FreePlug, RestrictedPlug, FocusStage, Clip, Rename, Drop, Fault, \
    RepeatScenario, Pipeline


class Double(Stage):
    def __init__(self):
        Stage.__init__(self, FreePlug())

    def _process_timeline(self, timelines: pd.DataFrame) -> pd.DataFrame:
        return timelines * 2


class Max9(Stage):
    def __init__(self):
        Stage.__init__(self, FreePlug())

    def _process_timeline(self, timelines: pd.DataFrame) -> pd.DataFrame:
        return timelines.clip(None, 9)


class Divide(FocusStage):
    def __init__(self):
        Stage.__init__(self, RestrictedPlug(inputs=['a', 'b'], outputs=['d', 'r']))

    def _process_scenarios(self, n_scn: int, scenario: pd.DataFrame) -> pd.DataFrame:
        scenario.loc[:, 'd'] = (scenario['a'] / scenario['b']).apply(np.floor)
        scenario.loc[:, 'r'] = scenario['a'] - scenario['b'] * scenario['d']
        return scenario.drop(['a', 'b'], axis=1)


class Inverse(FocusStage):
    def __init__(self):
        FocusStage.__init__(self, RestrictedPlug(inputs=['d'], outputs=['d', '-d']))

    def _process_scenarios(self, n_scn: int, scenario: pd.DataFrame) -> pd.DataFrame:
        scenario.loc[:, '-d'] = -scenario['d']
        return scenario.copy()


class Wrong(Stage):
    def __init__(self):
        Stage.__init__(self, plug=RestrictedPlug(inputs=['e'], outputs=['e']))

    def _process_timeline(self, timeline: pd.DataFrame) -> pd.DataFrame:
        return timeline


class TestFreePlug(unittest.TestCase):
    def test_linkable_to(self):
        self.assertTrue(FreePlug().linkable_to(FreePlug()))

    def test_join_to_fre(self):
        # Input
        a = FreePlug()
        b = FreePlug()

        # Test
        c = a + b
        self.assertEqual(a, c)

    def test_join_to_restricted(self):
        # Input
        a = FreePlug()
        b = RestrictedPlug(inputs=['a', 'b'], outputs=['c', 'd'])

        # Test
        c = a + b
        self.assertEqual(b, c)


class TestRestrictedPlug(unittest.TestCase):
    def test_linkable_to_free(self):
        # Input
        a = RestrictedPlug(inputs=['a'], outputs=['b'])

        # Test
        self.assertTrue(a.linkable_to(FreePlug()))

    def test_linkable_to_restricted_ok(self):
        # Input
        a = RestrictedPlug(inputs=['a'], outputs=['b', 'c', 'd'])
        b = RestrictedPlug(inputs=['b', 'c'], outputs=['e'])

        # Test
        self.assertTrue(a.linkable_to(b))

    def test_linkable_to_restricted_wrong(self):
        # Input
        a = RestrictedPlug(inputs=['a'], outputs=['b', 'c', 'd'])
        b = RestrictedPlug(inputs=['b', 'c', 'f'], outputs=['e'])

        # Test
        self.assertFalse(a.linkable_to(b))

    def test_join_to_free(self):
        # Input
        a = RestrictedPlug(inputs=['a'], outputs=['b'])

        # Test
        b = a + FreePlug()
        self.assertEqual(a, b)

    def test_join_to_restricted(self):
        # Input
        a = RestrictedPlug(inputs=['a'], outputs=['b', 'c', 'd'])
        b = RestrictedPlug(inputs=['b', 'c'], outputs=['e'])

        # Expected
        exp = RestrictedPlug(inputs=['a'], outputs=['e', 'd'])

        # Test
        c = a + b
        self.assertEqual(exp, c)


class TestPipeline(unittest.TestCase):
    def test_compute(self):
        # Input
        i = pd.DataFrame({'a': [1, 2, 3]})
        pipe = Pipeline(stages=[Double(), Double()])

        # Expected
        exp = pd.DataFrame({(0, 'a'): [4, 8, 12]})

        # Test & Verify
        o = pipe(i)
        pd.testing.assert_frame_equal(exp, o)

    def test_add(self):
        # Input
        i = pd.DataFrame({'a': [1, 2, 3], 'b': [1, 2, 3]})
        pipe = Pipeline(stages=[Double(), Double()])
        pipe += Divide()

        # Expected
        exp = pd.DataFrame({(0, 'd'): [1, 1, 1], (0, 'r'): [0, 0, 0]}, dtype=float)

        # Test & Verify
        o = pipe(i)
        self.assertEqual(3, len(pipe.stages))
        self.assertIsInstance(pipe.plug, RestrictedPlug)
        pd.testing.assert_frame_equal(exp, o)

    def test_link_pipeline_free_to_free(self):
        # Input
        i = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        pipe = Double() + Max9()

        # Expected
        exp = pd.DataFrame({(0, 'a'): [2, 4, 6], (0, 'b'): [8, 9, 9]})

        # Test & Verify
        o = pipe(i)
        pd.testing.assert_frame_equal(exp, o)
        self.assertEqual([], pipe.plug.inputs)
        self.assertEqual([], pipe.plug.outputs)

    def test_link_pipeline_free_to_restricted(self):
        # Input
        i = pd.DataFrame({'a': [10, 20, 32], 'b': [4, 5, 6]})
        pipe = Double() + Divide()

        # Expected
        exp = pd.DataFrame({(0, 'd'): [2, 4, 5], (0, 'r'): [4, 0, 4]}, dtype='float')

        # Test & Verify
        o = pipe(i)
        pd.testing.assert_frame_equal(exp, o)
        self.assertEqual(['a', 'b'], pipe.plug.inputs)
        self.assertEqual(['d', 'r'], pipe.plug.outputs)

    def test_link_pipeline_restricted_to_free(self):
        # Input
        i = pd.DataFrame({'a': [10, 20, 32], 'b': [4, 5, 6]})
        pipe = Divide() + Double()

        # Expected
        exp = pd.DataFrame({(0, 'd'): [4, 8, 10], (0, 'r'): [4, 0, 4]}, dtype='float')

        # Test & Verify
        o = pipe(i)
        pd.testing.assert_frame_equal(exp, o)
        self.assertEqual(['a', 'b'], pipe.plug.inputs)
        self.assertEqual(['d', 'r'], pipe.plug.outputs)

    def test_link_pipeline_restricted_to_restricted(self):
        # Input
        i = pd.DataFrame({'a': [10, 20, 32], 'b': [4, 5, 6]})
        pipe = Divide() + Inverse()

        # Expected
        exp = pd.DataFrame({(0, 'd'): [2, 4, 5], (0, '-d'): [-2, -4, -5], (0, 'r'): [2, 0, 2]}, dtype='float')

        # Test & Verify
        o = pipe(i)
        pd.testing.assert_frame_equal(exp, o)
        self.assertEqual({'a', 'b'}, set(pipe.plug.inputs))
        self.assertEqual({'d', '-d', 'r'}, set(pipe.plug.outputs))

    def test_wrong_link(self):
        # Test & Verify
        self.assertRaises(ValueError, lambda: Divide() + Wrong())


class TestStage(unittest.TestCase):
    def test_compute(self):
        # Input
        i = pd.DataFrame({(0, 'a'): [1, 2, 3], (0, 'b'): [4, 5, 6],
                          (1, 'a'): [10, 20, 30], (1, 'b'): [40, 50, 60]})
        stage = Double()

        # Expected
        exp = pd.DataFrame({(0, 'a'): [2, 4, 6], (0, 'b'): [8, 10, 12],
                            (1, 'a'): [20, 40, 60], (1, 'b'): [80, 100, 120]})

        # Test & Verify
        o = stage(i)
        pd.testing.assert_frame_equal(exp, o)

    def test_wrong_compute(self):
        i = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        pipe = Inverse()

        self.assertRaises(ValueError, lambda: pipe(i))

    def test_standardize_column(self):
        i = pd.DataFrame({'a': [1, 2, 3]})

        # Expected
        exp = pd.DataFrame({(0, 'a'): [1, 2, 3]})

        res = Stage.standardize_column(i)
        pd.testing.assert_frame_equal(exp, res)

    def test_build_multi_index(self):
        # Input
        scenarios = [1, 2, 3]
        names = ['a', 'b']

        # Expected
        exp = MultiIndex.from_tuples([(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b'), (3, 'a'), (3, 'b')])

        # Test & Verify
        index = Stage.build_multi_index(scenarios=scenarios, names=names)
        pd.testing.assert_index_equal(exp, index)


class TestFocusPipeline(unittest.TestCase):
    def test_compute(self):
        # Input
        i = pd.DataFrame({(0, 'b'): [1, 2, 3], (0, 'a'): [4, 5, 6],
                          (1, 'b'): [10, 20, 30], (1, 'a'): [40, 50, 60]})
        pipe = Divide()

        # Expected
        exp = pd.DataFrame({(0, 'd'): [4, 2, 2], (0, 'r'): [0, 1, 0],
                            (1, 'd'): [4, 2, 2], (1, 'r'): [0, 10, 0]}, dtype='float')

        # Test & Verify
        o = pipe(i)
        pd.testing.assert_frame_equal(exp, o)


class TestClip(unittest.TestCase):
    def test_compute(self):
        # Input
        i = pd.DataFrame({'a': [12, 54, 87, 12], 'b': [98, 23, 65, 4]})

        pipe = Clip(lower=10, upper=50)

        # Expected
        exp = pd.DataFrame({(0, 'a'): [12, 50, 50, 12], (0, 'b'): [50, 23, 50, 10]})

        # Test & Verify
        o = pipe(i)
        pd.testing.assert_frame_equal(exp, o)


class TestRename(unittest.TestCase):
    def test_compute(self):
        # Input
        i = pd.DataFrame({'a': [12, 54, 87, 12], 'b': [98, 23, 65, 4]})

        pipe = Rename(a='alpha')

        # Expected
        exp = pd.DataFrame({(0, 'alpha'): [12, 54, 87, 12], (0, 'b'): [98, 23, 65, 4]})

        # Test & Verify
        o = pipe(i)
        pd.testing.assert_frame_equal(exp, o)


class TestDrop(unittest.TestCase):
    def test_compute(self):
        # Input
        i = pd.DataFrame({'a': [12, 54, 87, 12], 'b': [98, 23, 65, 4]})

        pipe = Drop('b')

        # Expected
        exp = pd.DataFrame({(0, 'a'): [12, 54, 87, 12]})

        # Test & Verify
        o = pipe(i)
        pd.testing.assert_frame_equal(exp, o)


class TestFault(unittest.TestCase):
    def test_compute(self):
        # Input
        power = 100
        i = pd.DataFrame({'quantity': np.ones(10000) * power})

        pipe = Fault(loss=20, occur_freq=0.001, downtime_min=50, downtime_max=60, seed=543)

        # Expected
        exp_time_down = i.size * pipe.occur_freq * (pipe.downtime_max + pipe.downtime_min) / 2
        exp_total_loss = exp_time_down * pipe.loss

        # Test & Verify
        o = pipe(i)

        time_down = o.where(o < power).dropna().size
        self.assertAlmostEqual(exp_time_down, time_down, delta=exp_time_down*0.1)

        total_loss = o.size * power - o.values.sum()
        self.assertAlmostEqual(exp_total_loss, total_loss, delta=exp_total_loss*0.1)


class TestRepeat(unittest.TestCase):
    def test_compute(self):
        # Input
        i = pd.DataFrame({'a': [12, 54, 87, 12], 'b': [98, 23, 65, 4]})
        pipe = RepeatScenario(n=2)

        # Expected
        exp1 = pd.DataFrame({(0, 'a'): [12, 54, 87, 12], (0, 'b'): [98, 23, 65, 4],
                             (1, 'a'): [12, 54, 87, 12], (1, 'b'): [98, 23, 65, 4]})

        exp2 = pd.DataFrame({(0, 'a'): [12, 54, 87, 12], (0, 'b'): [98, 23, 65, 4],
                             (1, 'a'): [12, 54, 87, 12], (1, 'b'): [98, 23, 65, 4],
                             (2, 'a'): [12, 54, 87, 12], (2, 'b'): [98, 23, 65, 4],
                             (3, 'a'): [12, 54, 87, 12], (3, 'b'): [98, 23, 65, 4]})

        # Test & Verify
        o = pipe(i)
        pd.testing.assert_frame_equal(exp1, o)

        o = pipe(o)
        pd.testing.assert_frame_equal(exp2, o)