import unittest
from unittest.mock import MagicMock

from domain import *
from node import Dispatcher, DispatcherRegistry, LedgerExchange


class TestNode(unittest.TestCase):

    def setUp(self) -> None:
        self.registry = DispatcherRegistry()

    def test_optimize_adequacy_rac_positive(self):
        # Input
        productions = [
            Production(type='nuclear', cost=10, quantity=200),
            Production(type='solar', cost=5, quantity=50),
            Production(type='oil', cost=20, quantity=200)
        ]

        consumptions = [
            Consumption(cost=10**6, quantity=300)
        ]

        # Output
        productions_free = [
            Production(type='oil', cost=20, quantity=150, id=42)
        ]

        productions_used = [
            Production(type='solar', cost=5, quantity=50, id=42),
            Production(type='nuclear', cost=10, quantity=200, id=42),
            Production(type='oil', cost=20, quantity=50, id=42)
        ]

        # Compare
        expected_state = NodeState(productions_used, productions_free, 3250, 150)

        dispatcher = Dispatcher(name='fr', consumptions=consumptions, productions=productions, uuid_generate=lambda: 42)
        state = dispatcher.optimize_adequacy(productions)
        self.assertEqual(expected_state, state)

    def test_optimize_adequacy_rac_zero(self):
        # Input
        productions = [
            Production(type='nuclear', cost=10, quantity=200),
            Production(type='solar', cost=5, quantity=50),
            Production(type='oil', cost=20, quantity=200)
        ]

        consumptions = [
            Consumption(cost=10**6, quantity=450)
        ]

        # Output
        productions_free = [
        ]

        productions_used = [
            Production(type='solar', cost=5, quantity=50, id=42),
            Production(type='nuclear', cost=10, quantity=200, id=42),
            Production(type='oil', cost=20, quantity=200, id=42)
        ]

        # Compare
        expected_state = NodeState(productions_used, productions_free, 6250, 0)

        dispatcher = Dispatcher(name='fr', consumptions=consumptions, productions=productions, uuid_generate=lambda: 42)
        state = dispatcher.optimize_adequacy(productions)
        self.assertEqual(expected_state, state)

    def test_optimize_adequacy_rac_negative(self):
        # Input
        productions = [
            Production(type='nuclear', cost=10, quantity=200),
            Production(type='solar', cost=5, quantity=50),
            Production(type='oil', cost=20, quantity=200)
        ]

        consumptions = [
            Consumption(cost=10**6, quantity=300),
            Consumption(cost=10**3, quantity=300)
        ]

        # Output
        productions_free = [
        ]

        productions_used = [
            Production(type='solar', cost=5, quantity=50, id=42),
            Production(type='nuclear', cost=10, quantity=200, id=42),
            Production(type='oil', cost=20, quantity=200, id=42)
        ]

        # Test
        expected_state = NodeState(productions_used, productions_free, 156250, -150)

        dispatcher = Dispatcher(name='fr', consumptions=consumptions, productions=productions, uuid_generate=lambda: 42)
        state = dispatcher.optimize_adequacy(productions)
        self.assertEqual(expected_state, state)


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
        self.assertEqual(proposal, mock_actor.mes, "Wrong proposal send")

    def test_receive_proposal_offer_give_all(self):
        # Input
        ledger = LedgerExchange()
        ledger.add(Exchange(quantity=50, id=1234, production_id=42))

        dispatcher = Dispatcher(name='fr',
                                uuid_generate=lambda: 42,
                                min_exchange=50,
                                ledger_exchange=ledger,
                                productions=[Production(cost=10, quantity=100)])

        prop = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['fr'])

        # Expected
        ex_expected = Exchange(id=42, production_id=42, quantity=50)

        # Test
        ex = dispatcher.receive_proposal_offer(proposal=prop)
        self.assertEqual([ex_expected], ex, 'Wrong exchange comme back')
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

        prop = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['fr'])

        # Expected
        ex_expected = Exchange(id=42, production_id=42, quantity=20)

        # Test
        ex = dispatcher.receive_proposal_offer(proposal=prop)
        self.assertEqual([ex_expected], ex, 'Wrong exchange comme back')
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

        prop = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['fr', 'be'])

        # Expected
        prop_forward = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['be'])


        # Test
        ex = dispatcher.receive_proposal_offer(proposal=prop)
        self.assertEqual([ex_expected], ex, 'Wrong exchange come back')
        registry.get.assert_called_with('be')

    def test_respond_proposal_ask_all_get_all(self):
        # Input
        mock_actor = MockActorRef([Exchange(quantity=50)])
        registry = DispatcherRegistry()
        registry.get = MagicMock(return_value=mock_actor)

        prop = Proposal(production_id=1234, cost=10, quantity=50, path_node=['be'])
        state = NodeState(productions_used=[Production(cost=10, quantity=50, id=1234)],
                          productions_free=[], cost=0, rac=0)

        # Output
        prop_asked = ProposalOffer(production_id=prop.production_id, cost=prop.cost, quantity=prop.quantity, path_node=prop.path_node)

        # Test
        dispatcher = Dispatcher(name='fr', registry=registry)
        dispatcher.responce_proposal(proposal=prop, new_state=state)

        registry.get.assert_called_with('be')
        self.assertEqual(prop_asked, mock_actor.mes, "Wrong proposal offer send")

    def test_respond_proposal_ask_partial_get_all(self):
        # Input
        mock_actor = MockActorRef([Exchange(quantity=50)])
        registry = DispatcherRegistry()
        registry.get = MagicMock(return_value=mock_actor)

        prop = Proposal(production_id=1234, cost=10, quantity=100, path_node=['be'])
        state = NodeState(productions_used=[Production(cost=10, quantity=50, id=1234)],
                          productions_free=[], cost=0, rac=0)

        # Output
        prop_asked = ProposalOffer(production_id=prop.production_id, cost=prop.cost, quantity=50, path_node=prop.path_node)

        # Test
        dispatcher = Dispatcher(name='fr', registry=registry)
        dispatcher.responce_proposal(proposal=prop, new_state=state)

        registry.get.assert_called_with('be')
        self.assertEqual(prop_asked, mock_actor.mes, "Wrong proposal offer send")

    def test_generate_exchange(self):
        #Input
        dispatcher = Dispatcher(name='fr', uuid_generate=lambda: 42, min_exchange=10)

        # Expected
        expected = [
            Exchange(id=42, production_id=45, quantity=10),
            Exchange(id=42, production_id=45, quantity=10)
        ]

        # Test complete
        res = dispatcher.generate_exchanges(production_id=45, quantity=20)
        self.assertEqual(expected, res, 'Wrong exchange generation')

        # Expected
        expected = [
            Exchange(id=42, production_id=45, quantity=10),
            Exchange(id=42, production_id=45, quantity=10),
            Exchange(id=42, production_id=45, quantity=5)
        ]

        # Test partial
        res = dispatcher.generate_exchanges(production_id=45, quantity=25)
        self.assertEqual(expected, res, 'Wrong exchange generation')

        # Test empty
        res = dispatcher.generate_exchanges(production_id=45, quantity=0)
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
        self.mes = None
        self.res = res

    def tell(self, mes):
        self.mes = mes

    def ask(self, mes):
        self.mes = mes
        return self.res

