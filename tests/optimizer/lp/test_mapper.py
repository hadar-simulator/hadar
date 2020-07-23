#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest

from hadar.optimizer.input import Production, Consumption, Study
from hadar.optimizer.lp.domain import LPLink, LPConsumption, LPProduction, LPNode, LPStorage
from hadar.optimizer.lp.mapper import InputMapper, OutputMapper
from hadar.optimizer.output import OutputConsumption, OutputLink, OutputNode, OutputProduction, Result, OutputNetwork, \
    OutputStorage
from tests.optimizer.lp.ortools_mock import MockSolver, MockNumVar
from tests.utils import assert_study


class TestInputMapper(unittest.TestCase):
    def test_map_input(self):
        # Input
        study = Study(horizon=2, nb_scn=2) \
            .network()\
                .node('a')\
                    .consumption(name='load', quantity=[[10, 1], [20, 2]], cost=[[.01, .1], [.02, .2]])\
                    .production(name='nuclear', quantity=[[12, 2], [21, 20]], cost=[[0.12, 0.2], [0.21, 0.02]]) \
                    .storage(name='cell', capacity=10, flow_in=1, flow_out=1, cost_in=[[1, 11], [22, 2]],
                             cost_out=[[3, 33], [44, 4]], init_capacity=2, eff=.9) \
            .node('be')\
                .link(src='a', dest='be', quantity=[[10, 3], [20, 30]], cost=[[.01, .3], [.02, .03]])\
            .build()

        s = MockSolver()

        mapper = InputMapper(solver=s, study=study)

        # Expected
        suffix = 'inside network=default on node=a at t=0 for scn=0'
        out_cons_0 = [LPConsumption(name='load', cost=.01, quantity=10, variable=MockNumVar(0, 10, 'lol=load %s' % suffix))]
        out_prod_0 = [LPProduction(name='nuclear', cost=0.12, quantity=12, variable=MockNumVar(0, 12.0, 'prod=nuclear %s' % suffix))]

        out_stor_0 = [LPStorage(name='cell', capacity=10, var_capacity=MockNumVar(0, 10, 'storage_capacity=cell %s' % suffix),
                                flow_in=1, var_flow_in=MockNumVar(0, 1, 'storage_flow_in=cell %s' % suffix),
                                flow_out=1, var_flow_out=MockNumVar(0, 1, 'storage_flow_out=cell %s' % suffix),
                                cost_in=1, cost_out=3, init_capacity=2, eff=.9)]
        out_link_0 = [LPLink(src='a', dest='be', cost=.01, quantity=10, variable=MockNumVar(0, 10.0, 'link=be %s' % suffix))]
        out_node_0 = LPNode(consumptions=out_cons_0, productions=out_prod_0, storages=out_stor_0, links=out_link_0)

        self.assertEqual(out_node_0, mapper.get_var(network='default', node='a', t=0, scn=0))

        suffix = 'inside network=default on node=a at t=1 for scn=1'
        out_cons_1 = [LPConsumption(name='load', cost=.2, quantity=2, variable=MockNumVar(0, 2, 'lol=load %s' % suffix))]
        out_prod_1 = [LPProduction(name='nuclear', cost=.02, quantity=20, variable=MockNumVar(0, 20.0, 'prod=nuclear %s' % suffix))]

        out_stor_1 = [LPStorage(name='cell', capacity=10, var_capacity=MockNumVar(0, 10, 'storage_capacity=cell %s' % suffix),
                                flow_in=1, var_flow_in=MockNumVar(0, 1, 'storage_flow_in=cell %s' % suffix),
                                flow_out=1, var_flow_out=MockNumVar(0, 1, 'storage_flow_out=cell %s' % suffix),
                                cost_in=2, cost_out=4, init_capacity=2, eff=.9)]
        out_link_1 = [LPLink(src='a', dest='be', cost=.03, quantity=30, variable=MockNumVar(0, 30.0, 'link=be %s' % suffix))]
        out_node_1 = LPNode(consumptions=out_cons_1, productions=out_prod_1, storages=out_stor_1,links=out_link_1)

        self.assertEqual(out_node_1, mapper.get_var(network='default', node='a', t=1, scn=1))


class TestOutputMapper(unittest.TestCase):
    def test_map_output(self):
        # Input
        study = Study(horizon=2, nb_scn=2) \
            .network()\
                .node('a')\
                    .consumption(name='load', quantity=[[10, 1], [20, 2]], cost=[[.01, .1], [.02, .2]])\
                    .production(name='nuclear', quantity=[[12, 2], [21, 20]], cost=[[0.12, 0.2], [0.21, 0.02]]) \
                    .storage(name='cell', capacity=10, flow_in=1, flow_out=1, cost_in=[[1, 11], [22, 2]],
                             cost_out=[[3, 33], [44, 4]], init_capacity=2, eff=.9) \
            .node('be')\
                .link(src='a', dest='be', quantity=[[10, 3], [20, 30]], cost=[[.01, .3], [.02, .03]])\
            .build()

        s = MockSolver()
        mapper = OutputMapper(study=study)

        out_cons_0 = [LPConsumption(name='load', cost=.01, quantity=10, variable=MockNumVar(0, 5, ''))]
        out_prod_0 = [LPProduction(name='nuclear', cost=.12, quantity=12, variable=MockNumVar(0, 12, ''))]
        out_stor_0 = [LPStorage(name='cell', capacity=10, flow_in=1, flow_out=1, init_capacity=2, eff=.9,
                                cost_in=[[1, 11], [22, 2]], cost_out=[[3, 33], [44, 4]],
                                var_capacity=MockNumVar(0, 5, ''),
                                var_flow_in=MockNumVar(0, 2, ''),
                                var_flow_out=MockNumVar(0, 4, ''))]
        out_link_0 = [LPLink(src='a', dest='be', cost=.01, quantity=10, variable=MockNumVar(0, 8, ''))]
        mapper.set_var(network='default', node='a', t=0, scn=0,
                       vars=LPNode(consumptions=out_cons_0, productions=out_prod_0, storages=out_stor_0, links=out_link_0))

        out_cons_1 = [LPConsumption(name='load', cost=.2, quantity=20, variable=MockNumVar(0, 5, ''))]
        out_prod_1 = [LPProduction(name='nuclear', cost=.21, quantity=2, variable=MockNumVar(0, 112, ''))]
        out_stor_1 = [LPStorage(name='cell', capacity=10, flow_in=1, flow_out=1, init_capacity=2, eff=.9,
                                cost_in=[[1, 11], [22, 2]], cost_out=[[3, 33], [44, 4]],
                                var_capacity=MockNumVar(0, 55, ''),
                                var_flow_in=MockNumVar(0, 22, ''),
                                var_flow_out=MockNumVar(0, 44, ''))]
        out_link_1 = [LPLink(src='a', dest='be', cost=.02, quantity=10, variable=MockNumVar(0, 18, ''))]
        mapper.set_var(network='default', node='a', t=1, scn=1,
                       vars=LPNode(consumptions=out_cons_1, productions=out_prod_1, storages=out_stor_1, links=out_link_1))

        # Expected
        node = OutputNode(consumptions=[OutputConsumption(name='load', quantity=[[5, 0], [0, 15]], cost=[[.01, .1], [.02, .2]])],
                          productions=[OutputProduction(name='nuclear', quantity=[[12, 0], [0, 112]], cost=[[0.12, 0.2], [0.21, 0.02]])],
                          storages=[OutputStorage(name='cell', capacity=[[5, 0], [0, 55]], flow_in=[[2, 0], [0, 22]],
                                                  flow_out=[[4, 0], [0, 44]])],
                          links=[OutputLink(dest='be', quantity=[[8, 0], [0, 18]], cost=[[.01, .3], [.02, .03]])])
        nodes = {'a': node, 'be': OutputNode(consumptions=[], productions=[], storages=[], links=[])}
        expected = Result(networks={'default': OutputNetwork(nodes=nodes)})

        assert_study(self, expected=expected, result=mapper.get_result())
