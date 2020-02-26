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
            .add_on_node('a', Consumption(type='load', quantity=[10, 1], cost=10)) \
            .add_on_node('a', Production(type='nuclear', quantity=[12, 2], cost=10)) \
            .add_border(src='a', dest='be', quantity=[10, 3], cost=2)

        s = MockSolver()

        mapper = InputMapper(solver=s, study=study)

        # Expected
        out_cons_0 = [LPConsumption(type='load', cost=10, quantity=10, variable=MockNumVar(0, 10, 'lol load on a at 0'))]
        out_prod_0 = [LPProduction(type='nuclear', cost=10, quantity=12, variable=MockNumVar(0, 12.0, 'prod nuclear on a at 0'))]

        out_bord_0 = [LPBorder(src='a', dest='be', cost=2, quantity=10, variable=MockNumVar(0, 10.0, 'border on a to be at 0'))]
        out_node_0 = LPNode(consumptions=out_cons_0, productions=out_prod_0, borders=out_bord_0)

        self.assertEqual(out_node_0, mapper.get_var(name='a', t=0))

        out_cons_1 = [LPConsumption(type='load', cost=10, quantity=1, variable=MockNumVar(0, 1, 'lol load on a at 1'))]
        out_prod_1 = [LPProduction(type='nuclear', cost=10, quantity=2, variable=MockNumVar(0, 2.0, 'prod nuclear on a at 1'))]

        out_bord_1 = [LPBorder(src='a', dest='be', cost=2, quantity=3, variable=MockNumVar(0, 3.0, 'border on a to be at 1'))]
        out_node_1 = LPNode(consumptions=out_cons_1, productions=out_prod_1, borders=out_bord_1)

        self.assertEqual(out_node_1, mapper.get_var(name='a', t=1))


class TestOutputMapper(unittest.TestCase):
    def test_map_output(self):
        # Input
        study = Study(['a', 'be']) \
            .add_on_node('a', Consumption(type='load', quantity=[10, 20], cost=10)) \
            .add_on_node('a', Production(type='nuclear', quantity=[12, 2], cost=10)) \
            .add_border(src='a', dest='be', quantity=[10, 3], cost=2)

        s = MockSolver()
        mapper = OutputMapper(solver=s, study=study)

        out_cons_0 = [LPConsumption(type='load', cost=10, quantity=10, variable=MockNumVar(0, 5.0, 'lol load on a'))]
        out_prod_0 = [LPProduction(type='nuclear', cost=10, quantity=12, variable=MockNumVar(0, 12.0, 'prod nuclear on a'))]

        out_bord_0 = [LPBorder(src='a', dest='be', cost=2, quantity=10, variable=MockNumVar(0, 8.0, 'border on a to be'))]
        mapper.set_var(name='a', t=0, vars=LPNode(consumptions=out_cons_0 , productions=out_prod_0, borders=out_bord_0))

        out_cons_1 = [LPConsumption(type='load', cost=10, quantity=20, variable=MockNumVar(0, 5.0, 'lol load on a'))]
        out_prod_1 = [LPProduction(type='nuclear', cost=10, quantity=2, variable=MockNumVar(0, 112.0, 'prod nuclear on a'))]

        out_bord_1 = [LPBorder(src='a', dest='be', cost=2, quantity=10, variable=MockNumVar(0, 18.0, 'border on a to be'))]
        mapper.set_var(name='a', t=1, vars=LPNode(consumptions=out_cons_1 , productions=out_prod_1, borders=out_bord_1))

        # Expected
        node = OutputNode(consumptions=[OutputConsumption(type='load', quantity=[5, 15], cost=10)],
                          productions=[OutputProduction(type='nuclear', quantity=[12, 112], cost=10)],
                          borders=[OutputBorder(dest='be', quantity=[8, 18], cost=2)])
        expected = Result(nodes={'a': node, 'be': OutputNode(consumptions=[], productions=[], borders=[])})


        assert_study(self, expected=expected, result=mapper.get_result())
