#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest

import pandas as pd
import numpy as np

from hadar.aggregator.result import Index, TimeIndex, ResultAggregator, NodeIndex, TypeIndex, SrcIndex, DestIndex, \
    IntIndex
from hadar.solver.input import Production, Consumption, Study
from hadar.solver.output import OutputConsumption, OutputBorder, OutputNode, OutputProduction, Result


class TestIndex(unittest.TestCase):

    def test_no_parameters(self):
        self.assertEqual(True, Index(column='i').all)

    def test_on_element(self):
        i = Index(column='i')['fr']
        self.assertEqual(False, i.all)
        self.assertEqual(('fr',), i.index)

    def test_list_1(self):
        i = Index(column='i')['fr', 'be']
        self.assertEqual(False, i.all)
        self.assertEqual(('fr', 'be'), i.index)

    def test_list_2(self):
        l = ['fr', 'be']
        i = Index(column='i')[l]
        self.assertEqual(False, i.all)
        self.assertEqual(('fr', 'be'), i.index)

    def test_filter(self):
        i = Index(column='i')['fr', 'be']
        df = pd.DataFrame(data={'i': ['it', 'fr', 'fr', 'be', 'de', 'it', 'be'],
                                'a': [0, 1, 2, 3, 4, 5, 6]})

        exp = pd.Series(data=[False, True, True, True, False, False, True], index=[0, 1, 2, 3, 4, 5, 6], name='i')

        pd.testing.assert_series_equal(exp, i.filter(df))


class TestIntIndex(unittest.TestCase):

    def test_range(self):
        i = IntIndex('i')[2:6]
        self.assertEqual(False, i.all)
        self.assertEqual((2, 3, 4, 5), i.index)

    def test_list(self):
        i = IntIndex('i')[2, 6]
        self.assertEqual(False, i.all)
        self.assertEqual((2, 6), i.index)


class TestAggregator(unittest.TestCase):
    def setUp(self) -> None:
        self.study = Study(['a', 'b', 'c'], horizon=2, nb_scn=2) \
            .add_on_node('a', data=Consumption(cost=10 ** 3, quantity=[[120, 12], [12, 120]], type='load')) \
            .add_on_node('a', data=Consumption(cost=10 ** 3, quantity=[[130, 13], [13, 130]], type='car')) \
            .add_on_node('a', data=Production(cost=10, quantity=[[130, 13], [13, 130]], type='prod')) \
            .add_on_node('b', data=Consumption(cost=10 ** 3, quantity=[[120, 12], [12, 120]], type='load')) \
            .add_on_node('b', data=Production(cost=20, quantity=[[110, 11], [11, 110]], type='prod')) \
            .add_on_node('b', data=Production(cost=20, quantity=[[120, 12], [12, 120]], type='nuclear')) \
            .add_border(src='a', dest='b', quantity=[[110, 11], [11, 110]], cost=2) \
            .add_border(src='a', dest='c', quantity=[[120, 12], [12, 120]], cost=2)

        out = {
            'a': OutputNode(consumptions=[OutputConsumption(cost=10 ** 3, quantity=[[20, 2], [2, 20]], type='load'),
                                          OutputConsumption(cost=10 ** 3, quantity=[[30, 3], [3, 30]], type='car')],
                            productions=[OutputProduction(cost=10, quantity=[[30, 3], [3, 30]], type='prod')],
                            borders=[OutputBorder(dest='b', quantity=[[10, 1], [1, 10]], cost=2),
                                     OutputBorder(dest='c', quantity=[[20, 2], [2, 20]], cost=2)]),

            'b': OutputNode(consumptions=[OutputConsumption(cost=10 ** 3, quantity=[[20, 2], [2, 20]], type='load')],
                            productions=[OutputProduction(cost=20, quantity=[[10, 1], [1, 10]], type='prod'),
                                         OutputProduction(cost=20, quantity=[[20, 2], [2, 20]], type='nuclear')],
                            borders=[])
        }

        self.result = Result(nodes=out)

    def test_build_consumption(self):
        # Expected
        exp = pd.DataFrame(data={'cost': [10 ** 3] * 12,
                                 'asked': [120, 12, 12, 120, 130, 13, 13, 130, 120, 12, 12, 120],
                                 'given': [20, 2, 2, 20, 30, 3, 3, 30, 20, 2, 2, 20],
                                 'type': ['load', 'load', 'load', 'load', 'car', 'car', 'car', 'car', 'load', 'load', 'load', 'load'],
                                 'node': ['a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'b', 'b', 'b', 'b'],
                                 't':   [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                                 'scn': [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]}, dtype=float)

        cons = ResultAggregator._build_consumption(self.study, self.result)

        pd.testing.assert_frame_equal(exp, cons)

    def test_build_production(self):
        # Expected
        exp = pd.DataFrame(data={'cost': [10, 10, 10, 10, 20, 20, 20, 20, 20, 20, 20, 20],
                                 'avail': [130, 13, 13, 130, 110, 11, 11, 110, 120, 12, 12, 120],
                                 'used': [30, 3, 3, 30, 10, 1, 1, 10, 20, 2, 2, 20],
                                 'type': ['prod', 'prod', 'prod', 'prod', 'prod', 'prod', 'prod', 'prod','nuclear', 'nuclear','nuclear', 'nuclear'],
                                 'node': ['a', 'a', 'a', 'a', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b'],
                                 't':   [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                                 'scn': [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]}, dtype=float)

        prod = ResultAggregator._build_production(self.study, self.result)

        pd.testing.assert_frame_equal(exp, prod)

    def test_build_border(self):
        # Expected
        exp = pd.DataFrame(data={'cost': [2] * 8,
                                 'avail': [110, 11, 11, 110, 120, 12, 12, 120],
                                 'used': [10, 1, 1, 10, 20, 2, 2, 20],
                                 'src': ['a'] * 8,
                                 'dest': ['b', 'b', 'b', 'b', 'c', 'c', 'c', 'c'],
                                 't':   [0, 1, 0, 1, 0, 1, 0, 1],
                                 'scn': [0, 0, 1, 1, 0, 0, 1, 1]}, dtype=float)

        border = ResultAggregator._build_border(self.study, self.result)

        pd.testing.assert_frame_equal(exp, border)

    def test_aggregate_cons(self):
        # Expected
        index = pd.Index(data=[0, 1], dtype=float, name='t')
        exp_cons = pd.DataFrame(data={'asked': [120, 12],
                                      'cost': [10 ** 3] * 2,
                                      'given': [20, 2]}, dtype=float, index=index)

        agg = ResultAggregator(study=self.study, result=self.result)
        cons = agg.agg_cons(agg.iscn[0], agg.inode['a'], agg.itype['load'], agg.itime)

        pd.testing.assert_frame_equal(exp_cons, cons)

    def test_aggregate_prod(self):
        # Expected
        index = pd.MultiIndex.from_tuples((('a', 'prod', 0.0), ('a', 'prod', 1.0), ('b', 'prod', 0.0), ('b', 'prod', 1.0)),
                                          names=['node', 'type', 't'], )
        exp_cons = pd.DataFrame(data={'avail': [130, 13, 110, 11],
                                      'cost': [10, 10, 20, 20],
                                      'used': [30, 3, 10, 1]}, dtype=float, index=index)

        agg = ResultAggregator(study=self.study, result=self.result)
        cons = agg.agg_prod(agg.iscn[0], agg.inode['a', 'b'], agg.itype['prod'], agg.itime)

        pd.testing.assert_frame_equal(exp_cons, cons)

    def test_aggregate_border(self):
        # Expected
        index = pd.MultiIndex.from_tuples((('b', 0.0), ('b', 1.0), ('c', 0.0), ('c', 1.0)),
                                          names=['dest', 't'], )
        exp_cons = pd.DataFrame(data={'avail': [110, 11, 120, 12],
                                      'cost': [2, 2, 2, 2],
                                      'used': [10, 1, 20, 2]}, dtype=float, index=index)

        agg = ResultAggregator(study=self.study, result=self.result)
        cons = agg.agg_border(agg.iscn[0], agg.isrc['a'], agg.idest['b', 'c'], agg.itime)

        pd.testing.assert_frame_equal(exp_cons, cons)

    def test_get_elements_inide(self):
        agg = ResultAggregator(study=self.study, result=self.result)
        self.assertEqual((2, 1, 2), agg.get_elements_inside('a'))
        self.assertEqual((1, 2, 0), agg.get_elements_inside('b'))

    def test_balance(self):
        agg = ResultAggregator(study=self.study, result=self.result)
        np.testing.assert_array_equal([[30, 3], [3, 30]], agg.get_balance(node='a'))
        np.testing.assert_array_equal([[-10, -1], [-1, -10]], agg.get_balance(node='b'))

    def test_cost(self):
        agg = ResultAggregator(study=self.study, result=self.result)
        np.testing.assert_array_equal([[200360, 20036], [20036, 200360]], agg.get_cost(node='a'))
        np.testing.assert_array_equal([[100600, 10060], [10060, 100600]], agg.get_cost(node='b'))
