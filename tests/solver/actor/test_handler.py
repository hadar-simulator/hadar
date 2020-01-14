from unittest.mock import MagicMock, call

import pandas as pd
import numpy as np
import unittest

from hadar.solver.actor.actor import HandlerParameter, Exchange
from hadar.solver.actor.common import State
from hadar.solver.actor.handler import *
from hadar.solver.actor.ledger import *


class TestCancelExchangeUselessHandler(unittest.TestCase):

    def test_execute(self):
        # Create mock
        tell_mock = MagicMock()
        HandlerParameter(tell=tell_mock)

        uuid_mock = MockUUID()

        # Input
        exchange2 = Exchange(id=2, production_id=10, quantity=1, path_node=['fr'])
        exchange3 = Exchange(id=3, production_id=20, quantity=1, path_node=['be'])
        exchange4 = Exchange(id=4, production_id=20, quantity=1, path_node=['be'])

        productions = LedgerProduction(uuid_generate=uuid_mock.generate)
        productions.add_exchange(cost=10, used=True, ex=Exchange(id=0, production_id=10, quantity=1, path_node=['fr']))
        productions.add_exchange(cost=10, used=True, ex=Exchange(id=1, production_id=10, quantity=1, path_node=['fr']))
        productions.add_exchange(cost=10, used=False, ex=exchange2)  # Should be canceled
        productions.add_exchange(cost=10, used=False, ex=exchange3)  # Should be canceled
        productions.add_exchange(cost=10, used=False, ex=exchange4)  # Should be canceled 

        exchanges = LedgerExchange()
        exchanges.add_all(productions.filter_exchanges()['exchange'].values)

        state = State(consumptions=LedgerConsumption(),
                      productions=productions,
                      borders=LedgerBorder(), rac=0, cost=0)
        state.exchanges = exchanges

        # Expected
        exp_productions = LedgerProduction(uuid_generate=uuid_mock.generate)
        exp_productions.add_exchange(cost=10, used=True, ex=Exchange(id=0, production_id=10, quantity=1, path_node=['fr']))
        exp_productions.add_exchange(cost=10, used=True, ex=Exchange(id=1, production_id=10, quantity=1, path_node=['fr']))

        exp_exchanges = LedgerExchange()
        exp_exchanges.add_all(exp_productions.filter_exchanges()['exchange'].values)

        exp_state = State(consumptions=LedgerConsumption(),
                          productions=exp_productions,
                          borders=LedgerBorder(), rac=0, cost=0)
        exp_state.exchanges = exp_exchanges

        handler = CancelExchangeUselessHandler(next=ReturnHandler())
        new_state = handler.execute(state)

        # Test
        self.assertEqual(exp_state, new_state)

        tell_mock.assert_has_calls([call(to='fr', mes=ConsumerCanceledExchange(exchanges=[exchange2], path_node=['fr'])),
                                    call(to='be', mes=ConsumerCanceledExchange(exchanges=[exchange3, exchange4], path_node=['be']))])


class MockUUID:
    def __init__(self):
        self.inc = 0

    def generate(self):
        self.inc += 1
        return self.inc
