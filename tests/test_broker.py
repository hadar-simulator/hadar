import unittest
from unittest.mock import MagicMock, call

from dispatcher.domain import *
from dispatcher.broker import *


class BrokerTest(unittest.TestCase):

    def test_send_proposal(self):
        # Input
        tell = MagicMock()

        broker = Broker(name='fr',
                        tell=tell, ask=None,
                        borders=[Border(dest='be', capacity=0, cost=5), Border(dest='de', capacity=0, cost=5)])

        # Expected
        proposal = Proposal(production_id=42, cost=15, quantity=30, path_node=['fr', 'be'])

        # Test
        broker.send_proposal(productions=[Production(id=42, cost=10, quantity=30)], path_node=['be'])
        tell.assert_called_with(to='de', mes=proposal)

    def test_receive_proposal_offer_give_all(self):
        # Input
        ledger = LedgerExchange()
        ledger.add(Exchange(quantity=50, id=1234, production_id=42, path_node=['be']))

        broker = Broker(name='fr',
                        uuid_generate=lambda: 42,
                        ask=None, tell=None,
                        min_exchange=50,
                        ledger_exchange=ledger,
                        productions=[Production(cost=10, quantity=100)],
                        borders=[Border(dest='be', capacity=100)])

        prop = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['fr'], return_path_node=['be'])

        # Expected
        ex_expected = Exchange(id=42, production_id=42, quantity=50, path_node=['be'])

        # Test
        ex = broker.receive_proposal_offer(proposal=prop)
        self.assertEqual([ex_expected], ex, 'Wrong exchange come back')
        self.assertEqual(100, ledger.sum_production(42), 'Ledger not updated')

    def test_receive_proposal_offer_capped_by_border(self):
        # Input
        ledger = LedgerExchange()
        ledger.add(Exchange(quantity=80, id=1234, production_id=42, path_node=['be']))
        ledger.add(Exchange(quantity=20, id=4321, production_id=24, path_node=['be']))

        broker = Broker(name='fr',
                        uuid_generate=lambda: 42,
                        tell=None, ask=None,
                        min_exchange=20,
                        ledger_exchange=ledger,
                        productions=[Production(cost=10, quantity=100)],
                        borders=[Border(dest='be', capacity=120)])

        prop = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['fr'], return_path_node=['be'])

        # Expected
        ex_expected = Exchange(id=42, production_id=42, quantity=20, path_node=['be'])

        # Test
        ex = broker.receive_proposal_offer(proposal=prop)
        self.assertEqual([ex_expected], ex, 'Wrong exchange come back')
        self.assertEqual(100, ledger.sum_production(42), 'Ledger not updated')

    def test_receive_proposal_offer_capped_by_production(self):
        # Input
        ledger = LedgerExchange()
        ledger.add(Exchange(quantity=80, id=1234, production_id=42, path_node=['be']))

        broker = Broker(name='fr',
                        uuid_generate=lambda: 42,
                        tell=None, ask=None,
                        min_exchange=20,
                        ledger_exchange=ledger,
                        productions=[Production(cost=10, quantity=100)],
                        borders=[Border(dest='be', capacity=200)])

        prop = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['fr'], return_path_node=['be'])

        # Expected
        ex_expected = Exchange(id=42, production_id=42, quantity=20, path_node=['be'])

        # Test
        ex = broker.receive_proposal_offer(proposal=prop)
        self.assertEqual([ex_expected], ex, 'Wrong exchange come back')
        self.assertEqual(100, ledger.sum_production(42), 'Ledger not updated')

    def test_receive_proposal_offer_forward(self):
        # Input
        ledger = LedgerExchange()

        ex_expected = Exchange(id=1, production_id=42, quantity=50, path_node=['it'])
        ask = MagicMock(return_value=[ex_expected])
        broker = Broker(name='fr',
                        uuid_generate=lambda: 1,
                        ask=ask, tell=None,
                        ledger_exchange=ledger,
                        borders=[Border(dest='it', capacity=50)])

        prop = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['fr', 'be'],
                             return_path_node=['fr', 'it'])

        # Expected
        prop_forward = ProposalOffer(production_id=42, cost=10, quantity=50, path_node=['be'],
                                     return_path_node=['fr', 'it'])
        # Test
        ex = broker.receive_proposal_offer(proposal=prop)
        self.assertEqual([ex_expected], ex, 'Wrong exchange come back')
        ask.assert_called_with(to='be', mes=prop_forward)

        self.assertEqual({'it': {42: {1: ex_expected}}}, ledger.ledger, 'Wrong ledger state')

    def test_make_offer_ask_all_get_all(self):
        # Input
        ask = MagicMock(return_value=[Exchange(quantity=50)])
        broker = Broker(name='fr', ask=ask, tell=None,
                        consumptions=[Consumption(cost=10 ** 6, quantity=50)])
        broker.send_cancel_exchange = MagicMock()

        prop = Proposal(production_id=1234, cost=10, quantity=50, path_node=['be'])
        state = NodeState(productions_used=[Production(cost=10, quantity=50, id=1234)],
                          productions_free=[], cost=0, rac=0)

        # Output
        prop_asked = ProposalOffer(production_id=prop.production_id, cost=prop.cost, quantity=prop.quantity,
                                   path_node=prop.path_node, return_path_node=['fr'])

        # Test
        broker.make_offer(proposal=prop, new_state=state)

        ask.assert_called_with(to='be', mes=prop_asked)
        broker.send_cancel_exchange.assert_called_with([])

    def test_make_offer_ask_partial_get_all(self):
        # Input
        ask = MagicMock(return_value=[Exchange(quantity=50)])

        broker = Broker(name='fr', ask=ask, tell=None,
                        consumptions=[Consumption(cost=10 ** 6, quantity=50)])
        broker.send_remain_proposal = MagicMock()
        broker.send_cancel_exchange = MagicMock()

        prop = Proposal(production_id=1234, cost=10, quantity=100, path_node=['be'])
        state = NodeState(productions_used=[Production(cost=10, quantity=50, id=1234)],
                          productions_free=[], cost=0, rac=0)

        # Output
        prop_asked = ProposalOffer(production_id=prop.production_id, cost=prop.cost, quantity=50,
                                   path_node=prop.path_node, return_path_node=['fr'])

        # Test
        broker.make_offer(proposal=prop, new_state=state)

        ask.assert_called_with(to='be', mes=prop_asked)
        broker.send_remain_proposal.assert_called_with(proposal=prop, asked_quantity=50, given_quantity=50)
        broker.send_cancel_exchange.assert_called_with([])

    def test_receive_cancel_exchange_forward(self):
        # Input
        tell = MagicMock()
        broker = Broker(name='fr', tell=tell, ask=None)

        exchange = Exchange(quantity=10, id=0, production_id=42, path_node=['fr', 'it'])
        cancel = ConsumerCanceledExchange(exchanges=[exchange], path_node=['fr', 'it'])

        # Expected
        expected = ConsumerCanceledExchange(exchanges=[exchange], path_node=['it'])

        # Test
        broker.receive_cancel_exchange(cancel)
        tell.assert_called_with(to='it', mes=expected)

    def test_receive_cancel_exchange_cancel(self):
        # Input
        ledger = LedgerExchange()
        ledger.add(Exchange(quantity=10, id=1, production_id=42, path_node=['be']))
        ledger.add(Exchange(quantity=10, id=2, production_id=42, path_node=['be']))
        ledger.add(Exchange(quantity=10, id=3, production_id=42, path_node=['be']))

        tell = MagicMock()
        broker = Broker(name='fr',
                        tell=tell, ask=None,
                        ledger_exchange=ledger,
                        uuid_generate=lambda: 42,
                        productions=[Production(cost=10, quantity=40)],
                        borders=[Border(dest='be', capacity=100, cost=2)])

        ex1 = Exchange(quantity=10, id=1, production_id=42, path_node=['be'])
        ex2 = Exchange(quantity=10, id=2, production_id=42, path_node=['be'])
        cancel = ConsumerCanceledExchange(exchanges=[ex1, ex2], path_node=['fr'])

        # Expected
        proposal = Proposal(production_id=42, cost=10 + 2, quantity=20, path_node=['fr'])

        # Test
        broker.receive_cancel_exchange(cancel)
        self.assertEqual(10, ledger.sum_production(42))
        tell.assert_called_with(to='be', mes=proposal)

    def test_send_remain_proposal(self):
        # Input
        broker = Broker(name='fr', tell=None, ask=None)
        broker.send_proposal = MagicMock()

        prop = Proposal(production_id=1, cost=10, quantity=200, path_node=['be'])

        # Expected
        expected = Production(id=1, cost=10, quantity=100)

        # Test
        broker.send_remain_proposal(proposal=prop, asked_quantity=100, given_quantity=100)
        broker.send_proposal.assert_called_with([expected], ['be'])

    def test_send_cancel_exchange(self):
        # Input
        tell = MagicMock()

        broker = Broker(name='fr', tell=tell, ask=None)

        exchanges = [
            Exchange(quantity=10, id=0, production_id=24, path_node=['be']),
            Exchange(quantity=10, id=1, production_id=24, path_node=['be']),
            Exchange(quantity=10, id=2, production_id=42, path_node=['de']),
            Exchange(quantity=10, id=3, production_id=24, path_node=['be']),
        ]

        # Expected
        cancel24 = ConsumerCanceledExchange(exchanges=[exchanges[0], exchanges[1], exchanges[3]], path_node=['be'])
        cancel42 = ConsumerCanceledExchange(exchanges=[exchanges[2]], path_node=['de'])

        broker.send_cancel_exchange(exchanges)

        tell.assert_has_calls([call(to='be', mes=cancel24), call(to='de', mes=cancel42)])

    def test_generate_exchange(self):
        # Input
        broker = Broker(name='fr',
                        tell=lambda: None,
                        ask=lambda: None,
                        uuid_generate=lambda: 42, min_exchange=10)

        # Expected
        expected = [
            Exchange(id=42, production_id=45, quantity=10, path_node=['fr']),
            Exchange(id=42, production_id=45, quantity=10, path_node=['fr'])
        ]

        # Test complete
        res = broker.generate_exchanges(production_id=45, quantity=20, path_node=['fr'])
        self.assertEqual(expected, res, 'Wrong exchange generation')

        # Expected
        expected = [
            Exchange(id=42, production_id=45, quantity=10, path_node=['fr']),
            Exchange(id=42, production_id=45, quantity=10, path_node=['fr']),
            Exchange(id=42, production_id=45, quantity=5, path_node=['fr'])
        ]

        # Test partial
        res = broker.generate_exchanges(production_id=45, quantity=25, path_node=['fr'])
        self.assertEqual(expected, res, 'Wrong exchange generation')

        # Test empty
        res = broker.generate_exchanges(production_id=45, quantity=0, path_node=['fr'])
        self.assertEqual([], res, 'Wrong empty exchange generation')

    def test_find_production(self):
        productions = [
            Production(type='nuclear', cost=10, quantity=200, id=98),
            Production(type='solar', cost=5, quantity=50, id=23),
            Production(type='oil', cost=20, quantity=200, id=45)
        ]

        self.assertEqual(productions[1], Broker.find_production(prods=productions, id=23),
                         "Can't find productions by id")

    def test_compute_total(self):
        ledger = LedgerExchange()
        ledger.add(Exchange(quantity=10, id=1, production_id=42, path_node=['be']))
        broker = Broker(name='fr',
                        ask=None, tell=None,
                        uuid_generate=lambda: 42,
                        ledger_exchange=ledger,
                        consumptions=[Consumption(quantity=10, cost=10**6)],
                        productions=[Production(quantity=30, cost=10)],
                        borders=[Border(dest='be', capacity=20, cost=10)])

        consumptions, productions, border = broker.compute_total()
        self.assertEqual([Consumption(quantity=10, cost=10**6)], consumptions, 'Wrong compute consumptions')
        self.assertEqual([Production(quantity=20, cost=10, id=42)], productions, 'Wrong compute productions')
        self.assertEqual([Border(dest='be', capacity=10, cost=10)], border)


class TestLedgerExchange(unittest.TestCase):

    def test(self):
        ex = [
            Exchange(id=1234, production_id=1, quantity=10, path_node=['fr']),
            Exchange(id=9876, production_id=1, quantity=10, path_node=['fr']),
            Exchange(id=5432, production_id=1, quantity=10, path_node=['be']),
            Exchange(id=4566, production_id=2, quantity=10, path_node=['fr'])
        ]
        ledger = LedgerExchange()
        ledger.add_all(ex)

        self.assertEqual(30, ledger.sum_production(production_id=1), "Wrong ledger behaviour")
        self.assertEqual(30, ledger.sum_border(name='fr'), 'Wrong ledger behaviour')

        ledger.delete(Exchange(id=9876, production_id=1, quantity=10, path_node=['fr']))
        self.assertEqual(20, ledger.sum_production(production_id=1), "Wrong ledger behaviour")
        self.assertEqual(20, ledger.sum_border(name='fr'), 'Wrong ledger behaviour')
