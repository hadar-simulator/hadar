import unittest
import pandas as pd

from solver.actor.domain.message import Exchange
from solver.actor.ledger import LedgerExchange, LedgerProduction, LedgerConsumption, LedgerBorder


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

        ledger.delete(ex[1])
        self.assertEqual(20, ledger.sum_production(production_id=1), "Wrong ledger behaviour")
        self.assertEqual(20, ledger.sum_border(name='fr'), 'Wrong ledger behaviour')


class TestLedgerProduction(unittest.TestCase):

    def test(self):

        mock = MockUUID()
        ledger = LedgerProduction(uuid_generate=mock.generate)

        # Add production
        ledger.add_production(cost=10, quantity=15, type='nuclear')
        ledger.add_production(cost=10, quantity=20, type='solar')
        ex = Exchange(id=1234, production_id=3, quantity=10, path_node=['fr'])
        ledger.add_exchange(cost=10, ex=ex)

        # Inspect ledger
        expectedA = pd.DataFrame({'cost': [10, 10],
                                  'quantity': [15, 20],
                                  'type': ['nuclear', 'solar'],
                                  'used': [False, False],
                                  'exchange': [None, None]},
                                 index=[1, 2])
        pd.testing.assert_frame_equal(expectedA, ledger.filter_productions())

        expectedB = pd.DataFrame({'cost': [10],
                                  'quantity': [10],
                                  'type': ['import'],
                                  'used': [False],
                                  'exchange': [ex]},
                                 index=[1234])
        pd.testing.assert_frame_equal(expectedB, ledger.filter_exchanges())


        # Delete production
        ledger.delete(id=2)

        # Inspect ledger
        expectedC = pd.DataFrame({'cost': [10],
                                  'quantity': [15],
                                  'type': ['nuclear'],
                                  'used': [False],
                                  'exchange': [None]},
                                 index=[1])
        pd.testing.assert_frame_equal(expectedC, ledger.filter_productions())
        pd.testing.assert_series_equal(expectedC.iloc[0], ledger.find_production(1))

        pd.testing.assert_frame_equal(expectedB, ledger.filter_exchanges())


class TestLedgerConsumption(unittest.TestCase):
    def test(self):
        ledger = LedgerConsumption()

        # Add
        ledger.add(type='load', cost=20, quantity=100)
        ledger.add(type='stockage', cost=20, quantity=200)

        # Inspect
        expected = pd.DataFrame({'cost': [20, 20], 'quantity': [100, 200]}, index=['load', 'stockage'])
        pd.testing.assert_frame_equal(expected, ledger.ledger)

        # Delete
        ledger.delete(type='load')
        expected = pd.DataFrame({'cost': [20], 'quantity': [200]}, index=['stockage'])
        pd.testing.assert_frame_equal(expected, ledger.ledger)


class TestLedgerBorder(unittest.TestCase):
    def test(self):
        ledger = LedgerBorder()

        # Add
        ledger.add(dest='fr', cost=20, quantity=100)
        ledger.add(dest='be', cost=20, quantity=200)

        # Inspect
        expected = pd.DataFrame({'cost': [20, 20], 'quantity': [100, 200]}, index=['fr', 'be'])
        pd.testing.assert_frame_equal(expected, ledger.ledger)

        # Delete
        ledger.delete(dest='fr')
        expected = pd.DataFrame({'cost': [20], 'quantity': [200]}, index=['be'])
        pd.testing.assert_frame_equal(expected, ledger.ledger)

class MockUUID:
    def __init__(self):
        self.inc = 0

    def generate(self):
        self.inc += 1
        return self.inc