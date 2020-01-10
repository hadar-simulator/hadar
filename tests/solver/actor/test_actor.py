import numpy as np
import unittest

from hadar.solver.actor.ledger import *
from hadar.solver.actor.domain.input import *
from solver.actor.actor import Dispatcher
from solver.actor.common import State


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

        state = State(consumptions=cons, productions=prod, borders=border, rac=0, cost=0)

        self.assertEqual(state, dispatcher.build_state(0))
        # TODO error undefined
