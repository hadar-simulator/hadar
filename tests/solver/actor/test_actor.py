import numpy as np
import unittest

from hadar.solver.actor.ledger import *
from hadar.solver.actor.domain.input import *
from hadar.solver.actor.actor import Dispatcher, State
from hadar.solver.actor.domain.output import *


class TestDispatcher(unittest.TestCase):

    def test_build_state(self):
        # Input
        dispatcher = Dispatcher(name='fr',
                                uuid_generate=lambda: 42,
                                consumptions=[InputConsumption(type='load', quantity=np.array([10]), cost=20)],
                                productions=[InputProduction(type='solar', quantity=np.array([10]), cost=23)],
                                borders=[InputBorder(dest='be', quantity=np.array([10]), cost=2)])

        # Expected
        cons = LedgerConsumption()
        cons.add(type='load', cost=20, quantity=10)

        prod = LedgerProduction(uuid_generate=lambda: 42)
        prod.add_production(type='solar', cost=23, quantity=10)

        border = LedgerBorder()
        border.add(dest='be', cost=2, quantity=10)

        state = State(name='fr', consumptions=cons, productions=prod, borders=border, rac=0, cost=0)

        self.assertEqual(state, dispatcher.build_state(0))


    def test_compute_total(self):

        mock_id = MockUUID()
        # Input
        dispatcher = Dispatcher(name='fr',
                                uuid_generate=mock_id.generate,
                                consumptions=[
                                    InputConsumption(cost=2, type='load', quantity=np.array([7, 7]))],
                                productions=[
                                    InputProduction(cost=3, type='solar', quantity=np.array([5, 6])),
                                    InputProduction(cost=3, type='nuclear', quantity=np.array([5, 6]))],
                                borders=[
                                    InputBorder(dest='be', cost=2, quantity=np.array([7, 8]))
                                ])

        ledger_cons = LedgerConsumption()
        ledger_cons.add(type='load', cost=2, quantity=7)

        ledger_prod = LedgerProduction()
        ledger_prod.add_production(type='solar', cost=3, quantity=5, used=True)
        ledger_prod.add_production(type='nuclear', cost=3, quantity=2, used=True)
        ledger_prod.add_production(type='nuclear', cost=3, quantity=3, used=False)

        ledger_border = LedgerBorder()
        ledger_border.add(dest='be', cost=2, quantity=7)

        dispatcher.state = State(name='fr', consumptions=ledger_cons, borders=ledger_border,
                                 productions=ledger_prod, cost=0, rac=0)
        dispatcher.state.exchanges = LedgerExchange()
        dispatcher.state.exchanges.add(Exchange(id=0, production_type='nuclear', quantity=3, path_node=['be']), type='export')

        # Expected
        expected = OutputNode()
        expected.consumptions = [OutputConsumption(type='load', quantity=np.array([7, 0]), cost=2)]
        expected.productions = [OutputProduction(type='solar', cost=3, quantity=np.array([5, 0])),
                                OutputProduction(type='nuclear', cost=3, quantity=np.array([5, 0]))]
        expected.borders = [OutputBorder(dest='be', cost=2, quantity=np.array([3, 0]))]

        # Start test
        dispatcher.compute_total(0)

        self.assertEqual(expected, dispatcher.out_node)



class MockUUID:
    def __init__(self):
        self.inc = 0

    def generate(self):
        self.inc += 1
        return self.inc