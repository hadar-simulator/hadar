import unittest
from unittest.mock import MagicMock

from solver.actor.common import State
from solver.actor.domain.message import *
from solver.actor.handler.entry import CanceledCustomerExchangeHandler
from solver.actor.ledger import *
from solver.actor.handler.handler import *


class TestCanceledCustomerExchangeHandler(unittest.TestCase):
    def test_execute_producer(self):
        # Create mock
        tell_mock = MagicMock()
        params = HandlerParameter(tell=tell_mock)

        uuid_mock = MockUUID()

        # Input
        ex_cancel = Exchange(id=10, production_id=1, quantity=10, path_node=['fr', 'be', 'de'])
        ex_keep = Exchange(id=5, production_id=1, quantity=10, path_node=['fr', 'be', 'de'])

        borders = LedgerBorder()
        borders.add(dest='be', cost=2, quantity=10)

        productions = LedgerProduction(uuid_generate=uuid_mock.generate)
        productions.add_production(cost=10, quantity=20, type='nuclear', used=False)

        state = State(name='fr', consumptions=LedgerConsumption(),
                      borders=borders, productions=productions, rac=0, cost=0)
        state.exchanges = LedgerExchange()
        state.exchanges.add_all([ex_cancel, ex_keep])

        message = ConsumerCanceledExchange(path_node=['fr'], exchanges=[ex_cancel])

        # Expected
        state_exp = State(name='fr', consumptions=LedgerConsumption(),
                          borders=borders, productions=productions, rac=0, cost=0)
        state_exp.exchanges = LedgerExchange()
        state_exp.exchanges.add(ex_keep)

        # Test
        handler = CanceledCustomerExchangeHandler(params=params)
        res, _ = handler.execute(state=state, message=message)

        self.assertEqual(state_exp, res)
        tell_mock.assert_called_with(to='be', mes=Proposal(production_id=1, cost=12, quantity=10, path_node=['fr']))


class MockUUID:
    def __init__(self):
        self.inc = 0

    def generate(self):
        self.inc += 1
        return self.inc