import unittest

from solver.actor.adequacy import *
from solver.actor.domain import *


class TestAdequacy(unittest.TestCase):

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

        productions_used = [
            Production(type='solar', cost=5, quantity=50),
            Production(type='nuclear', cost=10, quantity=200),
            Production(type='oil', cost=20, quantity=50)
        ]

        # Compare
        expected_state = NodeState(productions_used, productions_free, 3250, 150)

        state = optimize_adequacy(consumptions, productions)
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

        state = optimize_adequacy(consumptions, productions)
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

        state = optimize_adequacy(consumptions, productions)
        self.assertEqual(expected_state, state)

    def test_clean_production(self):
        # Input
        productions = [
            Production(id=2, cost=20, quantity=10),
            Production(id=1, cost=40, quantity=10),
            Production(id=0, cost=10, quantity=10),
            Production(id=2, cost=20, quantity=10),
        ]

        # Expected
        expected = [
            Production(id=0, cost=10, quantity=10),
            Production(id=2, cost=20, quantity=20),
            Production(id=1, cost=40, quantity=10)
        ]

        self.assertEqual(expected, clean_production(productions), 'Productions is not cleaned')

    def test_is_same_prod(self):
        a = Production(id=0, cost=0, quantity=0)
        b = Production(id=1, cost=0, quantity=0)
        c = Production(id=0, cost=0, quantity=0, exchange=Exchange(id=1))
        e = Production(id=2, cost=0, quantity=0, exchange=Exchange(id=2))
        f = Production(id=2, cost=0, quantity=0, exchange=Exchange(id=3))

        self.assertTrue(is_same_prod(a, a))
        self.assertTrue(is_same_prod(e, e))

        self.assertFalse(is_same_prod(a, b))
        self.assertFalse(is_same_prod(a, c))
        self.assertFalse(is_same_prod(e, f))
