import unittest
from hadar.solver.lp.solver import *
from tests.solver.lp.ortools_mock import *


class TestObjectiveBuilder(unittest.TestCase):

    def test_add_node(self):
        # Mock
        objective = MockObjective()
        solver = MockSolver(objective=objective)

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
        builder = AdequacyBuilder(solver=solver)
        builder.add_node(name='fr', node=fr_node)
        builder.add_node(name='be', node=be_node)
        builder.build()

        self.assertEqual(fr_constraint, builder.constraints['fr'])
        self.assertEqual(be_constraint, builder.constraints['be'])
