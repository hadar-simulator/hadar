import unittest
from unittest.mock import MagicMock

from hadar.solver.lp.solver import *
from hadar.solver.input import *
from hadar.solver.output import *
from hadar.solver.lp.solver import _solve
from tests.solver.lp.ortools_mock import *


class TestObjectiveBuilder(unittest.TestCase):

    def test_add_node(self):
        # Mock
        objective = MockObjective()
        solver = MockSolver()

        # Input
        consumptions = [LPConsumption(type='load', quantity=10, cost=10, variable=MockNumVar(0, 10, 'load'))]
        productions = [LPProduction(type='solar', quantity=10, cost=20, variable=MockNumVar(0, 20, 'solar'))]
        borders = [LPBorder(src='fr', dest='be', quantity=10, cost=30, variable=MockNumVar(0, 30, 'be'))]
        node = LPNode(consumptions=consumptions, productions=productions, borders=borders)

        # Expected
        coeffs = {MockNumVar(0, 10, 'load'): 10, MockNumVar(0, 20, 'solar'): 20, MockNumVar(0, 30, 'be'): 30}
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
        fr_consumptions = [LPConsumption(type='load', quantity=10, cost=10, variable=MockNumVar(0, 10, 'load'))]
        fr_productions = [LPProduction(type='solar', quantity=10, cost=20, variable=MockNumVar(0, 20, 'solar'))]
        fr_borders = [LPBorder(src='fr', dest='be', quantity=10, cost=30, variable=MockNumVar(0, 30, 'be'))]
        fr_node = LPNode(consumptions=fr_consumptions, productions=fr_productions, borders=fr_borders)

        be_node = LPNode(consumptions=[], productions=[], borders=[])

        # Expected
        fr_coeffs = {MockNumVar(0, 10, 'load'): 1, MockNumVar(0, 20, 'solar'): 1, MockNumVar(0, 30, 'be'): -1}
        fr_constraint = MockConstraint(10, 10, coeffs=fr_coeffs)

        be_coeffs = {MockNumVar(0, 30, 'be'): 1}
        be_constraint = MockConstraint(0, 0, coeffs=be_coeffs)

        # Test
        builder = AdequacyBuilder(solver=solver, horizon=1)
        builder.add_node(name='fr', node=fr_node, t=0)
        builder.add_node(name='be', node=be_node, t=0)
        builder.build()

        self.assertEqual(fr_constraint, builder.constraints[0]['fr'])
        self.assertEqual(be_constraint, builder.constraints[0]['be'])


class TestSolve(unittest.TestCase):
    def test_solve(self):
        # Input
        study = Study(node_names=['a']) \
            .add_on_node(node='a', data=Consumption(type='load', cost=10, quantity=[10]))

        # Expected
        out_a = OutputNode(consumptions=[OutputConsumption(type='load', cost=10, quantity=[10])],
                       productions=[], borders=[])
        exp_result = Result(nodes={'a': out_a})

        # Mock
        solver = MockSolver()
        solver.Solve = MagicMock()

        objective = ObjectiveBuilder(solver=solver)
        objective.add_node = MagicMock()
        objective.build = MagicMock()

        adequacy = AdequacyBuilder(solver=solver, horizon=study.horizon)
        adequacy.add_node = MagicMock()
        adequacy.build = MagicMock()

        in_cons = LPConsumption(type='load', quantity=10, cost=10, variable=MockNumVar(0, 10, 'load'))
        var = LPNode(consumptions=[in_cons], productions=[], borders=[])
        in_mapper = InputMapper(solver=solver, study=study)
        in_mapper.get_var = MagicMock(return_value=var)

        out_mapper = OutputMapper(solver=solver, study=study)
        out_mapper.set_var = MagicMock()
        out_mapper.get_result = MagicMock(return_value=exp_result)


        # Test
        res = _solve(study, solver, objective, adequacy, in_mapper, out_mapper)

        self.assertEqual(exp_result, res)

        in_mapper.get_var.assert_called_with(name='a', t=0)
        adequacy.add_node.assert_called_with(name='a', t=0, node=var)
        objective.add_node.assert_called_with(node=var)

        objective.build.assert_called_with()
        adequacy.build.assert_called_with()

        solver.Solve.assert_called_with()

        out_mapper.set_var.assert_called_with(name='a', t=0, vars=var)
