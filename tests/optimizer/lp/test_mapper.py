#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest

from hadar.optimizer.input import Production, Consumption, Study
from hadar.optimizer.lp.domain import LPLink, LPConsumption, LPProduction, LPNode, LPStorage, LPConverter, LPNetwork
from hadar.optimizer.lp.mapper import InputMapper, OutputMapper
from hadar.optimizer.output import OutputConsumption, OutputLink, OutputNode, OutputProduction, Result, OutputNetwork, \
    OutputStorage, OutputConverter
from tests.optimizer.lp.ortools_mock import MockSolver, MockNumVar
from tests.utils import assert_result


class TestInputMapper(unittest.TestCase):
    def test_map_consumption(self):
        # Input
        study = Study(horizon=2, nb_scn=2) \
            .network()\
                .node('a')\
                    .consumption(name='load', quantity=[[10, 1], [20, 2]], cost=[[.01, .1], [.02, .2]])\
            .build()

        s = MockSolver()

        mapper = InputMapper(solver=s, study=study)

        # Expected
        suffix = 'inside network=default on node=a at t=0 for scn=0'
        out_cons_0 = [LPConsumption(name='load', cost=.01, quantity=10, variable=MockNumVar(0, 10, 'lol=load %s' % suffix))]
        out_node_0 = LPNode(consumptions=out_cons_0, productions=[], storages=[], links=[])

        self.assertEqual(out_node_0, mapper.get_node_var(network='default', node='a', t=0, scn=0))

        suffix = 'inside network=default on node=a at t=1 for scn=1'
        out_cons_1 = [LPConsumption(name='load', cost=.2, quantity=2, variable=MockNumVar(0, 2, 'lol=load %s' % suffix))]
        out_node_1 = LPNode(consumptions=out_cons_1, productions=[], storages=[], links=[])

        self.assertEqual(out_node_1, mapper.get_node_var(network='default', node='a', t=1, scn=1))

    def test_map_production(self):
        # Input
        study = Study(horizon=2, nb_scn=2) \
            .network() \
                .node('a') \
                    .production(name='nuclear', quantity=[[12, 2], [21, 20]], cost=[[0.12, 0.2], [0.21, 0.02]]) \
            .build()

        s = MockSolver()

        mapper = InputMapper(solver=s, study=study)

        # Expected
        suffix = 'inside network=default on node=a at t=0 for scn=0'
        out_prod_0 = [LPProduction(name='nuclear', cost=0.12, quantity=12, variable=MockNumVar(0, 12.0, 'prod=nuclear %s' % suffix))]
        out_node_0 = LPNode(consumptions=[], productions=out_prod_0, storages=[], links=[])

        self.assertEqual(out_node_0, mapper.get_node_var(network='default', node='a', t=0, scn=0))

        suffix = 'inside network=default on node=a at t=1 for scn=1'

        out_prod_1 = [LPProduction(name='nuclear', cost=.02, quantity=20, variable=MockNumVar(0, 20.0, 'prod=nuclear %s' % suffix))]
        out_node_1 = LPNode(consumptions=[], productions=out_prod_1, storages=[], links=[])

        self.assertEqual(out_node_1, mapper.get_node_var(network='default', node='a', t=1, scn=1))

    def test_map_storage(self):
        # Input
        study = Study(horizon=2, nb_scn=2) \
            .network()\
                .node('a')\
                    .storage(name='cell', capacity=10, flow_in=1, flow_out=1, cost=1, init_capacity=2, eff=.9) \
            .build()

        s = MockSolver()

        mapper = InputMapper(solver=s, study=study)

        # Expected
        suffix = 'inside network=default on node=a at t=0 for scn=0'
        out_stor_0 = [LPStorage(name='cell', capacity=10, var_capacity=MockNumVar(0, 10, 'storage_capacity=cell %s' % suffix),
                                flow_in=1, var_flow_in=MockNumVar(0, 1, 'storage_flow_in=cell %s' % suffix),
                                flow_out=1, var_flow_out=MockNumVar(0, 1, 'storage_flow_out=cell %s' % suffix),
                                cost=1, init_capacity=2, eff=.9)]
        out_node_0 = LPNode(consumptions=[], productions=[], storages=out_stor_0, links=[])

        self.assertEqual(out_node_0, mapper.get_node_var(network='default', node='a', t=0, scn=0))

        suffix = 'inside network=default on node=a at t=1 for scn=1'
        out_stor_1 = [LPStorage(name='cell', capacity=10, var_capacity=MockNumVar(0, 10, 'storage_capacity=cell %s' % suffix),
                                flow_in=1, var_flow_in=MockNumVar(0, 1, 'storage_flow_in=cell %s' % suffix),
                                flow_out=1, var_flow_out=MockNumVar(0, 1, 'storage_flow_out=cell %s' % suffix),
                                cost=1, init_capacity=2, eff=.9)]
        out_node_1 = LPNode(consumptions=[], productions=[], storages=out_stor_1, links=[])

        self.assertEqual(out_node_1, mapper.get_node_var(network='default', node='a', t=1, scn=1))

    def test_map_links(self):
        # Input
        study = Study(horizon=2, nb_scn=2) \
            .network()\
                .node('a')\
                .node('be')\
                    .link(src='a', dest='be', quantity=[[10, 3], [20, 30]], cost=[[.01, .3], [.02, .03]])\
            .build()

        s = MockSolver()

        mapper = InputMapper(solver=s, study=study)

        # Expected
        suffix = 'inside network=default on node=a at t=0 for scn=0'
        out_link_0 = [LPLink(src='a', dest='be', cost=.01, quantity=10, variable=MockNumVar(0, 10.0, 'link=be %s' % suffix))]
        out_node_0 = LPNode(consumptions=[], productions=[], storages=[], links=out_link_0)

        self.assertEqual(out_node_0, mapper.get_node_var(network='default', node='a', t=0, scn=0))

        suffix = 'inside network=default on node=a at t=1 for scn=1'
        out_link_1 = [LPLink(src='a', dest='be', cost=.03, quantity=30, variable=MockNumVar(0, 30.0, 'link=be %s' % suffix))]
        out_node_1 = LPNode(consumptions=[], productions=[], storages=[],links=out_link_1)

        self.assertEqual(out_node_1, mapper.get_node_var(network='default', node='a', t=1, scn=1))

    def test_map_converter(self):
        # Mock
        s = MockSolver()

        # Input
        study = Study(horizon=1)\
            .network('gas')\
                .node('a')\
                    .to_converter(name='conv', ratio=.5)\
            .network()\
                .node('b')\
            .converter(name='conv', to_network='default', to_node='b', max=100)\
            .build()

        mapper = InputMapper(solver=s, study=study)

        # Expected
        suffix = 'at t=0 for scn=0'
        out_conv_0 = LPConverter(name='conv', src_ratios={('gas', 'a'): 0.5}, dest_network='default', dest_node='b',
                                  cost=0, max=100,
                                  var_flow_dest=MockNumVar(0, 100, 'flow_dest conv %s' % suffix),
                                  var_flow_src={('gas', 'a'): MockNumVar(0, 200, 'flow_src conv gas:a %s' % suffix)})

        self.assertEqual(out_conv_0, mapper.get_conv_var(name='conv', t=0, scn=0))


class TestOutputMapper(unittest.TestCase):
    def test_map_consumption(self):
        # Input
        study = Study(horizon=2, nb_scn=2) \
            .network()\
                .node('a')\
                    .consumption(name='load', quantity=[[10, 1], [20, 2]], cost=[[.01, .1], [.02, .2]])\
            .build()

        mapper = OutputMapper(study=study)

        out_cons_0 = [LPConsumption(name='load', cost=.01, quantity=10, variable=MockNumVar(0, 5, ''))]
        mapper.set_node_var(network='default', node='a', t=0, scn=0,
                            vars=LPNode(consumptions=out_cons_0, productions=[], storages=[], links=[]))

        out_cons_1 = [LPConsumption(name='load', cost=.2, quantity=20, variable=MockNumVar(0, 5, ''))]
        mapper.set_node_var(network='default', node='a', t=1, scn=1,
                            vars=LPNode(consumptions=out_cons_1, productions=[], storages=[], links=[]))

        # Expected
        cons = OutputConsumption(name='load', quantity=[[5, 0], [0, 15]], cost=[[.01, .1], [.02, .2]])
        nodes = {'a': OutputNode(consumptions=[cons], productions=[], storages=[], links=[])}
        expected = Result(networks={'default': OutputNetwork(nodes=nodes)}, converters={})

        assert_result(self, expected=expected, result=mapper.get_result())

    def test_map_production(self):
        # Input
        study = Study(horizon=2, nb_scn=2) \
            .network()\
                .node('a')\
                    .production(name='nuclear', quantity=[[12, 2], [21, 20]], cost=[[0.12, 0.2], [0.21, 0.02]]) \
            .build()

        mapper = OutputMapper(study=study)

        out_prod_0 = [LPProduction(name='nuclear', cost=.12, quantity=12, variable=MockNumVar(0, 12, ''))]
        mapper.set_node_var(network='default', node='a', t=0, scn=0,
                            vars=LPNode(consumptions=[], productions=out_prod_0, storages=[], links=[]))

        out_prod_1 = [LPProduction(name='nuclear', cost=.21, quantity=2, variable=MockNumVar(0, 112, ''))]
        mapper.set_node_var(network='default', node='a', t=1, scn=1,
                            vars=LPNode(consumptions=[], productions=out_prod_1, storages=[], links=[]))

        # Expected
        prod = OutputProduction(name='nuclear', quantity=[[12, 0], [0, 112]], cost=[[0.12, 0.2], [0.21, 0.02]])
        nodes = {'a': OutputNode(consumptions=[], productions=[prod], storages=[], links=[])}
        expected = Result(networks={'default': OutputNetwork(nodes=nodes)}, converters={})

        assert_result(self, expected=expected, result=mapper.get_result())

    def test_map_storage(self):
        # Input
        study = Study(horizon=2, nb_scn=2) \
            .network()\
                .node('a')\
                    .storage(name='cell', capacity=10, flow_in=1, flow_out=1, cost=1, init_capacity=2, eff=.9) \
            .build()

        mapper = OutputMapper(study=study)

        out_stor_0 = [LPStorage(name='cell', capacity=10, flow_in=1, flow_out=1, init_capacity=2, eff=.9, cost=1,
                                var_capacity=MockNumVar(0, 5, ''),
                                var_flow_in=MockNumVar(0, 2, ''),
                                var_flow_out=MockNumVar(0, 4, ''))]
        mapper.set_node_var(network='default', node='a', t=0, scn=0,
                            vars=LPNode(consumptions=[], productions=[], storages=out_stor_0, links=[]))

        out_stor_1 = [LPStorage(name='cell', capacity=10, flow_in=1, flow_out=1, init_capacity=2, eff=.9, cost=1,
                                var_capacity=MockNumVar(0, 55, ''),
                                var_flow_in=MockNumVar(0, 22, ''),
                                var_flow_out=MockNumVar(0, 44, ''))]
        mapper.set_node_var(network='default', node='a', t=1, scn=1,
                            vars=LPNode(consumptions=[], productions=[], storages=out_stor_1, links=[]))

        # Expected
        stor = OutputStorage(name='cell', capacity=[[5, 0], [0, 55]], flow_in=[[2, 0], [0, 22]], flow_out=[[4, 0], [0, 44]])
        nodes = {'a': OutputNode(consumptions=[], productions=[], storages=[stor], links=[])}
        expected = Result(networks={'default': OutputNetwork(nodes=nodes)}, converters={})

        assert_result(self, expected=expected, result=mapper.get_result())

    def test_map_link(self):
        # Input
        study = Study(horizon=2, nb_scn=2) \
            .network()\
                .node('a')\
                .node('be')\
                .link(src='a', dest='be', quantity=[[10, 3], [20, 30]], cost=[[.01, .3], [.02, .03]])\
            .build()

        mapper = OutputMapper(study=study)

        out_link_0 = [LPLink(src='a', dest='be', cost=.01, quantity=10, variable=MockNumVar(0, 8, ''))]
        mapper.set_node_var(network='default', node='a', t=0, scn=0,
                            vars=LPNode(consumptions=[], productions=[], storages=[], links=out_link_0))

        out_link_1 = [LPLink(src='a', dest='be', cost=.02, quantity=10, variable=MockNumVar(0, 18, ''))]
        mapper.set_node_var(network='default', node='a', t=1, scn=1,
                            vars=LPNode(consumptions=[], productions=[], storages=[], links=out_link_1))

        # Expected
        link = OutputLink(dest='be', quantity=[[8, 0], [0, 18]], cost=[[.01, .3], [.02, .03]])
        nodes = {'a': OutputNode(consumptions=[], productions=[], storages=[], links=[link]),
                 'be': OutputNode(consumptions=[], productions=[], storages=[], links=[])}
        expected = Result(networks={'default': OutputNetwork(nodes=nodes)}, converters={})

        assert_result(self, expected=expected, result=mapper.get_result())

    def test_map_converter(self):
        # Input
        study = Study(horizon=1)\
            .network('gas')\
                .node('a')\
                    .to_converter(name='conv', ratio=.5)\
            .network()\
                .node('b')\
            .converter(name='conv', to_network='default', to_node='b', max=100)\
            .build()

        # Expected
        exp = OutputConverter(name='conv', flow_src={('gas', 'a'): [[200]]}, flow_dest=[[100]])
        blank_node = OutputNode(consumptions=[], productions=[], storages=[], links=[])
        mapper = OutputMapper(study=study)
        vars = LPConverter(name='conv', src_ratios={('gas', 'a'): 0.5}, dest_network='default', dest_node='b',
                    cost=0, max=100,
                    var_flow_dest=MockNumVar(0, 100, 'flow_dest conv %s'),
                    var_flow_src={('gas', 'a'): MockNumVar(0, 200, 'flow_src conv gas:a %s')})
        mapper.set_converter_var(name='conv', t=0, scn=0, vars=vars)

        res = mapper.get_result()
        self.assertEqual(Result(networks={'gas': OutputNetwork(nodes={'a': blank_node}),
                                          'default': OutputNetwork(nodes={'b': blank_node})},
                                converters={'conv': exp}), res)

