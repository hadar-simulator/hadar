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
            .add_on_node('a', data=Consumption(cost=10 ** 3, quantity=[120, 12], type='load')) \
            .add_on_node('a', data=Consumption(cost=10 ** 3, quantity=[130, 13], type='car')) \
            .add_on_node('a', data=Production(cost=10, quantity=[130, 13], type='prod')) \
            .add_on_node('b', data=Consumption(cost=10 ** 3, quantity=[120, 12], type='load')) \
            .add_on_node('b', data=Production(cost=20, quantity=[110, 11], type='prod')) \
            .add_on_node('b', data=Production(cost=20, quantity=[120, 12], type='nuclear')) \
            .add_border(src='a', dest='b', quantity=[110, 11], cost=2) \
            .add_border(src='a', dest='c', quantity=[120, 12], cost=2)

        out = {
            'a': OutputNode(consumptions=[OutputConsumption(cost=10 ** 3, quantity=[20, 2], type='load'),
                                          OutputConsumption(cost=10 ** 3, quantity=[30, 3], type='car')],
                            productions=[OutputProduction(cost=10, quantity=[30, 3], type='prod')],
                            borders=[OutputBorder(dest='b', quantity=[10, 1], cost=2),
                                     OutputBorder(dest='c', quantity=[20, 2], cost=2)]),

            'b': OutputNode(consumptions=[OutputConsumption(cost=10 ** 3, quantity=[20, 2], type='load')],
                            productions=[OutputProduction(cost=20, quantity=[10, 1], type='prod'),
                                         OutputProduction(cost=20, quantity=[20, 2], type='nuclear')],
                            borders=[])
        }

        self.result = Result(nodes=out)

    def test_build_consumption(self):
        # Expected
        exp = pd.DataFrame(data={'cost': [10 ** 3] * 6,
                                 'asked': [120, 12, 130, 13, 120, 12],
                                 'given': [20, 2, 30, 3, 20, 2],
                                 'type': ['load', 'load', 'car', 'car', 'load', 'load'],
                                 'node': ['a', 'a', 'a', 'a', 'b', 'b'],
                                 't': [0, 1, 0, 1, 0, 1]}, dtype=float)

        agg = ResultAggregator(study=self.study, result=self.result)
        cons = agg._build_consumption()

        pd.testing.assert_frame_equal(exp, cons)

    def test_build_production(self):
        # Expected
        exp = pd.DataFrame(data={'cost': [10, 10, 20, 20, 20, 20],
                                 'avail': [130, 13, 110, 11, 120, 12],
                                 'used': [30, 3, 10, 1, 20, 2],
                                 'type': ['prod', 'prod', 'prod', 'prod', 'nuclear', 'nuclear'],
                                 'node': ['a', 'a', 'b', 'b', 'b', 'b'],
                                 't': [0, 1, 0, 1, 0, 1]}, dtype=float)

        agg = ResultAggregator(study=self.study, result=self.result)
        prod = agg._build_production()

        pd.testing.assert_frame_equal(exp, prod)

    def test_build_border(self):
        # Expected
        exp = pd.DataFrame(data={'cost': [2, 2, 2, 2],
                                 'avail': [110, 11, 120, 12],
                                 'used': [10, 1, 20, 2],
                                 'src': ['a', 'a', 'a', 'a'],
                                 'dest': ['b', 'b', 'c', 'c'],
                                 't': [0, 1, 0, 1]}, dtype=float)

        agg = ResultAggregator(study=self.study, result=self.result)
        border = agg._build_border()

        pd.testing.assert_frame_equal(exp, border)

    def test_aggregate_cons(self):
        # Expected
        index = pd.Index(data=[0, 1], dtype=float, name='t')
        exp_cons = pd.DataFrame(data={'asked': [120, 12],
                                      'cost': [10 ** 3] * 2,
                                      'given': [20, 2]}, dtype=float, index=index)

        agg = ResultAggregator(study=self.study, result=self.result)
        cons = agg.agg_cons(i0=NodeIndex(index='a'), i1=TypeIndex(index='load'), i2=TimeIndex())

        pd.testing.assert_frame_equal(exp_cons, cons)

    def test_aggregate_prod(self):
        # Expected
        index = pd.MultiIndex.from_tuples((('a', 'prod', 0.0), ('a', 'prod', 1.0), ('b', 'prod', 0.0), ('b', 'prod', 1.0)),
                                          names=['node', 'type', 't'], )
        exp_cons = pd.DataFrame(data={'avail': [130, 13, 110, 11],
                                      'cost': [10, 10, 20, 20],
                                      'used': [30, 3, 10, 1]}, dtype=float, index=index)

        agg = ResultAggregator(study=self.study, result=self.result)
        cons = agg.agg_prod(i0=NodeIndex(index=['a', 'b']), i1=TypeIndex(index='prod'), i2=TimeIndex())

        pd.testing.assert_frame_equal(exp_cons, cons)

    def test_aggregate_border(self):
        # Expected
        index = pd.MultiIndex.from_tuples((('b', 0.0), ('b', 1.0), ('c', 0.0), ('c', 1.0)),
                                          names=['dest', 't'], )
        exp_cons = pd.DataFrame(data={'avail': [110, 11, 120, 12],
                                      'cost': [2, 2, 2, 2],
                                      'used': [10, 1, 20, 2]}, dtype=float, index=index)

        agg = ResultAggregator(study=self.study, result=self.result)
        cons = agg.agg_border(i0=SrcIndex(index=['a']), i1=DestIndex(index=['b', 'c']), i2=TimeIndex())

        pd.testing.assert_frame_equal(exp_cons, cons)

    def test_get_elements_inide(self):
        agg = ResultAggregator(study=self.study, result=self.result)
        self.assertEqual((2, 1, 2), agg.get_elements_inside('a'))
        self.assertEqual((1, 2, 0), agg.get_elements_inside('b'))

    def test_balance(self):
        agg = ResultAggregator(study=self.study, result=self.result)
        np.testing.assert_array_equal([30, 3], agg.get_balance(node='a'))
        np.testing.assert_array_equal([-10, -1], agg.get_balance(node='b'))

    def test_cost(self):
        agg = ResultAggregator(study=self.study, result=self.result)
        np.testing.assert_array_equal([200360, 20036], agg.get_cost(node='a'))
        np.testing.assert_array_equal([100600, 10060], agg.get_cost(node='b'))


