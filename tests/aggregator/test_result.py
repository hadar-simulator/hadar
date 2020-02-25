import unittest
import pandas as pd

from hadar.aggregator.result import Index, TimeIndex, ResultAggregator, NodeIndex, TypeIndex, SrcIndex, DestIndex
from hadar.solver.input import *
from hadar.solver.output import *


class TestIndex(unittest.TestCase):

    def test_no_parameters(self):
        self.assertEqual(True, Index(column='i').all)

    def test_on_element(self):
        i = Index(column='i', index='fr')
        self.assertEqual(False, i.all)
        self.assertEqual(['fr'], i.index)

    def test_list(self):
        i = Index(column='i', index=['fr', 'be'])
        self.assertEqual(False, i.all)
        self.assertEqual(['fr', 'be'], i.index)

    def test_filter(self):
        i = Index(column='i', index=['fr', 'be'])
        df = pd.DataFrame(data={'i': ['it', 'fr', 'fr', 'be', 'de', 'it', 'be'],
                                'a': [0, 1, 2, 3, 4, 5, 6]})

        exp = pd.Series(data=[False, True, True, True, False, False, True], index=[0, 1, 2, 3, 4, 5, 6], name='i')

        pd.testing.assert_series_equal(exp, i.filter(df))


class TestTimeIndex(unittest.TestCase):

    def test_wrong_range(self):
        self.assertRaises(ValueError, lambda: TimeIndex(start=56))
        self.assertRaises(ValueError, lambda: TimeIndex(end=23))

    def test_range(self):
        i = TimeIndex(start=2, end=6)
        self.assertEqual(False, i.all)
        self.assertEqual([2, 3, 4, 5], i.index)

    def test_list(self):
        i = TimeIndex(index=[2, 6])
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
                            productions=[OutputProduction(cost=10, quantity=[130, 13], type='prod')],
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

    def test_build_production(self):
        # Expected
        exp = pd.DataFrame(data={'cost': [10, 10, 20, 20, 20, 20],
                                 'avail': [30, 3, 10, 1, 20, 2],
                                 'used': [130, 13, 110, 11, 120, 12],
                                 'type': ['prod', 'prod', 'prod', 'prod', 'nuclear', 'nuclear'],
                                 'node': ['a', 'a', 'b', 'b', 'b', 'b'],
                                 't': [0, 1, 0, 1, 0, 1]}, dtype=float)

        agg = ResultAggregator(study=self.study, result=self.result)
        prod = agg._build_production()

        pd.testing.assert_frame_equal(exp, prod)

    def test_build_border(self):
        # Expected
        exp = pd.DataFrame(data={'cost': [2, 2, 2, 2],
                                 'avail': [10, 1, 20, 2],
                                 'used': [110, 11, 120, 12],
                                 'src': ['a', 'a', 'a', 'a'],
                                 'dest': ['b', 'b', 'c', 'c'],
                                 't': [0, 1, 0, 1]}, dtype=float)

        agg = ResultAggregator(study=self.study, result=self.result)
        border = agg._build_border()

        pd.testing.assert_frame_equal(exp, border)

    def test_aggregate_cons(self):
        # Expected
        index = pd.MultiIndex.from_tuples((('a', 'load', 0.0), ('a', 'load', 1.0)), names=['node', 'type', 't'], )
        exp_cons = pd.DataFrame(data={'asked': [20, 2],
                                      'cost': [10 ** 6] * 2,
                                      'given': [120, 12]}, dtype=float, index=index)

        agg = ResultAggregator(study=self.study, result=self.result)
        cons = agg.agg_cons(i0=NodeIndex(index='a'), i1=TypeIndex(index='load'), i2=TimeIndex())

        pd.testing.assert_frame_equal(exp_cons, cons)

    def test_aggregate_prod(self):
        # Expected
        index = pd.MultiIndex.from_tuples((('a', 'prod', 0.0), ('a', 'prod', 1.0), ('b', 'prod', 0.0), ('b', 'prod', 1.0)),
                                          names=['node', 'type', 't'], )
        exp_cons = pd.DataFrame(data={'avail': [30, 3, 10, 1],
                                      'cost': [10, 10, 20, 20],
                                      'used': [130, 13, 110, 11]}, dtype=float, index=index)

        agg = ResultAggregator(study=self.study, result=self.result)
        cons = agg.agg_prod(i0=NodeIndex(index=['a', 'b']), i1=TypeIndex(index='prod'), i2=TimeIndex())

        pd.testing.assert_frame_equal(exp_cons, cons)

    def test_aggregate_border(self):
        # Expected
        index = pd.MultiIndex.from_tuples((('a', 'b', 0.0), ('a', 'b', 1.0), ('a', 'c', 0.0), ('a', 'c', 1.0)),
                                          names=['src', 'dest', 't'], )
        exp_cons = pd.DataFrame(data={'avail': [10, 1, 20, 2],
                                      'cost': [2, 2, 2, 2],
                                      'used': [110, 11, 120, 12]}, dtype=float, index=index)

        agg = ResultAggregator(study=self.study, result=self.result)
        cons = agg.agg_border(i0=SrcIndex(index=['a']), i1=DestIndex(index=['b', 'c']), i2=TimeIndex())

        pd.testing.assert_frame_equal(exp_cons, cons)
