import unittest

import time

from domain import Consumption, Production, Border, Start
from node import DispatcherRegistry, Dispatcher


class TestSolver(unittest.TestCase):

    def test_two_nodes_on_side(self):
        resolver = DispatcherRegistry()

        a = Dispatcher.start(name='a',
                         consumptions=[Consumption(cost=10**6, quantity=1000)],
                         productions=[Production(cost=10, quantity=1500, type='nuclear')],
                         borders=[Border(dest='b', capacity=1000, cost=2)])

        b = Dispatcher.start(name='b',
                         consumptions=[Consumption(cost=10**6, quantity=1000)],
                         productions=[Production(cost=10, quantity=500, type='nuclear')])

        a.tell(Start())
        b.tell(Start())

        time.sleep(2)
        a.stop()
        b.stop()
