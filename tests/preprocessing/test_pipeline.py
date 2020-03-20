import unittest
import pandas as pd
import numpy as np

from hadar.preprocessing.pipeline import Stage, FreePlug, RestrictedPlug, FocusStage


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
        scenario['d'] = (scenario['a'] / scenario['b']).apply(np.floor)
        scenario['r'] = scenario['a'] - scenario['b'] * scenario['d']
        return scenario.drop(['a', 'b'], axis=1)


class Inverse(FocusStage):
    def __init__(self):
        Stage.__init__(self, RestrictedPlug(inputs=['d'], outputs=['d', '-d']))

    def _process_scenarios(self, n_scn: int, scenario: pd.DataFrame) -> pd.DataFrame:
        scenario['-d'] = -scenario['d']
        return scenario.copy()


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
        exp = RestrictedPlug(inputs=['a'], outputs=['d', 'e'])

        # Test
        c = a + b
        self.assertEqual(exp, c)


class TestPipeline(unittest.TestCase):
    def test_compute(self):
        # Input
        i = pd.DataFrame({(0, 'a'): [1, 2, 3], (0, 'b'): [4, 5, 6],
                          (1, 'a'): [10, 20, 30], (1, 'b'): [40, 50, 60]})
        pipe = Double()

        # Expected
        exp = pd.DataFrame({(0, 'a'): [2, 4, 6], (0, 'b'): [8, 10, 12],
                            (1, 'a'): [20, 40, 60], (1, 'b'): [80, 100, 120]})

        # Test & Verify
        o = pipe.compute(i)
        pd.testing.assert_frame_equal(exp, o)

    def test_link_pipeline_free_to_free(self):
        # Input
        i = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        pipe = Double() + Max9()

        # Expected
        exp = pd.DataFrame({'a': [2, 4, 6], 'b': [8, 9, 9]})

        # Test & Verify
        o = pipe.compute(i)
        pd.testing.assert_frame_equal(exp, o)
        self.assertEqual([], pipe.plug.inputs)
        self.assertEqual([], pipe.plug.outputs)

    def test_link_pipeline_free_to_restricted(self):
        # Input
        i = pd.DataFrame({'a': [10, 20, 32], 'b': [4, 5, 6]})
        pipe = Double() + Divide()

        # Expected
        exp = pd.DataFrame({'d': [2, 4, 5], 'r': [4, 0, 4]}, dtype='float')

        # Test & Verify
        o = pipe.compute(i)
        pd.testing.assert_frame_equal(exp, o)
        self.assertEqual(['a', 'b'], pipe.plug.inputs)
        self.assertEqual(['d', 'r'], pipe.plug.outputs)

    def test_link_pipeline_restricted_to_free(self):
        # Input
        i = pd.DataFrame({'a': [10, 20, 32], 'b': [4, 5, 6]})
        pipe = Divide() + Double()

        # Expected
        exp = pd.DataFrame({'d': [4, 8, 10], 'r': [4, 0, 4]}, dtype='float')

        # Test & Verify
        o = pipe.compute(i)
        pd.testing.assert_frame_equal(exp, o)
        self.assertEqual(['a', 'b'], pipe.plug.inputs)
        self.assertEqual(['d', 'r'], pipe.plug.outputs)

    def test_link_pipeline_restricted_to_restricted(self):
        # Input
        i = pd.DataFrame({'a': [10, 20, 32], 'b': [4, 5, 6]})
        pipe = Divide() + Double() + Inverse()

        # Expected
        exp = pd.DataFrame({'d': [4, 8, 10], 'r': [4, 0, 4], '-d': [-4, -8, -10]}, dtype='float')

        # Test & Verify
        o = pipe.compute(i)
        pd.testing.assert_frame_equal(exp, o)
        self.assertEqual({'a', 'b'}, set(pipe.plug.inputs))
        self.assertEqual({'d', '-d', 'r'}, set(pipe.plug.outputs))


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
        o = pipe.compute(i)
        pd.testing.assert_frame_equal(exp, o)
