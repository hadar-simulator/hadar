#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import pickle
import unittest
from unittest.mock import MagicMock

from hadar.optimizer.input import Study, Consumption
from hadar.optimizer.lp.domain import LPConsumption, LPProduction, LPLink, LPNode, SerializableVariable, LPStorage
from hadar.optimizer.lp.mapper import InputMapper, OutputMapper
from hadar.optimizer.lp.optimizer import ObjectiveBuilder, AdequacyBuilder, _solve_batch, StorageBuilder
from hadar.optimizer.lp.optimizer import solve_lp
from hadar.optimizer.output import OutputConsumption, OutputNode, Result, OutputNetwork
from tests.optimizer.lp.ortools_mock import MockConstraint, MockNumVar, MockObjective, MockSolver


class TestObjectiveBuilder(unittest.TestCase):

    def test_add_node(self):
        # Mock
        objective = MockObjective()
        solver = MockSolver()

        # Input
        consumptions = [LPConsumption(name='load', quantity=10, cost=10, variable=MockNumVar(0, 10, 'load'))]
        productions = [LPProduction(name='solar', quantity=10, cost=20, variable=MockNumVar(0, 20, 'solar'))]
        storages = [LPStorage(name='cell', capacity=10, var_capacity=MockNumVar(0, 10, 'cell_capacity'),
                              flow_in=1, var_flow_in=MockNumVar(0, 1, 'cell_flow_in'), cost_in=1,
                              flow_out=10, var_flow_out=MockNumVar(0, 10, 'cell_flow_out'), cost_out=10,
                              init_capacity=2, eff=1.2
                              )]
        links = [LPLink(src='fr', dest='be', quantity=10, cost=30, variable=MockNumVar(0, 30, 'be'))]
        node = LPNode(consumptions=consumptions, productions=productions, storages=storages, links=links)

        # Expected
        coeffs = {MockNumVar(0, 10, 'load'): 10, MockNumVar(0, 20, 'solar'): 20, MockNumVar(0, 30, 'be'): 30,
                  MockNumVar(0, 1, 'cell_flow_in'): 1, MockNumVar(0, 10, 'cell_flow_out'): 10}
        expected = MockObjective(min=True, coeffs=coeffs)

        # Test
        builder = ObjectiveBuilder(solver=solver)
        builder.add_node(node)
        builder.build()

        self.assertEqual(expected, builder.objective)


class TestAdequacyBuilder(unittest.TestCase):

    def test_add_node(self):
        # Mock
        solver = MockSolver()

        # Input
        fr_consumptions = [LPConsumption(name='load', quantity=10, cost=10, variable=MockNumVar(0, 10, 'load'))]
        fr_productions = [LPProduction(name='solar', quantity=10, cost=20, variable=MockNumVar(0, 20, 'solar'))]
        fr_storages = [LPStorage(name='cell', capacity=10, var_capacity=MockNumVar(0, 10, 'cell_capacity'),
                                 flow_in=1, var_flow_in=MockNumVar(0, 1, 'cell_flow_in'), cost_in=1,
                                 flow_out=10, var_flow_out=MockNumVar(0, 10, 'cell_flow_out'), cost_out=10,
                                 init_capacity=2, eff=1.2)]
        fr_links = [LPLink(src='fr', dest='be', quantity=10, cost=30, variable=MockNumVar(0, 30, 'be'))]
        fr_node = LPNode(consumptions=fr_consumptions, productions=fr_productions, storages=fr_storages, links=fr_links)

        be_node = LPNode(consumptions=[], productions=[], storages=[], links=[])

        # Expected
        fr_coeffs = {MockNumVar(0, 10, 'load'): 1, MockNumVar(0, 20, 'solar'): 1,
                     MockNumVar(0, 1, 'cell_flow_in'): -1, MockNumVar(0, 10, 'cell_flow_out'): 1,
                     MockNumVar(0, 30, 'be'): -1}
        fr_constraint = MockConstraint(10, 10, coeffs=fr_coeffs)

        be_coeffs = {MockNumVar(0, 30, 'be'): 1}
        be_constraint = MockConstraint(0, 0, coeffs=be_coeffs)

        # Test
        builder = AdequacyBuilder(solver=solver)
        builder.add_node(name_network='default', name_node='fr', node=fr_node, t=0)
        builder.add_node(name_network='default', name_node='be', node=be_node, t=0)
        builder.build()

        self.assertEqual(fr_constraint, builder.constraints[(0, 'default', 'fr')])
        self.assertEqual(be_constraint, builder.constraints[(0, 'default', 'be')])


class TestStorageBuilder(unittest.TestCase):
    def test_t0(self):
        # Mock
        solver = MockSolver()

        # Input
        c0 = MockNumVar(0, 10, 'cell_capacity')
        storages = [LPStorage(name='cell', capacity=10, var_capacity=c0,
                                 flow_in=1, var_flow_in=MockNumVar(0, 1, 'cell_flow_in'), cost_in=1,
                                 flow_out=10, var_flow_out=MockNumVar(0, 10, 'cell_flow_out'), cost_out=10,
                                 init_capacity=2, eff=1.2)]
        node = LPNode(consumptions=[], productions=[], storages=storages, links=[])

        # Expected
        coeffs = {MockNumVar(0, 1, 'cell_flow_in'): -1.2, MockNumVar(0, 10, 'cell_flow_out'): 1,
                  c0: 1}
        constraint = MockConstraint(2, 2, coeffs=coeffs)

        # Test
        builder = StorageBuilder(solver=solver)
        res = builder.add_node(name_network='default', name_node='fr', node=node, t=0)

        self.assertEqual(constraint, res)
        self.assertEqual(builder.capacities[(0, 'default', 'fr', 'cell')], c0)

    def test(self):
        # Mock
        solver = MockSolver()

        # Input
        storages = [LPStorage(name='cell', capacity=10, var_capacity=MockNumVar(0, 10, 'cell_capacity at 1'),
                                 flow_in=1, var_flow_in=MockNumVar(0, 1, 'cell_flow_in'), cost_in=1,
                                 flow_out=10, var_flow_out=MockNumVar(0, 10, 'cell_flow_out'), cost_out=10,
                                 init_capacity=2, eff=1.2)]
        node = LPNode(consumptions=[], productions=[], storages=storages, links=[])

        c0 = MockNumVar(0, 11, 'cell_capacity at 0')
        c1 = MockNumVar(0, 10, 'cell_capacity at 1')

        # Expected
        coeffs = {MockNumVar(0, 1, 'cell_flow_in'): -1.2, MockNumVar(0, 10, 'cell_flow_out'): 1,
                  c0: -1, c1: 1}
        constraint = MockConstraint(0, 0, coeffs=coeffs)

        # Test
        builder = StorageBuilder(solver=solver)
        builder.capacities[(0, 'default', 'fr', 'cell')] = c0
        res = builder.add_node(name_network='default', name_node='fr', node=node, t=1)

        self.assertEqual(constraint, res)
        self.assertEqual(c1, builder.capacities[(1, 'default', 'fr', 'cell')])


class TestSolve(unittest.TestCase):
    def test_solve_batch(self):
        # Input
        study = Study(horizon=1, nb_scn=1) \
            .network().node('a').consumption(name='load', cost=10, quantity=10).build()

        # Mock
        solver = MockSolver()
        solver.Solve = MagicMock()

        objective = ObjectiveBuilder(solver=solver)
        objective.add_node = MagicMock()
        objective.build = MagicMock()

        adequacy = AdequacyBuilder(solver=solver)
        adequacy.add_node = MagicMock()
        adequacy.build = MagicMock()

        storage = StorageBuilder(solver=solver)
        storage.add_node = MagicMock()
        storage.build = MagicMock()

        in_cons = LPConsumption(name='load', quantity=10, cost=10, variable=MockNumVar(0, 10, 'load'))
        var = LPNode(consumptions=[in_cons], productions=[], storages=[], links=[])
        in_mapper = InputMapper(solver=solver, study=study)
        in_mapper.get_var = MagicMock(return_value=var)

        # Expected
        in_cons = LPConsumption(name='load', quantity=10, cost=10, variable=SerializableVariable(MockNumVar(0, 10, 'load')))
        exp_var = LPNode(consumptions=[in_cons], productions=[], storages=[], links=[])

        # Test
        res = _solve_batch((study, 0, solver, objective, adequacy, storage, in_mapper))

        self.assertEqual([{'default': {'a': exp_var}}], pickle.loads(res))
        in_mapper.get_var.assert_called_with(network='default', node='a', t=0, scn=0)
        adequacy.add_node.assert_called_with(name_network='default', name_node='a', t=0, node=var)
        storage.add_node.assert_called_with(name_network='default', name_node='a', t=0, node=var)
        objective.add_node.assert_called_with(node=var)

        objective.build.assert_called_with()
        adequacy.build.assert_called_with()

        solver.Solve.assert_called_with()

    def test_solve(self):
        # Input
        study = Study(horizon=1, nb_scn=1) \
            .network().node('a').consumption(name='load', cost=10, quantity=10).build()

        # Expected
        out_a = OutputNode(consumptions=[OutputConsumption(name='load', cost=10, quantity=[0])],
                           productions=[], storages=[], links=[])
        exp_result = Result(networks={'default': OutputNetwork(nodes={'a': out_a})})

        in_cons = LPConsumption(name='load', quantity=10, cost=10, variable=SerializableVariable(MockNumVar(0, 10, '')))
        exp_var = LPNode(consumptions=[in_cons], productions=[], storages=[], links=[])

        # Mock
        out_mapper = OutputMapper(study=study)
        out_mapper.set_var = MagicMock()
        out_mapper.get_result = MagicMock(return_value=exp_result)

        # Test
        res = solve_lp(study, out_mapper)

        self.assertEqual(exp_result, res)
        out_mapper.set_var.assert_called_with(network='default', node='a', t=0, scn=0, vars=exp_var)
