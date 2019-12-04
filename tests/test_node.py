import unittest
from unittest.mock import MagicMock

from domain import *
from node import Dispatcher, DispatcherRegistry


class TestNode(unittest.TestCase):

    def setUp(self) -> None:
        self.resolver = DispatcherRegistry()

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
            Production(type='oil', cost=20, quantity=150)
        ]

        productions_used= [
            Production(type='solar', cost=5, quantity=50),
            Production(type='nuclear', cost=10, quantity=200),
            Production(type='oil', cost=20, quantity=50)
        ]

        # Compare
        expected_state = NodeState(productions_used, productions_free, 3250, 150)

        dispatcher = Dispatcher(name='fr', consumptions=consumptions, productions=productions, borders=None)
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
            Production(type='solar', cost=5, quantity=50),
            Production(type='nuclear', cost=10, quantity=200),
            Production(type='oil', cost=20, quantity=200)
        ]

        # Compare
        expected_state = NodeState(productions_used, productions_free, 6250, 0)

        dispatcher = Dispatcher(name='fr', consumptions=consumptions, productions=productions, borders=None)
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
            Production(type='solar', cost=5, quantity=50),
            Production(type='nuclear', cost=10, quantity=200),
            Production(type='oil', cost=20, quantity=200)
        ]

        # Test
        expected_state = NodeState(productions_used, productions_free, 156250, -150)

        dispatcher = Dispatcher(name='fr', consumptions=consumptions, productions=productions, borders=None)
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
                                uuid_generate=lambda: 42,
                                registry=registry,
                                borders=[Border(dest='be', capacity=0, cost=5), Border(dest='de', capacity=0, cost=5)])

        # Expected
        proposal = Proposal(id=42, cost=15, quantity=30, path_node=['fr', 'be'])

        # Test
        dispatcher.send_proposal(productions=[Production(cost=10, quantity=30)], path_node=['be'])
        registry.get.assert_called_with('de')
        self.assertEqual(proposal, mock_actor.mes, "Wrong proposal send")

    def test_respond_proposal_ask_all_get_all(self):
        # Input
        mock_actor = MockActorRef(ProposalFinal(quantity=50))
        registry = DispatcherRegistry()
        registry.get = MagicMock(return_value=mock_actor)

        prop = Proposal(id=1234, cost=10, quantity=50, path_node=['be'])
        state = NodeState(productions_used=[Production(cost=10, quantity=50, id=1234)],
                          productions_free=[], cost=0, rac=0)

        # Output
        prop_asked = ProposalOffer(id=prop.id, cost=prop.cost, quantity=prop.quantity, path_node=prop.path_node)

        # Test
        dispatcher = Dispatcher(name='fr', registry=registry)
        dispatcher.responce_proposal(proposal=prop, new_state=state)

        registry.get.assert_called_with('be')
        self.assertEqual(prop_asked, mock_actor.mes, "Wrong proposal offer send")



class MockActorRef:
    def __init__(self, res=None):
        self.mes = None
        self.res = res

    def tell(self, mes):
        self.mes = mes

    def ask(self, mes):
        self.mes = mes
        return self.res

