import unittest

from hadar.solver.actor.actor import Dispatcher, State
from hadar.solver.actor.ledger import *
from hadar.solver.output import *


class TestDispatcher(unittest.TestCase):

    def test_build_state(self):
        # Input

        # Expected
        cons = LedgerConsumption()
        cons.add(type='load', cost=20, quantity=10)

        prod = LedgerProduction(uuid_generate=lambda: 42)
        prod.add_production(type='solar', cost=23, quantity=10)

        border = LedgerBorder()
        border.add(dest='be', cost=2, quantity=10)

        exp_state = State(name='fr', consumptions=cons, productions=prod, borders=border, rac=0, cost=0)

        # Test
        res_state = Dispatcher.build_state(name='fr',
                                      uuid_generate=lambda: 42,
                                      consumptions=[Consumption(type='load', quantity=np.array([10]), cost=20)],
                                      productions=[Production(type='solar', quantity=np.array([10]), cost=23)],
                                      borders=[Border(dest='be', quantity=np.array([10]), cost=2)], t=0)

        self.assertEqual(exp_state, res_state)

    def test_compute_total(self):
        mock_id = MockUUID()

        # Input
        ledger_cons = LedgerConsumption()
        ledger_cons.add(type='load', cost=2, quantity=7)

        ledger_prod = LedgerProduction()
        ledger_prod.add_production(type='solar', cost=3, quantity=5, used=True)
        ledger_prod.add_production(type='nuclear', cost=3, quantity=2, used=True)
        ledger_prod.add_production(type='nuclear', cost=3, quantity=3, used=False)

        ledger_border = LedgerBorder()
        ledger_border.add(dest='be', cost=2, quantity=7)

        state = State(name='fr', consumptions=ledger_cons, borders=ledger_border,
                                 productions=ledger_prod, cost=0, rac=0)
        state.exchanges = LedgerExchange()
        state.exchanges.add(Exchange(id=0, production_type='nuclear', quantity=3, path_node=['be']),
                                       type='export')

        out_node = OutputNode(consumptions=[], borders=[], productions=[])
        out_node.consumptions = [OutputConsumption(type='load', quantity=np.array([0, 0]), cost=2)]
        out_node.productions = [OutputProduction(type='solar', cost=3, quantity=np.array([0, 0])),
                                OutputProduction(type='nuclear', cost=3, quantity=np.array([0, 0]))]
        out_node.borders = [OutputBorder(dest='be', cost=2, quantity=np.array([0, 0]))]

        # Expected
        expected = OutputNode(consumptions=[], borders=[], productions=[])
        expected.consumptions = [OutputConsumption(type='load', quantity=np.array([7, 0]), cost=2)]
        expected.productions = [OutputProduction(type='solar', cost=3, quantity=np.array([5, 0])),
                                OutputProduction(type='nuclear', cost=3, quantity=np.array([5, 0]))]
        expected.borders = [OutputBorder(dest='be', cost=2, quantity=np.array([3, 0]))]

        # Start test
        res = Dispatcher.compute_total(out_node=out_node, state=state, t=0)

        self.assertEqual(expected, res)


class MockUUID:
    def __init__(self):
        self.inc = 0

    def generate(self):
        self.inc += 1
        return self.inc
