from unittest.mock import MagicMock, call

import pandas as pd
import numpy as np
import unittest

from hadar.solver.actor.actor import Exchange
from hadar.solver.actor.common import State
from hadar.solver.actor.handler.handler import *
from hadar.solver.actor.ledger import *


class TestCancelExchangeUselessHandler(unittest.TestCase):

    def test_execute(self):
        # Create mock
        tell_mock = MagicMock()

        # Input
        exchange2 = Exchange(id=2, production_id=10, quantity=1, path_node=['fr'])
        exchange3 = Exchange(id=3, production_id=20, quantity=1, path_node=['be'])
        exchange4 = Exchange(id=4, production_id=20, quantity=1, path_node=['be'])

        productions = LedgerProduction(uuid_generate=lambda: None)
        productions.add_exchange(cost=10, used=True, ex=Exchange(id=0, production_id=10, quantity=1, path_node=['fr']))
        productions.add_exchange(cost=10, used=True, ex=Exchange(id=1, production_id=10, quantity=1, path_node=['fr']))
        productions.add_exchange(cost=10, used=False, ex=exchange2)  # Should be canceled
        productions.add_exchange(cost=10, used=False, ex=exchange3)  # Should be canceled
        productions.add_exchange(cost=10, used=False, ex=exchange4)  # Should be canceled

        exchanges = LedgerExchange()
        exchanges.add_all(productions.filter_exchanges()['exchange'].values)

        state = State(name='fr',
                      consumptions=LedgerConsumption(),
                      productions=productions,
                      borders=LedgerBorder(), rac=0, cost=0)
        state.exchanges = exchanges

        # Expected
        exp_productions = LedgerProduction(uuid_generate=lambda: None)
        exp_productions.add_exchange(cost=10, used=True,
                                     ex=Exchange(id=0, production_id=10, quantity=1, path_node=['fr']))
        exp_productions.add_exchange(cost=10, used=True,
                                     ex=Exchange(id=1, production_id=10, quantity=1, path_node=['fr']))

        exp_exchanges = LedgerExchange()
        exp_exchanges.add_all(exp_productions.filter_exchanges()['exchange'].values)

        exp_state = State(name='fr',
                          consumptions=LedgerConsumption(),
                          productions=exp_productions,
                          borders=LedgerBorder(), rac=0, cost=0)
        exp_state.exchanges = exp_exchanges

        handler = CancelUselessImportationHandler(next=ReturnHandler(), params=HandlerParameter(tell=tell_mock))
        new_state = handler.execute(state)

        # Test
        self.assertEqual(exp_state, new_state)

        tell_mock.assert_has_calls(
            [call(to='fr', mes=ConsumerCanceledExchange(exchanges=[exchange2], path_node=['fr'])),
             call(to='be', mes=ConsumerCanceledExchange(exchanges=[exchange3, exchange4], path_node=['be']))])


class ProposeFreeProduction(unittest.TestCase):

    def test_execute_enough_border(self):
        # Create mock
        tell_mock = MagicMock()
        params = HandlerParameter(tell=tell_mock)

        mock_uuid = MockUUID()

        # Input
        productions = LedgerProduction(uuid_generate=mock_uuid.generate)
        productions.add_production(type='solar', cost=10, quantity=10, used=True)
        productions.add_production(type='nuclear', cost=20, quantity=10, used=True)
        productions.add_production(type='nuclear', cost=20, quantity=10, used=False)

        borders = LedgerBorder()
        borders.add(dest='be', cost=10, quantity=10)  # Has enough quantity

        exchanges = LedgerExchange()
        exchanges.add(Exchange(id=1, quantity=5, production_id=3, path_node=['be']))

        state = State(name='fr', consumptions=LedgerConsumption(), borders=borders, productions=productions, cost=0,
                      rac=0)
        state.exchanges = exchanges

        handler = ProposeFreeProductionHandler(next=ReturnHandler(), params=params)
        new_sate = handler.execute(state)

        self.assertEqual(state, new_sate)
        tell_mock.assert_called_with(to='be', mes=Proposal(production_id=3, cost=30, quantity=5, path_node=['fr']))

    def test_execute_saturation_border(self):
        # Create mock
        tell_mock = MagicMock()
        params = HandlerParameter(tell=tell_mock)

        mock_uuid = MockUUID()

        # Input
        productions = LedgerProduction(uuid_generate=mock_uuid.generate)
        productions.add_production(type='solar', cost=10, quantity=10, used=True)
        productions.add_production(type='nuclear', cost=20, quantity=10, used=True)
        productions.add_production(type='nuclear', cost=20, quantity=10, used=False)

        borders = LedgerBorder()
        borders.add(dest='be', cost=10, quantity=7)  # Not enough quantity

        exchanges = LedgerExchange()
        exchanges.add(Exchange(id=1, quantity=5, production_id=3, path_node=['be']))

        state = State(name='fr', consumptions=LedgerConsumption(), borders=borders, productions=productions, cost=0,
                      rac=0)
        state.exchanges = exchanges

        handler = ProposeFreeProductionHandler(next=ReturnHandler(), params=params)
        new_sate = handler.execute(state)

        self.assertEqual(state, new_sate)
        tell_mock.assert_called_with(to='be', mes=Proposal(production_id=3, cost=30, quantity=2, path_node=['fr']))


class TestCancelExportationHandler(unittest.TestCase):
    def test_execute_forward(self):
        # Create mock
        tell_mock = MagicMock()
        params = HandlerParameter(tell=tell_mock)

        # Input
        ex_cancel = Exchange(id=10, production_id=1, quantity=10, path_node=['fr', 'be', 'de'])
        ex_keep = Exchange(id=5, production_id=1, quantity=10, path_node=['fr', 'be', 'de'])

        state = State(name='fr', consumptions=LedgerConsumption(),
                      borders=LedgerBorder(), productions=LedgerProduction(), rac=0, cost=0)
        state.exchanges = LedgerExchange()
        state.exchanges.add_all([ex_cancel, ex_keep])

        message = ConsumerCanceledExchange(path_node=['fr', 'be'], exchanges=[ex_cancel])

        # Expected
        state_exp = State(name='fr', consumptions=LedgerConsumption(),
                          borders=LedgerBorder(), productions=LedgerProduction(), rac=0, cost=0)
        state_exp.exchanges = LedgerExchange()
        state_exp.exchanges.add(ex_keep)

        # Test
        handler = CancelExportationHandler(on_producer=ReturnHandler(), on_forward=ReturnHandler(), params=params)
        res = handler.execute(state=state, message=message)

        self.assertEqual(state_exp, res)
        tell_mock.assert_called_with(to='be', mes=ConsumerCanceledExchange(path_node=['be'], exchanges=[ex_cancel]))

    def test_execute_producer(self):
        # Create mock
        tell_mock = MagicMock()
        params = HandlerParameter(tell=tell_mock)

        # Input
        ex_cancel = Exchange(id=10, production_id=1, quantity=10, path_node=['fr', 'be', 'de'])
        ex_keep = Exchange(id=5, production_id=1, quantity=10, path_node=['fr', 'be', 'de'])

        state = State(name='fr', consumptions=LedgerConsumption(),
                      borders=LedgerBorder(), productions=LedgerProduction(), rac=0, cost=0)
        state.exchanges = LedgerExchange()
        state.exchanges.add_all([ex_cancel, ex_keep])

        message = ConsumerCanceledExchange(path_node=['fr'], exchanges=[ex_cancel])

        # Expected
        state_exp = State(name='fr', consumptions=LedgerConsumption(),
                          borders=LedgerBorder(), productions=LedgerProduction(), rac=0, cost=0)
        state_exp.exchanges = LedgerExchange()
        state_exp.exchanges.add(ex_keep)

        # Test
        handler = CancelExportationHandler(on_producer=ReturnHandler(), on_forward=ReturnHandler(), params=params)
        res = handler.execute(state=state, message=message)

        self.assertEqual(state_exp, res)
        self.assertEqual(0, len(tell_mock.call_list()))


class MockUUID:
    def __init__(self):
        self.inc = 0

    def generate(self):
        self.inc += 1
        return self.inc
