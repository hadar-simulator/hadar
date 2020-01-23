import unittest
import pandas as pd

from hadar.solver.actor.domain.message import Exchange
from hadar.solver.actor.ledger import LedgerExchange, LedgerProduction, LedgerConsumption, LedgerBorder


class TestLedgerExchange(unittest.TestCase):

    def test(self):
        ex = [
            Exchange(id=1234, production_type='solar', quantity=10, path_node=['fr']),
            Exchange(id=9876, production_type='solar', quantity=10, path_node=['fr']),
            Exchange(id=5432, production_type='solar', quantity=10, path_node=['be']),
            Exchange(id=4566, production_type='nuclear', quantity=10, path_node=['fr'])
        ]
        ledger = LedgerExchange()
        ledger.add_all(ex, 'export')

        self.assertEqual(30, ledger.sum_production(production_type='solar'), "Wrong ledger behaviour")
        self.assertEqual(30, ledger.sum_border(name='fr'), 'Wrong ledger behaviour')

        ledger.delete(ex[1])
        self.assertEqual(20, ledger.sum_production(production_type='solar'), "Wrong ledger behaviour")
        self.assertEqual(20, ledger.sum_border(name='fr'), 'Wrong ledger behaviour')

    def test_filter_production_available(self):
        # Input
        ex = [
            Exchange(id=1, production_type='solar', quantity=1, path_node=['be']),
            Exchange(id=2, production_type='nuclear', quantity=1, path_node=['fr'])
        ]
        ledger = LedgerExchange()
        ledger.add_all(ex, 'export')

        prod = pd.DataFrame({'type': ['nuclear', 'wind'],
                             'quantity': [1, 1],
                             'used': [False, False],
                             'cost': [10, 10]},
                            index=[2, 3])

        # Expected
        prod_exp = pd.DataFrame({'type': ['wind'],
                                 'quantity': [1],
                                 'used': [False],
                                 'cost': [10]},
                                index=[3])

        # Test
        pd.testing.assert_frame_equal(prod_exp, ledger.filter_production_available(productions=prod))


class TestLedgerProduction(unittest.TestCase):

    def test(self):
        mock = MockUUID()
        ledger = LedgerProduction(uuid_generate=mock.generate)

        # Add production
        ledger.add_production(cost=10, quantity=2, type='nuclear')
        ledger.add_production(cost=10, quantity=3, type='solar', used=True)
        ex = Exchange(id=1234, production_type='wind', quantity=1, path_node=['fr'])
        ledger.add_exchanges(cost=10, ex=[ex])

        # Inspect ledger
        expectedA = pd.DataFrame({'cost': [10, 10, 10, 10, 10, 10],
                                  'quantity': [1, 1, 1, 1, 1, 1],
                                  'type': ['nuclear', 'nuclear', 'solar', 'solar', 'solar', 'import'],
                                  'used': [False, False, True, True, True, False],
                                  'path_node': [None, None, None, None, None, ['fr']]},
                                 index=[1, 2, 3, 4, 5, 1234])
        pd.testing.assert_frame_equal(expectedA, ledger.ledger)

        # Delete production
        ledger.delete(id=2)

        # Inspect ledger
        expectedB = pd.DataFrame({'cost': [10, 10, 10, 10, 10],
                                  'quantity': [1, 1, 1, 1, 1],
                                  'type': ['nuclear', 'solar', 'solar', 'solar', 'import'],
                                  'used': [False, True, True, True, False],
                                  'path_node': [None, None, None, None, ['fr']]},
                                 index=[1, 3, 4, 5, 1234])
        pd.testing.assert_frame_equal(expectedB, ledger.ledger)

    def test_group_free_productions(self):
        mock = MockUUID()
        ledger = LedgerProduction(uuid_generate=mock.generate)

        # Add production
        ledger.add_production(cost=10, quantity=2, type='nuclear')
        ledger.add_production(cost=20, quantity=10, type='wind')
        ledger.add_production(cost=10, quantity=3, type='solar', used=True)

        # Expected
        expected = pd.DataFrame(data={'cost': [10, 20],
                                      'quantity': [2, 10]},
                                index=['nuclear', 'wind'])
        expected.index.name = 'type'

        # Test
        pd.testing.assert_frame_equal(expected, ledger.group_free_productions())

    def test_get_production_quantity(self):
        mock = MockUUID()
        ledger = LedgerProduction(uuid_generate=mock.generate)

        # Add production
        ledger.add_production(cost=10, quantity=15, type='nuclear')
        ledger.add_production(cost=10, quantity=15, type='nuclear')
        ledger.add_production(cost=10, quantity=15, type='nuclear', used=True)
        ledger.add_production(cost=10, quantity=20, type='solar', used=True)

        self.assertEqual(30, ledger.get_production_quantity(type='nuclear', used=False))
        self.assertEqual(15, ledger.get_production_quantity(type='nuclear', used=True))
        self.assertEqual(20, ledger.get_production_quantity(type='solar', used=True))

    def test_apply_adequacy(self):
        # Input
        uuid_mock = MockUUID()
        ledger = LedgerProduction(uuid_generate=uuid_mock.generate)
        ledger.add_production(cost=10, quantity=5, type='solar')
        ledger.add_production(cost=15, quantity=3, type='nuclear')
        ledger.add_production(cost=5, quantity=2, type='wind')

        # Expected
        expected = pd.DataFrame({'cost': [5] * 2 + [10] * 5 + [15] * 3,
                                 'quantity': [1] * 10,
                                 'type': ['wind'] * 2 + ['solar'] * 5 + ['nuclear'] * 3,
                                 'used': [True] * 7 + [False] * 3,
                                 'path_node': [None] * 10},
                                index=[9, 10, 1, 2, 3, 4, 5, 6, 7, 8])

        # Test
        cost, power = ledger.apply_adequacy(quantity=7)

        self.assertEqual(60, cost)
        self.assertEqual(7, power)
        pd.testing.assert_frame_equal(expected, ledger.ledger)

    def test_split_quantity(self):
        # Input
        prod = pd.DataFrame({'quantity': [8, 6, 4],
                             'cost': [10, 10, 10],
                             'type': ['solar', 'solar', 'solar'],
                             'used': [False, False, False]},
                            index=[1, 2, 3])

        # Expected
        used = pd.DataFrame({'quantity': [8, 6],
                             'cost': [10, 10],
                             'type': ['solar', 'solar'],
                             'used': [False, False]},
                            index=[1, 2])

        free = pd.DataFrame({'quantity': [4],
                             'cost': [10],
                             'type': ['solar'],
                             'used': [False]},
                            index=[3])

        # Test
        res_used, res_free = LedgerProduction.split_by_quantity(prod=prod, quantity=15)
        pd.testing.assert_frame_equal(used, res_used)
        pd.testing.assert_frame_equal(free, res_free)


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

    def test_compute_cost(self):
        ledger = LedgerConsumption()
        ledger.add(type='load', cost=10, quantity=100)

        self.assertEqual(0, ledger.compute_cost(quantity=150))
        self.assertEqual(500, ledger.compute_cost(quantity=50))

        ledger = LedgerConsumption()
        ledger.add(type='load1', cost=1, quantity=10)
        ledger.add(type='load2', cost=2, quantity=10)
        ledger.add(type='load3', cost=3, quantity=10)
        ledger.add(type='load4', cost=4, quantity=10)

        self.assertEqual(0, ledger.compute_cost(quantity=40))
        self.assertEqual(16, ledger.compute_cost(quantity=27))


class TestLedgerBorder(unittest.TestCase):
    def test(self):
        ledger = LedgerBorder()

        # Add
        ledger.add(dest='fr', cost=20, quantity=100)
        ledger.add(dest='be', cost=20, quantity=200)

        # Inspect
        expected = pd.DataFrame({'cost': [20, 20], 'quantity': [100, 200]}, index=['fr', 'be'])
        pd.testing.assert_frame_equal(expected, ledger.ledger)

        pd.testing.assert_series_equal(ledger.ledger.loc['fr'], ledger.find_border_in_path(['it', 'fr']))

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
