import unittest
import pandas as pd
import numpy as np

from hadar.preprocessing.pipeline import Pipeline


class Double(Pipeline):
    def _process(self, timelines: pd.DataFrame) -> pd.DataFrame:
        return timelines * 2


class Max9(Pipeline):
    def _process(self, timelines: pd.DataFrame) -> pd.DataFrame:
        return timelines.clip(None, 9)


class Divide(Pipeline):
    def __init__(self):
        Pipeline.__init__(self, mandatory_fields=['a', 'b'], created_fields=['d', 'r'])

    def _process(self, timelines: pd.DataFrame) -> pd.DataFrame:
        timelines['d'] = (timelines['a'] / timelines['b']).apply(np.floor)
        timelines['r'] = timelines['a'] - timelines['b'] * timelines['d']
        return timelines.drop(['a', 'b'], axis=1)


class Inverse(Pipeline):
    def __init__(self):
        Pipeline.__init__(self, mandatory_fields=['d'], created_fields=['d', '-d'])

    def _process(self, timelines: pd.DataFrame) -> pd.DataFrame:
        timelines['-d'] = -timelines['d']
        return timelines


class TestPipeline(unittest.TestCase):

    def test_compute_without_scenario(self):
        # Input
        i = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        pipe = Double()

        # Expected
        exp = pd.DataFrame({'a': [2, 4, 6], 'b': [8, 10, 12]})

        # Test & Verify
        o = pipe.compute(i)
        pd.testing.assert_frame_equal(exp, o)

    def test_compute_with_scenario(self):
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
        self.assertEqual([], pipe.input_fields)
        self.assertEqual([], pipe.output_fields)

    def test_link_pipeline_free_to_restricted(self):
        # Input
        i = pd.DataFrame({'a': [10, 20, 32], 'b': [4, 5, 6]})
        pipe = Double() + Divide()

        # Expected
        exp = pd.DataFrame({'d': [2, 4, 5], 'r': [4, 0, 4]}, dtype='float')

        # Test & Verify
        o = pipe.compute(i)
        pd.testing.assert_frame_equal(exp, o)
        self.assertEqual(['a', 'b'], pipe.input_fields)
        self.assertEqual(['d', 'r'], pipe.output_fields)

    def test_link_pipeline_restricted_to_free(self):
        # Input
        i = pd.DataFrame({'a': [10, 20, 32], 'b': [4, 5, 6]})
        pipe = Divide() + Double()

        # Expected
        exp = pd.DataFrame({'d': [4, 8, 10], 'r': [4, 0, 4]}, dtype='float')

        # Test & Verify
        o = pipe.compute(i)
        pd.testing.assert_frame_equal(exp, o)
        self.assertEqual(['a', 'b'], pipe.input_fields)
        self.assertEqual(['d', 'r'], pipe.output_fields)

    def test_link_pipeline_restricted_to_restricted(self):
        # Input
        i = pd.DataFrame({'a': [10, 20, 32], 'b': [4, 5, 6]})
        pipe = Divide() + Double() + Inverse()

        # Expected
        exp = pd.DataFrame({'d': [4, 8, 10], 'r': [4, 0, 4], '-d': [-4, -8, -10]}, dtype='float')

        # Test & Verify
        o = pipe.compute(i)
        pd.testing.assert_frame_equal(exp, o)
        self.assertEqual({'a', 'b'}, set(pipe.input_fields))
        self.assertEqual({'d', '-d', 'r'}, set(pipe.output_fields))

    def test_linkable(self):
        self.assertTrue(Divide()._linkable_io(Inverse()))
        self.assertTrue(Divide()._linkable_io(Double()))
        self.assertTrue(Double()._linkable_io(Divide()))

        self.assertFalse(Inverse()._linkable_io(Divide()))

    def test_merge_io_restricted(self):
        # Input
        pipeA = Divide()
        pipeB = Inverse()

        # Expected
        exp = ['r', 'd', '-d']

        # Test
        pipeA._merge_io(pipeB)
        self.assertEqual(exp, pipeA.output_fields)

