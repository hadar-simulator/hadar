import unittest
from unittest.mock import MagicMock, call

from hadar.solver.actor.handler.handler import State
from hadar.solver.actor.domain.message import *
from hadar.solver.actor.handler.entry import CanceledCustomerExchangeHandler, ProposalOfferHandler, ProposalHandler
from hadar.solver.actor.ledger import *
from hadar.solver.actor.handler.handler import *


class TestCanceledCustomerExchangeHandler(unittest.TestCase):
    def test_execute_producer(self):
        # Create mock
        tell_mock = MagicMock()
        params = HandlerParameter(tell=tell_mock)

        uuid_mock = MockUUID()

        # Input
        ex_cancel = Exchange(id=10, production_type='nuclear', quantity=10, path_node=['fr', 'be', 'de'])
        ex_keep = Exchange(id=5, production_type='nuclear', quantity=10, path_node=['fr', 'be', 'de'])

        borders = LedgerBorder()
        borders.add(dest='be', cost=2, quantity=10)

        productions = LedgerProduction(uuid_generate=uuid_mock.generate)
        productions.add_production(cost=10, quantity=20, type='nuclear', used=False)

        state = State(name='fr', consumptions=LedgerConsumption(),
                      borders=borders, productions=productions, rac=0, cost=0)
        state.exchanges = LedgerExchange()
        state.exchanges.add_all([ex_cancel, ex_keep], 'export')

        message = ConsumerCanceledExchange(path_node=['fr'], exchanges=[ex_cancel])

        # Expected
        state_exp = State(name='fr', consumptions=LedgerConsumption(),
                          borders=borders, productions=productions, rac=0, cost=0)
        state_exp.exchanges = LedgerExchange()
        state_exp.exchanges.add(ex_keep, 'export')

        # Test
        handler = CanceledCustomerExchangeHandler(params=params)
        res, _ = handler.execute(state=state, message=message)

        self.assertEqual(state_exp, res)
        tell_mock.assert_called_with(to='be',
                                     mes=Proposal(production_type='nuclear', cost=12, quantity=10, path_node=['fr']))


class TestProposalOfferHandler(unittest.TestCase):
    def test_execute_produce(self):
        # Create mock
        ask_mock = MagicMock()
        uuid_mock = MockUUID()
        params = HandlerParameter(ask=ask_mock, uuid_generate=uuid_mock.generate)

        # Input
        productions = LedgerProduction(uuid_generate=uuid_mock.generate)
        productions.add_production(cost=10, quantity=10, type='solar')

        borders = LedgerBorder()
        borders.add(dest='be', cost=10, quantity=8)

        state = State(name='fr', consumptions=None, borders=borders, productions=productions, rac=0, cost=0)
        state.exchanges = LedgerExchange()
        state.exchanges.add_all([Exchange(id=1, production_type='solar', quantity=1, path_node=['be']),
                                 Exchange(id=2, production_type='solar', quantity=1, path_node=['be']),
                                 Exchange(id=3, production_type='solar', quantity=1, path_node=['be']),
                                 Exchange(id=4, production_type='solar', quantity=1, path_node=['be']),
                                 Exchange(id=5, production_type='solar', quantity=1, path_node=['be'])], 'export')

        offer = ProposalOffer(production_type='solar', cost=10, quantity=5, path_node=['fr'],
                              return_path_node=['fr', 'be'])

        # Expected
        message_exp = [Exchange(id=6, production_type='solar', quantity=1, path_node=['fr', 'be']),
                       Exchange(id=7, production_type='solar', quantity=1, path_node=['fr', 'be']),
                       Exchange(id=8, production_type='solar', quantity=1, path_node=['fr', 'be'])]
        exchanges_exp = [Exchange(id=6, production_type='solar', quantity=1, path_node=['be']),
                         Exchange(id=7, production_type='solar', quantity=1, path_node=['be']),
                         Exchange(id=8, production_type='solar', quantity=1, path_node=['be'])]
        state_exp = deepcopy(state)
        state_exp.exchanges.add_all(exchanges_exp, type='export')

        # Test
        handler = ProposalOfferHandler(params=params)
        state_res, message_res = handler.execute(state=state, message=offer)

        self.assertEqual(state_exp, state_res)
        self.assertEqual(message_exp, message_res)

    def test_execute_backward(self):
        # Create mock
        message_mock = [Exchange(id=2, production_type='solar', quantity=1, path_node=['de', 'fr', 'be']),
                        Exchange(id=3, production_type='solar', quantity=1, path_node=['de', 'fr', 'be']),
                        Exchange(id=4, production_type='solar', quantity=1, path_node=['de', 'fr', 'be'])]
        ask_mock = MagicMock(return_value=message_mock)
        uuid_mock = MockUUID()
        params = HandlerParameter(ask=ask_mock, uuid_generate=uuid_mock.generate)

        # Input
        productions = LedgerProduction(uuid_generate=uuid_mock.generate)
        productions.add_production(cost=10, quantity=10, type='solar')

        borders = LedgerBorder()
        borders.add(dest='be', cost=10, quantity=8)

        state = State(name='fr', consumptions=None, borders=borders, productions=productions, rac=0, cost=0)
        state.exchanges = LedgerExchange()
        state.exchanges.add(Exchange(id=0, production_type='solar', quantity=5, path_node=['be']), type='transfer')

        offer = ProposalOffer(production_type='solar', cost=10, quantity=5, path_node=['fr', 'de'],
                              return_path_node=['de', 'fr', 'be'])

        # Expected
        exchanges_exp = [Exchange(id=2, production_type='solar', quantity=1, path_node=['be']),
                         Exchange(id=3, production_type='solar', quantity=1, path_node=['be']),
                         Exchange(id=4, production_type='solar', quantity=1, path_node=['be'])]
        state_exp = deepcopy(state)
        state_exp.exchanges.add_all(exchanges_exp, type='transfer')

        # Test
        handler = ProposalOfferHandler(params=params)
        state_res, message_res = handler.execute(state=state, message=offer)

        self.assertEqual(state_exp, state_res)
        self.assertEqual(message_mock, message_res)


class TestProposalHandler(unittest.TestCase):
    def test_execute(self):
        # Mock
        expected_exs = [Exchange(id=100, quantity=1, production_type='solar', path_node=['it']),
                        Exchange(id=101, quantity=1, production_type='solar', path_node=['it']),
                        Exchange(id=102, quantity=1, production_type='solar', path_node=['it']),
                        Exchange(id=103, quantity=1, production_type='solar', path_node=['it']),
                        Exchange(id=104, quantity=1, production_type='solar', path_node=['it'])]
        ask_mock = MagicMock(return_value=expected_exs)
        tell_mock = MagicMock()
        params = HandlerParameter(ask=ask_mock, tell=tell_mock)

        uuid_mock = MockUUID()

        # Input
        consumptions = LedgerConsumption()
        consumptions.add(type='load', quantity=10, cost=10 ** 6)

        productions = LedgerProduction(uuid_generate=uuid_mock.generate)
        productions.add_production(type='solar', cost=5, quantity=5, used=True)
        productions.add_production(type='nuclear', cost=10, quantity=5, used=True)

        borders = LedgerBorder()
        borders.add(dest='be', cost=2, quantity=10)

        state = State(name='fr', consumptions=consumptions, borders=borders, productions=productions, rac=0, cost=75)
        proposal = Proposal(production_type='wind', cost=7, quantity=10, path_node=['it'])

        # Expected
        proposal_forward = Proposal(production_type='wind', cost=9, quantity=5, path_node=['fr', 'it'])
        proposal_nuclear = Proposal(production_type='nuclear', cost=12, quantity=5, path_node=['fr'])
        offer_expected = ProposalOffer(production_type='wind', cost=7, quantity=5, path_node=['it'],
                                       return_path_node=['fr'])

        state_expected = deepcopy(state)
        state_expected.cost = 60
        state_expected.exchanges.add_all(expected_exs, type='import')
        state_expected.productions.ledger = \
            pd.DataFrame({'cost': [5] * 5 + [7] * 5 + [10] * 5,
                          'quantity': [1] * 15,
                          'type': ['solar'] * 5 + ['import'] * 5 + ['nuclear'] * 5,
                          'used': [True] * 10 + [False] * 5,
                          'path_node': [None, None, None, None, None,
                                        ['it'], ['it'], ['it'], ['it'], ['it'],
                                        None, None, None, None, None]},
                         index=[1, 2, 3, 4, 5, 100, 101, 102, 103, 104, 6, 7, 8, 9, 10])

        # Test
        handler = ProposalHandler(params=params)
        state_res, _ = handler.execute(deepcopy(state), deepcopy(proposal))
        self.assertEqual(state_expected, state_res)

        ask_mock.assert_called_with(to='it', mes=offer_expected)
        tell_mock.assert_has_calls(
            [call(to='be', mes=proposal_forward),
             call(to='be', mes=proposal_nuclear)])


class MockUUID:
    def __init__(self):
        self.inc = 0

    def generate(self):
        self.inc += 1
        return self.inc
