import unittest

from ortools.linear_solver import pywraplp
from hadar.solver.lp.domain import *
from hadar.solver.lp.mapper import InputMapper, OutputMapper
from hadar.solver.input import *
from hadar.solver.output import *
from tests.solver.lp.ortools_mock import MockSolver, MockNumVar
from tests.utils import assert_study


class TestInputMapper(unittest.TestCase):
    def test_map_input(self):
        # Input
        study = Study(['a', 'be']) \
            .add_on_node('a', Consumption(type='load', quantity=[10], cost=10)) \
            .add_on_node('a', Production(type='nuclear', quantity=[12], cost=10)) \
            .add_border(src='a', dest='be', quantity=[10], cost=2)

        s = MockSolver()

        mapper = InputMapper(solver=s, study=study)

        # Expected
        out_cons = [LPConsumption(type='load', cost=10, quantity=10, variable=MockNumVar(0, 10, 'lol load on a'))]
        out_prod = [LPProduction(type='nuclear', cost=10, quantity=12, variable=MockNumVar(0, 12.0, 'prod nuclear on a'))]

        out_bord = [LPBorder(src='a', dest='be', cost=2, quantity=10, variable=MockNumVar(0, 10.0, 'border on a to be'))]
        out_node = LPNode(consumptions=out_cons, productions=out_prod, borders=out_bord)

        self.assertEqual(out_node, mapper.get_var(name='a', t=0))


class TestOutputMapper(unittest.TestCase):
    def test_map_output(self):
        # Input
        study = Study(['a', 'be']) \
            .add_on_node('a', Consumption(type='load', quantity=[10], cost=10)) \
            .add_on_node('a', Production(type='nuclear', quantity=[12], cost=10)) \
            .add_border(src='a', dest='be', quantity=[10], cost=2)

        s = MockSolver()
        mapper = OutputMapper(solver=s, study=study)

        out_cons = [LPConsumption(type='load', cost=10, quantity=10, variable=MockNumVar(0, 5.0, 'lol load on a'))]
        out_prod = [LPProduction(type='nuclear', cost=10, quantity=12, variable=MockNumVar(0, 12.0, 'prod nuclear on a'))]

        out_bord = [LPBorder(src='a', dest='be', cost=2, quantity=10, variable=MockNumVar(0, 8.0, 'border on a to be'))]
        mapper.set_var(name='a', t=0, vars=LPNode(consumptions=out_cons, productions=out_prod, borders=out_bord))

        # Expected
        node = OutputNode(consumptions=[OutputConsumption(type='load', quantity=[5], cost=10)],
                          productions=[OutputProduction(type='nuclear', quantity=[12], cost=10)],
                          borders=[OutputBorder(dest='be', quantity=[8], cost=2)])
        expected = Result(nodes={'a': node, 'be': OutputNode(consumptions=[], productions=[], borders=[])})

        assert_study(self, expected=expected, result=mapper.get_result())
