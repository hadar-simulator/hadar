import unittest

import time
import logging

from utils import assert_study

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('pykka').setLevel(logging.INFO)

from pykka import ActorRef

from dispatcher.domain import *
from solver import solve


class TestSolver(unittest.TestCase):

    def test_merit_order(self):
        """
        Capacity
        |          A           |
        | load: 30             |
        | solar: 10 @ 10       |
        | nuclear: 15 @ 20     |
        | gas: 10 @ 30         |


        Adequacy
        |          A           |
        | load: 30             |
        | solar: 10            |
        | nuclear: 15          |
        | gas: 5               |
        :return:
        """
        nodes = dict()
        nodes['a'] = NodeQuantity(min_exchange=1,
                                  consumptions=[Consumption(cost=10**6, quantity=30, type='load')],
                                  productions=[
                                      Production(type='nuclear', cost=20, quantity=15),
                                      Production(type='solar', cost=10, quantity=10),
                                      Production(type='oil', cost=30, quantity=10)],
                                  borders=[])

        nodes_expected = dict()
        nodes_expected['a'] = NodeQuantity(min_exchange=1,
                                           consumptions=[Consumption(cost=10**6, quantity=30, type='load')],
                                           productions=[
                                               Production(type='nuclear', cost=20, quantity=15),
                                               Production(type='solar', cost=10, quantity=10),
                                               Production(type='oil', cost=30, quantity=5)],
                                           borders=[])

        res = solve(Study(nodes=nodes))
        assert_study(self, Study(nodes_expected), res)

    def test_exchange_two_concurrent_nodes(self):
        """
        Capacity
        |          A           | --------> |          B           |
        | load: 10             |           | load: 10             |
        | nuclear: 30 @ 10     | ----.     | nuclear: 10 @ 20     |
                                     |
                                     .---> |          C           |
                                           | load: 10             |
                                           | nuclear: 10 @ 20     |

        Adequacy
        |          A           | --------> |          B           |
        | load: 10             | 10        | load: 10             |
        | nuclear: 30          | ----.     | nuclear: 0           |
                                 10  |
                                     .---> |          C           |
                                           | load: 10             |
                                           | nuclear: 0           |
        :return:
        """

        nodes = {}
        nodes['a'] = NodeQuantity(min_exchange=1,
                                  consumptions=[Consumption(cost=10 ** 6, quantity=10, type='load')],
                                  productions=[Production(cost=10, quantity=30, type='nuclear')],
                                  borders=[Border(dest='b', capacity=10, cost=2),
                                           Border(dest='c', capacity=10, cost=2)])

        nodes['b'] = NodeQuantity(min_exchange=1,
                                  consumptions=[Consumption(cost=10 ** 6, quantity=10, type='load')],
                                  productions=[Production(cost=20, quantity=10, type='nuclear')])

        nodes['c'] = NodeQuantity(min_exchange=1,
                                  consumptions=[Consumption(cost=10 ** 6, quantity=10, type='load')],
                                  productions=[Production(cost=10, quantity=10, type='nuclear')])

        nodes_expected = {}
        nodes_expected['a'] = NodeQuantity(min_exchange=1,
                                           consumptions=[Consumption(cost=10 ** 6, quantity=10, type='load')],
                                           productions=[Production(cost=10, quantity=30, type='nuclear')],
                                           borders=[])  # TODO

        nodes_expected['b'] = NodeQuantity(min_exchange=1,
                                           consumptions=[Consumption(cost=10 ** 6, quantity=5, type='load')],
                                           productions=[Production(cost=20, quantity=0, type='nuclear')])

        nodes_expected['c'] = NodeQuantity(min_exchange=1,
                                           consumptions=[Consumption(cost=10 ** 6, quantity=20, type='load')],
                                           productions=[Production(cost=10, quantity=0, type='nuclear')])

        res = solve(Study(nodes=nodes))

        assert_study(self, Study(nodes_expected), res)

    def test_exchange_border_saturation(self):
        pass

    def test_consumer_cancel_exchange(self):
        """
        Capacity
        |           A           | ---->  |           B           | ---->  |           C           |
        | load: 10              |        | load: 5               |        | load: 20              |
        | nuclear: 30 @ 10      |        | nuclear: 15 @ 20      |        | nuclear: 10 @ 10      |


        Adequacy
        |           A           | ---->  |           B           | ---->  |           C           |
        | load: 10              |        | load: 5               |        | load: 20              |
        | nuclear: 20           |        | nuclear: 5            |        | nuclear: 10           |


        :return:
        """

        nodes = {}
        nodes['a'] = NodeQuantity(min_exchange=1,
                                  consumptions=[Consumption(cost=10 ** 6, quantity=10, type='load')],
                                  productions=[Production(cost=10, quantity=20, type='nuclear')],
                                  borders=[Border(dest='b', capacity=10, cost=2)])

        nodes['b'] = NodeQuantity(min_exchange=1,
                                  consumptions=[Consumption(cost=10 ** 6, quantity=5, type='load')],
                                  productions=[Production(cost=20, quantity=15, type='nuclear')],
                                  borders=[Border(dest='c', capacity=1, cost=2)])

        nodes['c'] = NodeQuantity(min_exchange=1,
                                  consumptions=[Consumption(cost=10 ** 6, quantity=20, type='load')],
                                  productions=[Production(cost=10, quantity=10, type='nuclear')])

        nodes_expected = {}
        nodes_expected['a'] = NodeQuantity(min_exchange=1,
                                           consumptions=[Consumption(cost=10 ** 6, quantity=10, type='load')],
                                           productions=[Production(cost=10, quantity=20, type='nuclear')],
                                           borders=[])

        nodes_expected['b'] = NodeQuantity(min_exchange=1,
                                           consumptions=[Consumption(cost=10 ** 6, quantity=5, type='load')],
                                           productions=[Production(cost=20, quantity=5, type='nuclear')],
                                           borders=[])

        nodes_expected['c'] = NodeQuantity(min_exchange=1,
                                           consumptions=[Consumption(cost=10 ** 6, quantity=20, type='load')],
                                           productions=[Production(cost=10, quantity=10, type='nuclear')])

        res = solve(Study(nodes=nodes))

        assert_study(self, Study(nodes_expected), res)
