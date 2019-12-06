import unittest
from unittest.mock import MagicMock, call

from dispatcher.domain import *
from dispatcher.node import Dispatcher, LedgerExchange
from dispatcher.manager import DispatcherRegistry

class TestNode(unittest.TestCase):

    def setUp(self) -> None:
        self.registry = DispatcherRegistry()


    def test_find_production(self):
        productions = [
            Production(type='nuclear', cost=10, quantity=200, id=98),
            Production(type='solar', cost=5, quantity=50, id=23),
            Production(type='oil', cost=20, quantity=200, id=45)
        ]

        self.assertEqual(productions[1], Dispatcher.find_production(prods=productions, id=23), "Can't find productions by id")


    def test_send_proposal(self):
        # Input
        mock_actor = MockActorRef()
        registry = DispatcherRegistry()
        registry.get = MagicMock(return_value=mock_actor)

        dispatcher = Dispatcher(name='fr',
                                registry=registry,
                                borders=[Border(dest='be', capacity=0, cost=5), Border(dest='de', capacity=0, cost=5)])

        # Expected
        proposal = Proposal(production_id=42, cost=15, quantity=30, path_node=['fr', 'be'])

        # Test
        dispatcher.send_proposal(productions=[Production(id=42, cost=10, quantity=30)], path_node=['be'])
        registry.get.assert_called_with('de')
        self.assertEqual(proposal, mock_actor.mes[0], "Wrong proposal send")

    def test_receive_proposal_offer_give_all(self):
        # Input
        ledger = LedgerExchange()
        ledger.add(Exchange(quantity=50, id=1234, production_id=42))

        dispatcher = Dispatcher(name='fr',
                                uuid_generate=lambda: 42,
                                min_exchange=50,
                                ledger_exchange=ledger,
                                productions=[Production(cost=10, quantity=100)])

        prop = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['fr'], return_path_node=['be'])

        # Expected
        ex_expected = Exchange(id=42, production_id=42, quantity=50, path_node=['be'])

        # Test
        ex = dispatcher.receive_proposal_offer(proposal=prop)
        self.assertEqual([ex_expected], ex, 'Wrong exchange come back')
        self.assertEqual(100, ledger.sum_production(42), 'Ledger not updated')

    def test_receive_proposal_offer_give_partial(self):
        # Input
        ledger = LedgerExchange()
        ledger.add(Exchange(quantity=80, id=1234, production_id=42))

        dispatcher = Dispatcher(name='fr',
                                uuid_generate=lambda: 42,
                                min_exchange=20,
                                ledger_exchange=ledger,
                                productions=[Production(cost=10, quantity=100)])

        prop = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['fr'], return_path_node=['be'])

        # Expected
        ex_expected = Exchange(id=42, production_id=42, quantity=20, path_node=['be'])

        # Test
        ex = dispatcher.receive_proposal_offer(proposal=prop)
        self.assertEqual([ex_expected], ex, 'Wrong exchange come back')
        self.assertEqual(100, ledger.sum_production(42), 'Ledger not updated')


    def test_receive_proposal_offer_forward(self):
        # Input
        ex_expected = Exchange(id=1, production_id=42, quantity=50)
        mock_actor = MockActorRef([ex_expected])
        registry = DispatcherRegistry()
        registry.get = MagicMock(return_value=mock_actor)
        dispatcher = Dispatcher(name='fr',
                                uuid_generate=lambda: 1,
                                registry=registry)

        prop = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['fr', 'be'], return_path_node=['fr', 'it'])

        # Expected
        prop_forward = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['be'], return_path_node=['fr', 'it'])


        # Test
        ex = dispatcher.receive_proposal_offer(proposal=prop)
        self.assertEqual([ex_expected], ex, 'Wrong exchange come back')
        registry.get.assert_called_with('be')
        self.assertEqual(prop_forward, mock_actor.mes[0], 'Wrong message forward')

    def test_make_offer_ask_all_get_all(self):
        # Input
        mock_actor = MockActorRef([Exchange(quantity=50)])
        registry = DispatcherRegistry()
        registry.get = MagicMock(return_value=mock_actor)

        prop = Proposal(production_id=1234, cost=10, quantity=50, path_node=['be'])
        state = NodeState(productions_used=[Production(cost=10, quantity=50, id=1234)],
                          productions_free=[], cost=0, rac=0)

        # Output
        prop_asked = ProposalOffer(production_id=prop.production_id, cost=prop.cost, quantity=prop.quantity, path_node=prop.path_node, return_path_node=['fr'])

        # Test
        dispatcher = Dispatcher(name='fr', registry=registry)
        dispatcher.make_offer(proposal=prop, new_state=state)

        registry.get.assert_called_with('be')
        self.assertEqual(prop_asked, mock_actor.mes[0], "Wrong proposal offer send")

    def test_make_offer_ask_partial_get_all(self):
        # Input
        mock_actor = MockActorRef([Exchange(quantity=50)])
        registry = DispatcherRegistry()
        registry.get = MagicMock(return_value=mock_actor)

        dispatcher = Dispatcher(name='fr', registry=registry)
        dispatcher.send_remain_proposal = MagicMock()

        prop = Proposal(production_id=1234, cost=10, quantity=100, path_node=['be'])
        state = NodeState(productions_used=[Production(cost=10, quantity=50, id=1234)],
                          productions_free=[], cost=0, rac=0)

        # Output
        prop_asked = ProposalOffer(production_id=prop.production_id, cost=prop.cost, quantity=50, path_node=prop.path_node, return_path_node=['fr'])

        # Test
        dispatcher.make_offer(proposal=prop, new_state=state)

        registry.get.assert_called_with('be')
        dispatcher.send_remain_proposal.assert_called_with(proposal=prop, asked_quantity=50, given_quantity=50)
        self.assertEqual(prop_asked, mock_actor.mes[0], "Wrong proposal offer send")

    def test_receive_cancel_exchange_forward(self):
        # Input
        mock_actor = MockActorRef()
        registry = DispatcherRegistry()
        registry.get = MagicMock(return_value=mock_actor)

        dispatcher = Dispatcher(name='fr', registry=registry)

        exchange = Exchange(quantity=10, id=0, production_id=42, path_node=['fr', 'it'])
        cancel = CanceledExchange(exchanges=[exchange], path_node=['fr', 'it'])

        # Expected
        expected = CanceledExchange(exchanges=[exchange], path_node=['it'])

        # Test
        dispatcher.receive_cancel_exchange(cancel)
        registry.get.assert_called_with('it')
        self.assertEqual(expected, mock_actor.mes[0], "Wrong cancel forwarded")

    def test_receive_cancel_exchange_cancel(self):
        # Input
        ledger = LedgerExchange()
        ledger.add(Exchange(quantity=10, id=1, production_id=42, path_node=['be']))
        ledger.add(Exchange(quantity=10, id=2, production_id=42, path_node=['be']))
        ledger.add(Exchange(quantity=10, id=3, production_id=42, path_node=['be']))

        mock_actor = MockActorRef()
        registry = DispatcherRegistry()
        registry.get = MagicMock(return_value=mock_actor)

        dispatcher = Dispatcher(name='fr', registry=registry, ledger_exchange=ledger,
                                uuid_generate=lambda: 42,
                                productions=[Production(cost=10, quantity=40)],
                                borders=[Border(dest='be', capacity=100, cost=2)])

        ex1 = Exchange(quantity=10, id=1, production_id=42, path_node=['fr', 'it'])
        ex2 = Exchange(quantity=10, id=2, production_id=42, path_node=['fr', 'it'])
        cancel = CanceledExchange(exchanges=[ex1, ex2], path_node=['fr'])

        # Expected
        proposal = Proposal(production_id=42, cost=10+2, quantity=20, path_node=['fr'])

        # Test
        dispatcher.receive_cancel_exchange(cancel)
        self.assertEqual(10, ledger.sum_production(42))
        registry.get.assert_called_with('be')
        self.assertEqual(proposal, mock_actor.mes[0], 'Wrong proposal')

    def test_send_remain_proposal(self):
        # Input
        dispatcher = Dispatcher(name='fr')
        dispatcher.send_proposal = MagicMock()

        prop = Proposal(production_id=1, cost=10, quantity=200, path_node=['be'])

        # Expected
        expected = Production(id=1, cost=10, quantity=100)


        # Test
        dispatcher.send_remain_proposal(proposal=prop, asked_quantity=100, given_quantity=100)
        dispatcher.send_proposal.assert_called_with([expected], ['be'])

    def test_send_cancel_exchange(self):
        # Input
        mock_actor = MockActorRef()
        registry = DispatcherRegistry()
        registry.get = MagicMock(return_value=mock_actor)

        dispatcher = Dispatcher(name='fr', registry=registry)

        exchanges = [
            Exchange(quantity=10, id=0, production_id=24, path_node=['be']),
            Exchange(quantity=10, id=1, production_id=24, path_node=['be']),
            Exchange(quantity=10, id=2, production_id=42, path_node=['de']),
            Exchange(quantity=10, id=3, production_id=24, path_node=['be']),
        ]

        # Expected
        cancel24 = CanceledExchange(exchanges=[exchanges[0], exchanges[1], exchanges[3]], path_node=['be'])
        cancel42 = CanceledExchange(exchanges=[exchanges[2]], path_node=['de'])

        dispatcher.send_cancel_exchange(exchanges)

        registry.get.assert_has_calls([call('be'), call('de')])
        self.assertEqual(cancel24, mock_actor.mes[0], 'Wrong cancel exchange send')
        self.assertEqual(cancel42, mock_actor.mes[1], 'Wrong cancel exchange send')


    def test_generate_exchange(self):
        #Input
        dispatcher = Dispatcher(name='fr', uuid_generate=lambda: 42, min_exchange=10)

        # Expected
        expected = [
            Exchange(id=42, production_id=45, quantity=10, path_node=['fr']),
            Exchange(id=42, production_id=45, quantity=10, path_node=['fr'])
        ]

        # Test complete
        res = dispatcher.generate_exchanges(production_id=45, quantity=20, path_node=['fr'])
        self.assertEqual(expected, res, 'Wrong exchange generation')

        # Expected
        expected = [
            Exchange(id=42, production_id=45, quantity=10, path_node=['fr']),
            Exchange(id=42, production_id=45, quantity=10, path_node=['fr']),
            Exchange(id=42, production_id=45, quantity=5, path_node=['fr'])
        ]

        # Test partial
        res = dispatcher.generate_exchanges(production_id=45, quantity=25, path_node=['fr'])
        self.assertEqual(expected, res, 'Wrong exchange generation')

        # Test empty
        res = dispatcher.generate_exchanges(production_id=45, quantity=0, path_node=['fr'])
        self.assertEqual([], res, 'Wrong empty exchange generation')


class TestLedgerExchange(unittest.TestCase):

    def test(self):
        ex = [
            Exchange(id=1234, production_id=1, quantity=10),
            Exchange(id=9876, production_id=1, quantity=10),
            Exchange(id=5432, production_id=1, quantity=10),
            Exchange(id=4566, production_id=2, quantity=10)
        ]
        ledger = LedgerExchange()
        ledger.add_all(ex)

        self.assertEqual(30, ledger.sum_production(production_id=1), "Wrong ledger behaviour")

        ledger.delete(Exchange(id=9876, production_id=1, quantity=10))
        self.assertEqual(20, ledger.sum_production(production_id=1), "Wrong ledger behaviour")


class MockActorRef:
    def __init__(self, res=None):
        self.mes = []
        self.res = res

    def tell(self, mes):
        self.mes.append(mes)

    def ask(self, mes):
        self.mes.append(mes)
        return self.res

