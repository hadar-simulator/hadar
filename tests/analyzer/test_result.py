#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest

import numpy as np
import pandas as pd

from hadar import LPOptimizer
from hadar.analyzer.result import Index, ResultAnalyzer, IntIndex
from hadar.optimizer.input import Production, Consumption, Study
from hadar.optimizer.output import OutputConsumption, OutputLink, OutputNode, OutputProduction, Result, OutputNetwork, \
    OutputStorage, OutputConverter


class TestIndex(unittest.TestCase):

    def test_no_parameters(self):
        self.assertEqual(True, Index(column='i').all)

    def test_on_element(self):
        i = Index(column='i', index='fr')
        self.assertEqual(False, i.all)
        self.assertEqual(('fr',), i.index)

    def test_list(self):
        i = Index(column='i', index=['fr', 'be'])
        self.assertEqual(False, i.all)
        self.assertEqual(('fr', 'be'), i.index)

    def test_filter(self):
        i = Index(column='i', index=['fr', 'be'])
        df = pd.DataFrame(data={'i': ['it', 'fr', 'fr', 'be', 'de', 'it', 'be'],
                                'a': [0, 1, 2, 3, 4, 5, 6]})

        exp = pd.Series(data=[False, True, True, True, False, False, True], index=[0, 1, 2, 3, 4, 5, 6], name='i')

        pd.testing.assert_series_equal(exp, i.filter(df))


class TestIntIndex(unittest.TestCase):

    def test_range(self):
        i = IntIndex('i', index=slice(2, 6))
        self.assertEqual(False, i.all)
        self.assertEqual((2, 3, 4, 5), i.index)

    def test_list(self):
        i = IntIndex('i', index=[2, 6])
        self.assertEqual(False, i.all)
        self.assertEqual((2, 6), i.index)


class TestConsumptionAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.study = Study(horizon=3, nb_scn=2)\
            .network()\
                .node('a')\
                    .consumption(cost=10 ** 3, quantity=[[120, 12, 12], [12, 120, 120]], name='load')\
                    .consumption(cost=10 ** 3, quantity=[[130, 13, 13], [13, 130, 130]], name='car')\
                .node('b')\
                    .consumption(cost=10 ** 3, quantity=[[120, 12, 12], [12, 120, 120]], name='load')\
            .build()

        out = {
            'a': OutputNode(consumptions=[OutputConsumption(cost=np.ones((2, 3)) * 10 ** 3, quantity=[[20, 2, 2], [2, 20, 20]], name='load'),
                                          OutputConsumption(cost=np.ones((2, 3)) * 10 ** 3, quantity=[[30, 3, 3], [3, 30, 30]], name='car')],
                            productions=[], storages=[], links=[]),
            'b': OutputNode(consumptions=[OutputConsumption(cost=np.ones((2, 3)) * 10 ** 3, quantity=[[20, 2, 2], [2, 20, 20]], name='load')],
                            productions=[], storages=[], links=[])
        }
        self.result = Result(networks={'default': OutputNetwork(nodes=out)}, converters={})

    def test_build_consumption(self):
        # Expected
        exp = pd.DataFrame(data={'cost': [10 ** 3] * 18,
                                 'asked': [120, 12, 12, 12, 120, 120, 130, 13, 13, 13, 130, 130, 120, 12, 12, 12, 120, 120],
                                 'given': [20, 2, 2, 2, 20, 20, 30, 3, 3, 3, 30, 30, 20, 2, 2, 2, 20, 20],
                                 'name': ['load'] * 6 + ['car'] * 6 + ['load'] * 6,
                                 'node': ['a'] * 12 + ['b'] * 6,
                                 'network': ['default'] * 18,
                                 't':   [0, 1, 2] * 6,
                                 'scn': [0, 0, 0, 1, 1, 1] * 3}, dtype=float)

        cons = ResultAnalyzer._build_consumption(self.study, self.result)

        pd.testing.assert_frame_equal(exp, cons)

    def test_aggregate_cons(self):
        # Expected
        index = pd.Index(data=[0, 1, 2], dtype=float, name='t')
        exp_cons = pd.DataFrame(data={'asked': [120, 12, 12],
                                      'cost': [10 ** 3] * 3,
                                      'given': [20, 2, 2]}, dtype=float, index=index)

        # Test
        agg = ResultAnalyzer(study=self.study, result=self.result)
        cons = agg.network().scn(0).node('a').consumption('load').time()

        pd.testing.assert_frame_equal(exp_cons, cons)

    def test_get_elements_inside(self):
        agg = ResultAnalyzer(study=self.study, result=self.result)
        self.assertEqual((2, 0, 0, 0, 0, 0), agg.get_elements_inside('a'))
        self.assertEqual((1, 0, 0, 0, 0, 0), agg.get_elements_inside('b'))


class TestProductionAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.study = Study(horizon=3, nb_scn=2)\
            .network()\
                .node('a')\
                    .production(cost=10, quantity=[[130, 13, 13], [13, 130, 130]], name='prod')\
                .node('b')\
                    .production(cost=20, quantity=[[110, 11, 11], [11, 110, 110]], name='prod')\
                    .production(cost=20, quantity=[[120, 12, 12], [12, 120, 120]], name='nuclear') \
            .build()

        out = {
            'a': OutputNode(productions=[OutputProduction(cost=np.ones((2, 3)) * 10, quantity=[[30, 3, 3], [3, 30, 30]], name='prod')],
                            consumptions=[], storages=[], links=[]),

            'b': OutputNode(productions=[OutputProduction(cost=np.ones((2, 3)) * 20, quantity=[[10, 1, 1], [1, 10, 10]], name='prod'),
                                         OutputProduction(cost=np.ones((2, 3)) * 20, quantity=[[20, 2, 2], [2, 20, 20]], name='nuclear')],
                            consumptions=[], storages=[], links=[])
        }

        self.result = Result(networks={'default': OutputNetwork(nodes=out)}, converters={})

    def test_build_production(self):
        # Expected
        exp = pd.DataFrame(data={'cost': [10] * 6 + [20] * 12,
                                 'avail': [130, 13, 13, 13, 130, 130, 110, 11, 11, 11, 110, 110, 120, 12, 12, 12, 120, 120],
                                 'used': [30, 3, 3, 3, 30, 30, 10, 1, 1, 1, 10, 10, 20, 2, 2, 2, 20, 20],
                                 'name': ['prod'] * 12 + ['nuclear'] * 6,
                                 'node': ['a'] * 6 + ['b'] * 12,
                                 'network': ['default'] * 18,
                                 't':   [0, 1, 2] * 6,
                                 'scn': [0, 0, 0, 1, 1, 1] * 3}, dtype=float)

        prod = ResultAnalyzer._build_production(self.study, self.result)

        pd.testing.assert_frame_equal(exp, prod)

    def test_aggregate_prod(self):
        # Expected
        index = pd.MultiIndex.from_tuples((('a', 'prod', 0.0), ('a', 'prod', 1.0), ('a', 'prod', 2,0),
                                           ('b', 'prod', 0.0), ('b', 'prod', 1.0), ('b', 'prod', 2,0)),
                                          names=['node', 'name', 't'], )
        exp_cons = pd.DataFrame(data={'avail': [130, 13, 13, 110, 11, 11],
                                      'cost': [10, 10, 10, 20, 20, 20],
                                      'used': [30, 3, 3, 10, 1, 1]}, dtype=float, index=index)

        # Test
        agg = ResultAnalyzer(study=self.study, result=self.result)
        cons = agg.network().scn(0).node(['a', 'b']).production('prod').time()

        pd.testing.assert_frame_equal(exp_cons, cons)

    def test_get_elements_inside(self):
        agg = ResultAnalyzer(study=self.study, result=self.result)
        self.assertEqual((0, 1, 0, 0, 0, 0), agg.get_elements_inside('a'))
        self.assertEqual((0, 2, 0, 0, 0, 0), agg.get_elements_inside('b'))


class TestStorageAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.study = Study(horizon=3, nb_scn=2)\
            .network()\
                .node('b')\
                    .storage(name='store', capacity=100, flow_in=10, flow_out=20, cost=1) \
            .build()

        out = {
            'b': OutputNode(storages=[OutputStorage(name='store', capacity=[[10, 1, 1], [1, 10, 10]],
                                                    flow_out=[[20, 2, 2], [2, 20, 20]],
                                                    flow_in=[[30, 3, 3], [3, 30, 30]])],
                            consumptions=[], productions=[], links=[])
        }

        self.result = Result(networks={'default': OutputNetwork(nodes=out)}, converters={})

    def test_build_storage(self):
        # Expected
        exp = pd.DataFrame(data={'max_capacity': [100] * 6,
                                 'capacity': [10, 1, 1, 1, 10, 10],
                                 'max_flow_in': [10] * 6,
                                 'flow_in': [30, 3, 3, 3, 30, 30],
                                 'max_flow_out': [20] * 6,
                                 'flow_out': [20, 2, 2, 2, 20, 20],
                                 'cost': [1] * 6,
                                 'init_capacity': [0] * 6,
                                 'eff': [.99] * 6,
                                 'name': ['store'] * 6,
                                 'node': ['b'] * 6,
                                 'network': ['default'] * 6,
                                 't': [0, 1, 2] * 2,
                                 'scn': [0, 0, 0, 1, 1, 1]}, dtype=float)

        stor = ResultAnalyzer._build_storage(self.study, self.result)
        pd.testing.assert_frame_equal(exp, stor, check_dtype=False)

    def test_aggregate_stor(self):
        # Expected
        index = pd.MultiIndex.from_tuples((('b', 'store', 0), ('b', 'store', 1), ('b', 'store', 2)),
                                          names=['node', 'name', 't'], )
        exp_stor = pd.DataFrame(data={'capacity': [10, 1, 1],
                                      'cost': [1, 1, 1],
                                      'eff': [.99] * 3,
                                      'flow_in': [30, 3, 3],
                                      'flow_out': [20, 2, 2],
                                      'init_capacity': [0] * 3,
                                      'max_capacity': [100] * 3,
                                      'max_flow_in': [10] * 3,
                                      'max_flow_out': [20] * 3}, index=index)

        # Test
        agg = ResultAnalyzer(study=self.study, result=self.result)
        stor = agg.network().scn(0).node().storage('store').time()
        pd.testing.assert_frame_equal(exp_stor, stor, check_dtype=False)

    def test_get_elements_inside(self):
        agg = ResultAnalyzer(study=self.study, result=self.result)
        self.assertEqual((0, 0, 1, 0, 0, 0), agg.get_elements_inside('b'))


class TestLinkAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.study = Study(horizon=3, nb_scn=2)\
            .network()\
                .node('a')\
                .node('b')\
                .node('c')\
                .link(src='a', dest='b', quantity=[[110, 11, 11], [11, 110, 110]], cost=2)\
                .link(src='a', dest='c', quantity=[[120, 12, 12], [12, 120, 120]], cost=2)\
            .build()

        blank_node = OutputNode(consumptions=[], productions=[], storages=[], links=[])
        out = {
            'a': OutputNode(consumptions=[], productions=[], storages=[],
                            links=[OutputLink(dest='b', quantity=[[10, 1, 1], [1, 10, 10]], cost=np.ones((2, 3)) * 2),
                                   OutputLink(dest='c', quantity=[[20, 2, 2], [2, 20, 20]], cost=np.ones((2, 3)) * 2)]),

            'b': blank_node, 'c': blank_node
        }

        self.result = Result(networks={'default': OutputNetwork(nodes=out)}, converters={})

    def test_build_link(self):
        # Expected
        exp = pd.DataFrame(data={'cost': [2] * 12,
                                 'avail': [110, 11, 11, 11, 110, 110, 120, 12, 12, 12, 120, 120],
                                 'used': [10, 1, 1, 1, 10, 10, 20, 2, 2, 2, 20, 20],
                                 'node': ['a'] * 12,
                                 'dest': ['b'] * 6 + ['c'] * 6,
                                 'network': ['default'] * 12,
                                 't':   [0, 1, 2] * 4,
                                 'scn': [0, 0, 0, 1, 1, 1] * 2}, dtype=float)

        link = ResultAnalyzer._build_link(self.study, self.result)

        pd.testing.assert_frame_equal(exp, link)

    def test_aggregate_link(self):
        # Expected
        index = pd.MultiIndex.from_tuples((('b', 0.0), ('b', 1.0), ('b', 2,0),
                                           ('c', 0.0), ('c', 1.0), ('c', 2,0)),
                                          names=['dest', 't'], )
        exp_link = pd.DataFrame(data={'avail': [110, 11, 11, 120, 12, 12],
                                      'cost': [2, 2, 2, 2, 2, 2],
                                      'used': [10, 1, 1, 20, 2, 2]}, dtype=float, index=index)

        agg = ResultAnalyzer(study=self.study, result=self.result)
        link = agg.network().scn(0).node('a').link(['b', 'c']).time()

        pd.testing.assert_frame_equal(exp_link, link)

    def test_balance(self):
        agg = ResultAnalyzer(study=self.study, result=self.result)
        np.testing.assert_array_equal([[30, 3, 3], [3, 30, 30]], agg.get_balance(node='a'))
        np.testing.assert_array_equal([[-10, -1, -1], [-1, -10, -10]], agg.get_balance(node='b'))

    def test_get_elements_inside(self):
        agg = ResultAnalyzer(study=self.study, result=self.result)
        self.assertEqual((0, 0, 0, 2, 0, 0), agg.get_elements_inside('a'))


class TestConverterAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.study = Study(horizon=3, nb_scn=2)\
            .network()\
                .node('a')\
                    .to_converter(name='conv', ratio=2)\
            .network('elec').node('a')\
            .converter(name='conv', to_network='elec', to_node='a', max=10, cost=1)\
            .build()

        conv = OutputConverter(name='conv', flow_src={('default', 'a'): [[10, 1, 1], [1, 10, 10]]}, flow_dest=[[20, 2, 2], [2, 20, 20]])

        blank_node = OutputNode(consumptions=[], productions=[], storages=[], links=[])
        self.result = Result(networks={'default': OutputNetwork(nodes={'a': blank_node}),
                                       'elec': OutputNetwork(nodes={'a': blank_node})},
                             converters={'conv': conv})

    def test_build_dest_converter(self):
        # Expected
        exp = pd.DataFrame(data={'name': ['conv'] * 6,
                                 'network': ['elec'] * 6,
                                 'node': ['a'] * 6,
                                 'flow': [20, 2, 2, 2, 20, 20],
                                 'cost': [1] * 6,
                                 'max': [10] * 6,
                                 't': [0, 1, 2] * 2,
                                 'scn': [0, 0, 0, 1, 1, 1]})

        conv = ResultAnalyzer._build_dest_converter(self.study, self.result)

        pd.testing.assert_frame_equal(exp, conv, check_dtype=False)

    def test_build_src_converter(self):
        # Expected
        exp = pd.DataFrame(data={'name': ['conv'] * 6,
                                 'network': ['default'] * 6,
                                 'node': ['a'] * 6,
                                 'ratio': [2] * 6,
                                 'flow': [10, 1, 1, 1, 10, 10],
                                 'max': [5] * 6,
                                 't': [0, 1, 2] * 2,
                                 'scn': [0, 0, 0, 1, 1, 1]})

        conv = ResultAnalyzer._build_src_converter(self.study, self.result)

        pd.testing.assert_frame_equal(exp, conv, check_dtype=False)


    def test_aggregate_to_conv(self):
        # Expected
        exp_conv = pd.DataFrame(data={'flow': [10, 1, 1],
                                      'max': [5] * 3,
                                      'ratio': [2] * 3}, index=pd.Index([0, 1, 2], name='t'))

        agg = ResultAnalyzer(study=self.study, result=self.result)
        conv = agg.network().scn(0).node('a').to_converter('conv').time()

        pd.testing.assert_frame_equal(exp_conv, conv, check_dtype=False)

    def test_aggregate_from_conv(self):
        # Expected
        exp_conv = pd.DataFrame(data={'cost': [1] * 3,
                                      'flow': [20, 2, 2],
                                      'max': [10] * 3}, index=pd.Index([0, 1, 2], name='t'))

        agg = ResultAnalyzer(study=self.study, result=self.result)
        conv = agg.network('elec').scn(0).node('a').from_converter('conv').time()

        pd.testing.assert_frame_equal(exp_conv, conv, check_dtype=False)

    def test_get_elements_inside(self):
        agg = ResultAnalyzer(study=self.study, result=self.result)
        self.assertEqual((0, 0, 0, 0, 1, 0), agg.get_elements_inside('a'))
        self.assertEqual((0, 0, 0, 0, 0, 1), agg.get_elements_inside('a', network='elec'))


class TestAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.study = Study(horizon=1)\
            .network()\
                .node('a')\
                    .consumption(cost=10 ** 3, quantity=100, name='car')\
                    .production(cost=10, quantity=70, name='prod')\
                .node('b')\
                    .production(cost=20, quantity=70, name='nuclear') \
                    .storage(name='store', capacity=100, flow_in=10, flow_out=20, cost=-1) \
                    .to_converter(name='conv', ratio=2) \
                .link(src='b', dest='a', quantity=110, cost=2)\
            .network('elec')\
                .node('a')\
                    .consumption(cost=10 ** 3, quantity=20, name='load')\
            .converter(name='conv', to_network='elec', to_node='a', max=10, cost=1)\
            .build()

        optim = LPOptimizer()
        self.result = optim.solve(self.study)

    def test_cost(self):
        agg = ResultAnalyzer(study=self.study, result=self.result)
        np.testing.assert_array_equal(700, agg.get_cost(node='a'))
        np.testing.assert_array_equal(760, agg.get_cost(node='b'))
        np.testing.assert_array_equal(10010, agg.get_cost(node='a', network='elec'))

    def test_rac(self):
        agg = ResultAnalyzer(study=self.study, result=self.result)
        np.testing.assert_array_equal(35, agg.get_rac())
        np.testing.assert_array_equal(-10, agg.get_rac(network='elec'))
