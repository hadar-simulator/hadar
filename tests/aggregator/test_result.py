import unittest
import pandas as pd

from hadar.aggregator.result import Index, TimeIndex, ResultAggregator
from hadar.solver.input import *
from hadar.solver.output import *


class TestIndex(unittest.TestCase):

    def test_no_parameters(self):
        self.assertEqual(True, Index().all)

    def test_on_element(self):
        i = Index(index='fr')
        self.assertEqual(False, i.all)
        self.assertEqual(['fr'], i.index)

    def test_list(self):
        i = Index(index=['fr', 'be'])
        self.assertEqual(False, i.all)
        self.assertEqual(['fr', 'be'], i.index)


class TestTimeIndex(unittest.TestCase):

    def test_wrong_range(self):
        self.assertRaises(ValueError, lambda: TimeIndex(start=56))
        self.assertRaises(ValueError, lambda: TimeIndex(end=23))

    def test_range(self):
        i = TimeIndex(start=2, end=6)
        self.assertEqual(False, i.all)
        self.assertEqual([2, 3, 4, 5], i.index)

    def test_list(self):
        i = Index(index=[2, 6])
        self.assertEqual(False, i.all)
        self.assertEqual([2, 6], i.index)


class TestAggregator(unittest.TestCase):
    def setUp(self) -> None:
        self.study = Study(['a', 'b', 'c']) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[20, 2], type='load')) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[30, 3], type='car')) \
            .add_on_node('a', data=Production(cost=10, quantity=[30, 3], type='prod')) \
            .add_on_node('b', data=Consumption(cost=10 ** 6, quantity=[20, 2], type='load')) \
            .add_on_node('b', data=Production(cost=20, quantity=[10, 1], type='prod')) \
            .add_on_node('b', data=Production(cost=20, quantity=[20, 2], type='nuclear')) \
            .add_border(src='a', dest='b', quantity=[10, 1], cost=2) \
            .add_border(src='a', dest='c', quantity=[20, 2], cost=2)

        out = {
            'a': OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[120, 12], type='load'),
                                          OutputConsumption(cost=10 ** 6, quantity=[130, 13], type='car')],
                            productions=[OutputProduction(cost=10, quantity=[130,12], type='prod')],
                            borders=[OutputBorder(dest='b', quantity=[110, 11], cost=2),
                                     OutputBorder(dest='c', quantity=[120, 12], cost=2)],
                            rac=[0, 0], cost=[0, 0]),
            'b': OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[120, 12], type='load')],
                            productions=[OutputProduction(cost=20, quantity=[110, 11], type='prod'),
                                         OutputProduction(cost=20, quantity=[120, 12], type='nuclear')],
                            borders=[], rac=[0, 0], cost=[0, 0])
        }

        self.result = Result(nodes=out)

    def test_build_consumption(self):

        # Expected
        exp = pd.DataFrame(data={'cost': [10 ** 6] * 6,
                                 'asked': [20, 2, 30, 3, 20, 2],
                                 'given': [120, 12, 130, 13, 120, 12],
                                 'type': ['load', 'load', 'car', 'car', 'load', 'load'],
                                 'node': ['a', 'a', 'a', 'a', 'b', 'b'],
                                 't': [0, 1, 0, 1, 0, 1]}, dtype=float)

        agg = ResultAggregator(study=self.study, result=self.result)
        cons = agg._build_consumption()

        pd.testing.assert_frame_equal(exp, cons)

