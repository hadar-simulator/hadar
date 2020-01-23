from unittest.mock import MagicMock, call

import pandas as pd
import numpy as np
import unittest

from hadar.solver.actor.actor import Exchange
from hadar.solver.actor.handler.handler import State
from hadar.solver.actor.handler.handler import *
from hadar.solver.actor.ledger import *


class TestCancelExchangeUselessHandler(unittest.TestCase):

    def test_execute(self):
        # Create mock
        tell_mock = MagicMock()

        # Input
        exchange0 = Exchange(id=0, production_type='solar', quantity=1, path_node=['fr'])
        exchange1 = Exchange(id=1, production_type='solar', quantity=1, path_node=['fr'])
        exchange2 = Exchange(id=2, production_type='solar', quantity=1, path_node=['fr'])
        exchange3 = Exchange(id=3, production_type='solar', quantity=1, path_node=['be'])
        exchange4 = Exchange(id=4, production_type='solar', quantity=1, path_node=['be'])

        productions = LedgerProduction(uuid_generate=lambda: None)
        productions.add_exchanges(cost=10, used=True, ex=[exchange0, exchange1])
        productions.add_exchanges(cost=10, used=False, ex=[exchange2, exchange3, exchange4])

        exchanges = LedgerExchange()
        exchanges.add_all([exchange0, exchange1, exchange2, exchange3, exchange4], 'export')

        state = State(name='fr',
                      consumptions=LedgerConsumption(),
                      productions=productions,
                      borders=LedgerBorder(), rac=0, cost=0)
        state.exchanges = exchanges

        # Expected
        exp_productions = LedgerProduction(uuid_generate=lambda: None)
        exp_productions.add_exchanges(cost=10, used=True,
                                     ex=[Exchange(id=0, production_type='solar', quantity=1, path_node=['fr'])])
        exp_productions.add_exchanges(cost=10, used=True,
                                     ex=[Exchange(id=1, production_type='solar', quantity=1, path_node=['fr'])])

        exp_exchanges = LedgerExchange()
        exp_exchanges.add_all([Exchange(id=0, production_type='solar', quantity=1, path_node=['fr']),
                               Exchange(id=1, production_type='solar', quantity=1, path_node=['fr'])], 'export')

        exp_state = State(name='fr',
                          consumptions=LedgerConsumption(),
                          productions=exp_productions,
                          borders=LedgerBorder(), rac=0, cost=0)
        exp_state.exchanges = exp_exchanges

        handler = CancelUselessImportationHandler(next=ReturnHandler(), params=HandlerParameter(tell=tell_mock))
        new_state, _ = handler.execute(state)

        # Test
        self.assertEqual(exp_state, new_state)

        tell_mock.assert_has_calls(
            [call(to='fr', mes=ConsumerCanceledExchange(exchanges=[exchange2], path_node=['fr'])),
             call(to='be', mes=ConsumerCanceledExchange(exchanges=[exchange3, exchange4], path_node=['be']))])


class TestProposeFreeProduction(unittest.TestCase):

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
        exchanges.add(Exchange(id=1, quantity=5, production_type='nuclear', path_node=['be']), type='export')

        state = State(name='fr', consumptions=LedgerConsumption(), borders=borders, productions=productions, cost=0,
                      rac=0)
        state.exchanges = exchanges

        handler = ProposeFreeProductionHandler(next=ReturnHandler(), params=params)
        new_sate, _ = handler.execute(state)

        self.assertEqual(state, new_sate)
        tell_mock.assert_called_with(to='be', mes=Proposal(production_type='nuclear', cost=30, quantity=5, path_node=['fr']))

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
        exchanges.add(Exchange(id=1, quantity=5, production_type='nuclear', path_node=['be']), 'export')

        state = State(name='fr', consumptions=LedgerConsumption(), borders=borders, productions=productions, cost=0,
                      rac=0)
        state.exchanges = exchanges

        handler = ProposeFreeProductionHandler(next=ReturnHandler(), params=params)
        new_sate, _ = handler.execute(state)

        self.assertEqual(state, new_sate)
        tell_mock.assert_called_with(to='be', mes=Proposal(production_type='nuclear', cost=30, quantity=2, path_node=['fr']))


class TestForwardMessageHandler(unittest.TestCase):
    def test_execute(self):
        # Create mock
        tell_mock = MagicMock()
        params = HandlerParameter(tell=tell_mock)

        # Input
        borders = LedgerBorder()
        borders.add(dest='be', cost=2, quantity=10)
        borders.add(dest='de', cost=4, quantity=5)
        borders.add(dest='uk', cost=10, quantity=10)

        state = State(name='fr', consumptions=None, borders=borders, productions=None, rac=0, cost=0)
        state.exchanges = LedgerExchange()
        state.exchanges.add(ex=Exchange(quantity=5, id=0, production_type='solar', path_node=['uk', 'fr']), type='transfer')

        prop = Proposal(production_type='solar', cost=10, quantity=7, path_node=['it'])

        # Expected
        be_prop = Proposal(production_type='solar', cost=12, quantity=7, path_node=['fr', 'it'])
        de_prop = Proposal(production_type='solar', cost=14, quantity=5, path_node=['fr', 'it'])
        uk_prop = Proposal(production_type='solar', cost=20, quantity=5, path_node=['fr', 'it'])

        # Test
        handler = ForwardMessageHandler(next=ReturnHandler(), params=params)
        res_state, res_message = handler.execute(state=state, message=prop)

        tell_mock.assert_has_calls(
            [call(to='be', mes=be_prop),
             call(to='de', mes=de_prop),
             call(to='uk', mes=uk_prop)])


class TestSaveExchangeHandler(unittest.TestCase):
    def test_trim_path(self):
        self.assertEqual(['be'], SaveExchangeHandler.trim_path('fr', ['it', 'fr', 'be']))
        self.assertEqual(['be'], SaveExchangeHandler.trim_path('fr', ['fr', 'be']))
        self.assertEqual(['be'], SaveExchangeHandler.trim_path('fr', ['be']))
        self.assertEqual([], SaveExchangeHandler.trim_path('be', ['be']))


class TestCancelExportationHandler(unittest.TestCase):
    def test_execute(self):
        # Create mock
        params = HandlerParameter()

        # Input
        ex_cancel = Exchange(id=10, production_type='solar', quantity=10, path_node=['fr', 'be', 'de'])
        ex_keep = Exchange(id=5, production_type='solar', quantity=10, path_node=['fr', 'be', 'de'])

        state = State(name='fr', consumptions=LedgerConsumption(),
                      borders=LedgerBorder(), productions=LedgerProduction(), rac=0, cost=0)
        state.exchanges = LedgerExchange()
        state.exchanges.add_all([ex_cancel, ex_keep], 'export')

        message = ConsumerCanceledExchange(path_node=['fr', 'be'], exchanges=[ex_cancel])

        # Expected
        state_exp = State(name='fr', consumptions=LedgerConsumption(),
                          borders=LedgerBorder(), productions=LedgerProduction(), rac=0, cost=0)
        state_exp.exchanges = LedgerExchange()
        state_exp.exchanges.add(ex_keep, 'export')

        # Test
        handler = CancelExportationHandler(next=ReturnHandler(), params=params)
        res, _ = handler.execute(state=state, message=message)

        self.assertEqual(state_exp, res)


class TestBackwardMessageHandler(unittest.TestCase):
    def test_execute_tell(self):
        # Create mock
        tell_mock = MagicMock()
        params = HandlerParameter(tell=tell_mock)

        # Input
        message = ProposalOffer(production_type='solar', cost=10, quantity=10,
                                path_node=['fr', 'de'], return_path_node=['de', 'fr'])
        state = State(name='fr', consumptions=None, borders=None, productions=None, rac=0, cost=0)

        # Expected
        expected = ProposalOffer(production_type='solar', cost=10, quantity=10,
                                path_node=['de'], return_path_node=['de', 'fr'])

        # Test
        handler = BackwardMessageHandler(after_backward=ReturnHandler(), on_resume=ReturnHandler(), params=params, type='tell')
        res, _ = handler.execute(state=state, message=message)

        self.assertEqual(state, res)
        tell_mock.assert_called_with(to='de', mes=expected)

    def test_execute_ask(self):
        # Expected
        return_expected = [Exchange(quantity=10, id=1, production_type='solar', path_node=['be', 'fr', 'de'])]
        ask_expected = ProposalOffer(production_type='solar', cost=10, quantity=10,
                                path_node=['de'], return_path_node=['de', 'fr'])

        # Create mock
        ask_mock = MagicMock(return_value=return_expected)
        params = HandlerParameter(ask=ask_mock)

        # Input
        message = ProposalOffer(production_type='solar', cost=10, quantity=10,
                                path_node=['fr', 'de'], return_path_node=['de', 'fr'])
        state = State(name='fr', consumptions=None, borders=None, productions=None, rac=0, cost=0)

        # Test
        handler = BackwardMessageHandler(after_backward=ReturnHandler(), on_resume=ReturnHandler(), params=params, type='ask')
        res_state, res_message = handler.execute(state=state, message=message)

        self.assertEqual(state, res_state)
        self.assertEqual(return_expected, res_message)
        ask_mock.assert_called_with(to='de', mes=ask_expected)

    def test_execute_resume(self):
        # Create mock
        params = HandlerParameter()

        # Input
        message = ProposalOffer(production_type='solar', cost=10, quantity=10,
                                path_node=['de'], return_path_node=['fr', 'be'])
        state = State(name='de', consumptions=None, borders=None, productions=None, rac=0, cost=0)

        # Test
        handler = BackwardMessageHandler(after_backward=ReturnHandler(), on_resume=ReturnHandler(), params=params, type='ask')
        res_state, res_message = handler.execute(state=state, message=message)

        self.assertEqual(state, res_state)
        self.assertEqual(message, res_message)


class TestAcceptAvailableExchangeHandler(unittest.TestCase):
    def test_execute(self):
        # Input
        uuid_mock = MockUUID()
        params = HandlerParameter(uuid_generate=uuid_mock.generate)

        productions = LedgerProduction(uuid_generate=uuid_mock.generate)
        productions.add_production(cost=10, quantity=10, type='nuclear', used=False)

        state = State(name='fr', consumptions=None, productions=productions, borders=None, rac=0, cost=0)
        state.exchanges = LedgerExchange()
        state.exchanges.add_all([Exchange(quantity=1, id=1, production_type='nuclear', path_node=['be']),
                                 Exchange(quantity=1, id=2, production_type='nuclear', path_node=['be']),
                                 Exchange(quantity=1, id=3, production_type='nuclear', path_node=['be']),
                                 Exchange(quantity=1, id=4, production_type='nuclear', path_node=['be']),
                                 Exchange(quantity=1, id=5, production_type='nuclear', path_node=['be'])], 'export')

        offer = ProposalOffer(production_type='nuclear', cost=12, quantity=10, path_node=['fr'], return_path_node=['de'])

        # Expected
        response_exp = [Exchange(quantity=1, id=6, production_type='nuclear', path_node=['de']),
                        Exchange(quantity=1, id=7, production_type='nuclear', path_node=['de']),
                        Exchange(quantity=1, id=8, production_type='nuclear', path_node=['de']),
                        Exchange(quantity=1, id=9, production_type='nuclear', path_node=['de']),
                        Exchange(quantity=1, id=10, production_type='nuclear', path_node=['de'])]

        # Test
        handler = AcceptExchangeHandler(next=ReturnHandler(), params=params)
        state_res, response_res = handler.execute(state, offer)

        self.assertEqual(state, state_res)
        self.assertEqual(response_exp, response_res)


class TestCompareNewProduction(unittest.TestCase):
    def test_execute_on_expensive(self):
        # Input
        params = HandlerParameter()

        consumptions = LedgerConsumption()
        consumptions.add(type='load', cost=10**3, quantity=2)

        uuid_mock = MockUUID()
        productions = LedgerProduction(uuid_generate=uuid_mock.generate)
        productions.add_production(type='solar', cost=10, quantity=2, used=True)

        state = State(name='fr', consumptions=consumptions, borders=None, productions=productions, rac=0, cost=20)
        proposal = Proposal(production_type='nuclear', cost=12, quantity=10, path_node=['it'])

        # Create mock

        for_prod_useless = ReturnHandler()
        for_prod_useless.execute = MagicMock(return_value=(state, proposal))

        for_prod_useful = ReturnHandler()
        for_prod_useful.execute = MagicMock()

        # Test
        handler = CompareNewProduction(for_prod_useless=for_prod_useless, for_prod_useful=for_prod_useful, params=params)
        state_res, mes_res = handler.execute(state, proposal)

        self.assertEqual(state, state_res)
        self.assertEqual(proposal, mes_res)

    def test_execute_on_cheaper(self):
        # Input
        params = HandlerParameter()

        consumptions = LedgerConsumption()
        consumptions.add(type='load', cost=10**3, quantity=2)

        uuid_mock = MockUUID()
        productions = LedgerProduction(uuid_generate=uuid_mock.generate)
        productions.add_production(type='solar', cost=15, quantity=2, used=True)

        state = State(name='fr', consumptions=consumptions, borders=None, productions=productions, rac=0, cost=30)
        proposal = Proposal(production_type='nuclear', cost=12, quantity=4, path_node=['it'])

        # Create mock
        for_prod_useless = ReturnHandler()
        for_prod_useless.execute = MagicMock()

        for_prod_useful = ReturnHandler()
        for_prod_useful.execute = MagicMock(return_value=(state, proposal))

        # Expected
        expected_prop = Proposal(production_type='nuclear', cost=12, quantity=2, path_node=['it'])

        # Test
        handler = CompareNewProduction(for_prod_useless=for_prod_useless, for_prod_useful=for_prod_useful,
                                       params=params)
        state_res, mes_res = handler.execute(state, proposal)

        self.assertEqual(state, state_res)
        self.assertEqual(proposal, mes_res)
        for_prod_useless.execute.assert_called_with(state=state, message=expected_prop)


class TestMakeOfferHandler(unittest.TestCase):
    def test_execute(self):
        # Mock
        exs_return = [Exchange(quantity=1, id=0, production_type='solar', path_node=['it'])]
        ask_mock = MagicMock(return_value=exs_return)
        params = HandlerParameter(ask=ask_mock)

        # Input
        state = State(name='fr', consumptions=None, borders=None, productions=LedgerProduction(), rac=0, cost=0)
        proposal = Proposal(production_type='solar', cost=10, quantity=1, path_node=['it'])

        # Expected
        offer_expected = ProposalOffer(production_type='solar', cost=10, quantity=1, path_node=['it'], return_path_node=['fr'])

        exs_expected = [Exchange(quantity=1, id=0, production_type='solar', path_node=['it'])]

        state_expected = deepcopy(state)
        state_expected.productions.add_exchanges(cost=10, ex=exs_expected)

        # Test
        handler = MakerOfferHandler(next=ReturnHandler(), params=params)
        res_state, res_mes = handler.execute(deepcopy(state), deepcopy(proposal))

        self.assertEqual(state_expected, res_state)
        self.assertEqual(exs_expected, res_mes)
        ask_mock.assert_called_with(to='it', mes=offer_expected)


class TestCheckOfferBorderCapacityHandler(unittest.TestCase):
    def test_execute_available(self):
        # Input
        params = HandlerParameter()

        borders = LedgerBorder()
        borders.add(dest='be', cost=10, quantity=10)

        state = State(name='fr', consumptions=None, borders=borders, productions=None, rac=0, cost=0)
        state.exchanges = LedgerExchange()
        state.exchanges.add(Exchange(id=0, production_type='solar', quantity=5, path_node=['be']), type='export')

        offer = ProposalOffer(production_type='solar', cost=10, quantity=10, path_node=['fr', 'it'], return_path_node=['fr', 'be'])

        # Expected
        offer_exp = ProposalOffer(production_type='solar', cost=10, quantity=5, path_node=['fr', 'it'], return_path_node=['fr', 'be'])

        handler = CheckOfferBorderCapacityHandler(next=ReturnHandler(), params=params)
        res_state, res_message = handler.execute(state=state, message=offer)

        self.assertEqual(state, res_state)
        self.assertEqual(offer_exp, res_message)


class TestAdequacyHandler(unittest.TestCase):
    def test_execute(self):
        # Input
        params = HandlerParameter()

        consumptions = LedgerConsumption()
        consumptions.add(type='load', cost=100, quantity=10)

        uuid_mock = MockUUID()
        productions = LedgerProduction(uuid_generate=uuid_mock.generate)
        productions.add_production(type='solar', cost=10, quantity=4)
        productions.add_production(type='nuclear', cost=20, quantity=4)

        state = State(name='fr', consumptions=consumptions, borders=None, productions=productions, rac=0, cost=0)

        # Expected
        consumptions = LedgerConsumption()
        consumptions.ledger = pd.DataFrame({'cost': [100], 'quantity': [10]}, index=['load'])

        productions = LedgerProduction()
        productions.ledger = pd.DataFrame({'cost': [10] * 4 + [20] * 4,
                                           'quantity': [4] * 8,
                                           'type': ['solar'] * 4 + ['nuclear'] * 4,
                                           'path_node': [None] * 8},
                                          index=[1, 2, 3, 4, 5, 6, 7, 8])
        expected = State(name='fr', consumptions=consumptions, borders=None, productions=productions, rac=-2, cost=320)

        handler = AdequacyHandler(next=ReturnHandler(), params=params)
        new_state, _ = handler.execute(state=state, message=None)


class MockUUID:
    def __init__(self):
        self.inc = 0

    def generate(self):
        self.inc += 1
        return self.inc
