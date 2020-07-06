#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest

from hadar.optimizer.input import Production, Consumption, Study
from hadar.optimizer.lp.domain import LPLink, LPConsumption, LPProduction, LPNode
from hadar.optimizer.lp.mapper import InputMapper, OutputMapper
from hadar.optimizer.output import OutputConsumption, OutputLink, OutputNode, OutputProduction, Result
from tests.optimizer.lp.ortools_mock import MockSolver, MockNumVar
from tests.utils import assert_study


class TestInputMapper(unittest.TestCase):
    def test_map_input(self):
        # Input
        study = Study(horizon=2, nb_scn=2) \
            .network()\
                .node('a')\
                    .consumption(name='load', quantity=[[10, 1], [20, 2]], cost=10)\
                    .production(name='nuclear', quantity=[[12, 2], [21, 20]], cost=10)\
                .node('be')\
                .link(src='a', dest='be', quantity=[[10, 3], [20, 30]], cost=2)\
            .build()

        s = MockSolver()

        mapper = InputMapper(solver=s, study=study)

        # Expected
        out_cons_0 = [LPConsumption(name='load', cost=10, quantity=10, variable=MockNumVar(0, 10, 'lol load on a at t=0 for scn=0'))]
        out_prod_0 = [LPProduction(name='nuclear', cost=10, quantity=12, variable=MockNumVar(0, 12.0, 'prod nuclear on a at t=0 for scn=0'))]

        out_link_0 = [LPLink(src='a', dest='be', cost=2, quantity=10, variable=MockNumVar(0, 10.0, 'link on a to be at t=0 for scn=0'))]
        out_node_0 = LPNode(consumptions=out_cons_0, productions=out_prod_0, links=out_link_0)

        self.assertEqual(out_node_0, mapper.get_var(name='a', t=0, scn=0))

        out_cons_1 = [LPConsumption(name='load', cost=10, quantity=2, variable=MockNumVar(0, 2, 'lol load on a at t=1 for scn=1'))]
        out_prod_1 = [LPProduction(name='nuclear', cost=10, quantity=20, variable=MockNumVar(0, 20.0, 'prod nuclear on a at t=1 for scn=1'))]

        out_link_1 = [LPLink(src='a', dest='be', cost=2, quantity=30, variable=MockNumVar(0, 30.0, 'link on a to be at t=1 for scn=1'))]
        out_node_1 = LPNode(consumptions=out_cons_1, productions=out_prod_1, links=out_link_1)

        self.assertEqual(out_node_1, mapper.get_var(name='a', t=1, scn=1))


class TestOutputMapper(unittest.TestCase):
    def test_map_output(self):
        # Input
        study = Study(horizon=2, nb_scn=2) \
            .network()\
                .node('a')\
                    .consumption(name='load', quantity=[[10, 1], [20, 2]], cost=10)\
                    .production(name='nuclear', quantity=[[12, 2], [21, 20]], cost=10)\
                .node('be')\
                .link(src='a', dest='be', quantity=[[10, 3], [20, 30]], cost=2)\
            .build()

        s = MockSolver()
        mapper = OutputMapper(study=study)

        out_cons_0 = [LPConsumption(name='load', cost=10, quantity=10, variable=MockNumVar(0, 5, ''))]
        out_prod_0 = [LPProduction(name='nuclear', cost=10, quantity=12, variable=MockNumVar(0, 12, ''))]

        out_link_0 = [LPLink(src='a', dest='be', cost=2, quantity=10, variable=MockNumVar(0, 8, ''))]
        mapper.set_var(name='a', t=0, scn=0,
                       vars=LPNode(consumptions=out_cons_0, productions=out_prod_0, links=out_link_0))

        out_cons_1 = [LPConsumption(name='load', cost=10, quantity=20, variable=MockNumVar(0, 5, ''))]
        out_prod_1 = [LPProduction(name='nuclear', cost=10, quantity=2, variable=MockNumVar(0, 112, ''))]

        out_link_1 = [LPLink(src='a', dest='be', cost=2, quantity=10, variable=MockNumVar(0, 18, ''))]
        mapper.set_var(name='a', t=1, scn=1,
                       vars=LPNode(consumptions=out_cons_1, productions=out_prod_1, links=out_link_1))

        # Expected
        node = OutputNode(consumptions=[OutputConsumption(name='load', quantity=[[5, 0], [0, 15]], cost=10)],
                          productions=[OutputProduction(name='nuclear', quantity=[[12, 0], [0, 112]], cost=10)],
                          links=[OutputLink(dest='be', quantity=[[8, 0], [0, 18]], cost=2)])
        expected = Result(nodes={'a': node, 'be': OutputNode(consumptions=[], productions=[], links=[])})


        assert_study(self, expected=expected, result=mapper.get_result())
