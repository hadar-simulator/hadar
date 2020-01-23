import logging
import unittest

from tests.utils import assert_study

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('pykka').setLevel(logging.INFO)

from hadar.solver.actor.domain.input import *
# from hadar.solver.actor_solver import solve
from hadar.solver.mathprog_solver import solve


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
        nodes['a'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[30], type='load')],
                               productions=[
                                   InputProduction(type='nuclear', cost=20, quantity=[15]),
                                   InputProduction(type='solar', cost=10, quantity=[10]),
                                   InputProduction(type='oil', cost=30, quantity=[10])],
                               borders=[])

        nodes_expected = dict()
        nodes_expected['a'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[30], type='load')],
                                        productions=[
                                            InputProduction(type='nuclear', cost=20, quantity=[15]),
                                            InputProduction(type='solar', cost=10, quantity=[10]),
                                            InputProduction(type='oil', cost=30, quantity=[5])],
                                        borders=[])

        res = solve(Study(nodes=nodes))
        assert_study(self, Study(nodes_expected), res)

    def test_exchange_two_concurrent_nodes(self):
        """
        Capacity
        |          A           | --------> |          B           |
        | load: 10             |  10       | load: 10             |
        | nuclear: 30 @ 10     | ----.     | nuclear: 10 @ 20     |
                                  10 |
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
        nodes['a'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                               productions=[InputProduction(cost=10, quantity=[30], type='nuclear')],
                               borders=[InputBorder(dest='b', quantity=[20], cost=2),
                                        InputBorder(dest='c', quantity=[20], cost=2)])

        nodes['b'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                               productions=[InputProduction(cost=20, quantity=[10], type='nuclear')])

        nodes['c'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                               productions=[InputProduction(cost=20, quantity=[10], type='nuclear')])

        nodes_expected = {}
        nodes_expected['a'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                                        productions=[InputProduction(cost=10, quantity=[30], type='nuclear')],
                                        borders=[InputBorder(dest='b', quantity=[10], cost=2),
                                                 InputBorder(dest='c', quantity=[10], cost=2)])

        nodes_expected['b'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                                        productions=[InputProduction(cost=20, quantity=[0], type='nuclear')])

        nodes_expected['c'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                                        productions=[InputProduction(cost=20, quantity=[0], type='nuclear')])

        res = solve(Study(nodes=nodes))

        assert_study(self, Study(nodes_expected), res)

    def test_exchange_border_saturation(self):
        """
        Capacity
        |           A           | ---->  |           B           | ---->  |           C           |
        | nuclear: 30 @ 10      | 20     |  load: 10             | 15     | load: 20              |


        Adequacy
        |           A           | ---->  |           B           | ---->  |           C           |
        | nuclear: 20           | 20     |  load: 10             | 10     | load: 20              |

        :return:
        """
        nodes = {}
        nodes['a'] = InputNode(productions=[InputProduction(cost=10, quantity=[30], type='nuclear')],
                               borders=[InputBorder(dest='b', quantity=[20], cost=2)])

        nodes['b'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[10])],
                               borders=[InputBorder(dest='c', quantity=[15], cost=2)])

        nodes['c'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[20], type='load')])

        nodes_expected = {}
        nodes_expected['a'] = InputNode(productions=[InputProduction(cost=10, quantity=[20], type='nuclear')],
                                        borders=[InputBorder(dest='b', quantity=[20], cost=2)])

        nodes_expected['b'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[10])],
                                        borders=[InputBorder(dest='c', quantity=[10], cost=2)])

        nodes_expected['c'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[20], type='load')])

        res = solve(Study(nodes=nodes))

        assert_study(self, Study(nodes_expected), res)

    def test_consumer_cancel_exchange(self):
        """
        Capacity
        |           A           | ---->  |           B           | ---->  |           C           |
        | load: 10              |  20    | load: 5               |  20    | load: 20              |
        | nuclear: 20 @ 10      |        | nuclear: 15 @ 20      |        | nuclear: 10 @ 10      |


        Adequacy
        |           A           | ---->  |           B           | ---->  |           C           |
        | load: 10              | 10     | load: 5               | 10     | load: 20              |
        | nuclear: 20           |        | nuclear: 5            |        | nuclear: 10           |


        :return:
        """

        nodes = {}
        nodes['a'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                               productions=[InputProduction(cost=10, quantity=[20], type='nuclear')],
                               borders=[InputBorder(dest='b', quantity=[20], cost=2)])

        nodes['b'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[5], type='load')],
                               productions=[InputProduction(cost=20, quantity=[15], type='nuclear')],
                               borders=[InputBorder(dest='c', quantity=[20], cost=2)])

        nodes['c'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[20], type='load')],
                               productions=[InputProduction(cost=10, quantity=[10], type='nuclear')])

        nodes_expected = {}
        nodes_expected['a'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                                        productions=[InputProduction(cost=10, quantity=[20], type='nuclear')],
                                        borders=[InputBorder(dest='b', quantity=[10], cost=2)])

        nodes_expected['b'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[5], type='load')],
                                        productions=[InputProduction(cost=20, quantity=[5], type='nuclear')],
                                        borders=[InputBorder(dest='c', quantity=[10], cost=2)])

        nodes_expected['c'] = InputNode(consumptions=[InputConsumption(cost=10 ** 6, quantity=[20], type='load')],
                                        productions=[InputProduction(cost=10, quantity=[10], type='nuclear')])

        res = solve(Study(nodes=nodes))

        assert_study(self, Study(nodes_expected), res)
