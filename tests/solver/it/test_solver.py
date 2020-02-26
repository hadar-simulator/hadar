import unittest

from hadar.solver.input import *
from hadar.solver.output import *
from hadar.solver.study import solve
from tests.utils import assert_study


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
        study = Study(['a']) \
            .add_on_node(node='a', data=Consumption(type='load', cost=10 ** 6, quantity=[30, 6])) \
            .add_on_node(node='a', data=Production(type='nuclear', cost=20, quantity=[15, 3])) \
            .add_on_node(node='a', data=Production(type='solar', cost=10, quantity=[10, 2])) \
            .add_on_node(node='a', data=Production(type='oil', cost=30, quantity=[10, 2]))

        nodes_expected = dict()
        nodes_expected['a'] = OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[30, 6], type='load')],
                                         productions=[
                                             OutputProduction(type='nuclear', cost=20, quantity=[15, 3]),
                                             OutputProduction(type='solar', cost=10, quantity=[10, 2]),
                                             OutputProduction(type='oil', cost=30, quantity=[5, 1])],
                                         borders=[])

        res = solve(study, kind='lp')
        assert_study(self, Result(nodes_expected), res)

    def test_exchange_two_nodes(self):
        # Input
        study = Study(['a', 'b']) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[20, 200], type='load')) \
            .add_on_node('a', data=Production(cost=10, quantity=[30, 300], type='prod')) \
            .add_on_node('b', data=Consumption(cost=10 ** 6, quantity=[20, 200], type='load')) \
            .add_on_node('b', data=Production(cost=20, quantity=[10, 100], type='prod')) \
            .add_border(src='a', dest='b', quantity=[10, 100], cost=2)

        nodes_expected = {}
        nodes_expected['a'] = OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[20, 200], type='load')],
                                         productions=[OutputProduction(cost=10, quantity=[30, 300], type='prod')],
                                         borders=[OutputBorder(dest='b', quantity=[10, 100], cost=2)])

        nodes_expected['b'] = OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[20, 200], type='load')],
                                         productions=[OutputProduction(cost=20, quantity=[10, 100], type='prod')],
                                         borders=[])


        res = solve(study)
        assert_study(self, Result(nodes_expected), res)


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
        study = Study(node_names=['a', 'b', 'c']) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[10], type='load')) \
            .add_on_node('a', data=Production(cost=10, quantity=[30], type='nuclear')) \
            .add_on_node('b', data=Consumption(cost=10 ** 6, quantity=[10], type='load')) \
            .add_on_node('b', data=Production(cost=20, quantity=[10], type='nuclear')) \
            .add_on_node('c', data=Consumption(cost=10 ** 6, quantity=[10], type='load')) \
            .add_on_node('c', data=Production(cost=20, quantity=[10], type='nuclear')) \
            .add_border(src='a', dest='b', quantity=[20], cost=2) \
            .add_border(src='a', dest='c', quantity=[20], cost=2)

        nodes_expected = {}
        nodes_expected['a'] = OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                                         productions=[OutputProduction(cost=10, quantity=[30], type='nuclear')],
                                         borders=[OutputBorder(dest='b', quantity=[10], cost=2),
                                                  OutputBorder(dest='c', quantity=[10], cost=2)])

        nodes_expected['b'] = OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                                         productions=[OutputProduction(cost=20, quantity=[0], type='nuclear')],
                                         borders=[])

        nodes_expected['c'] = OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                                         productions=[OutputProduction(cost=20, quantity=[0], type='nuclear')],
                                         borders=[])

        res = solve(study, kind='lp')

        assert_study(self, Result(nodes_expected), res)

    def test_exchange_border_saturation(self):
        """
        Capacity
        |           A           | ---->  |           B           | ---->  |           C           |
        | nuclear: 30 @ 10      | 20     |  load: 10             | 15     | load: 20              |


        Adequacy
        |           A           | ---->  |           B           | ---->  |           C           |
        | nuclear: 20           | 20     |  load: 10             | 10     | load: 10              |

        :return:
        """
        study = Study(node_names=['a', 'b', 'c']) \
            .add_on_node('a', data=Production(cost=10, quantity=[30], type='nuclear')) \
            .add_on_node('b', data=Consumption(cost=10 ** 6, quantity=[10], type='load')) \
            .add_on_node('c', data=Consumption(cost=10 ** 6, quantity=[20], type='load')) \
            .add_border(src='a', dest='b', quantity=[20], cost=2) \
            .add_border(src='b', dest='c', quantity=[15], cost=2)

        nodes_expected = {}
        nodes_expected['a'] = OutputNode(productions=[OutputProduction(cost=10, quantity=[20], type='nuclear')],
                                         borders=[OutputBorder(dest='b', quantity=[20], cost=2)],
                                         consumptions=[])

        nodes_expected['b'] = OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                                         borders=[OutputBorder(dest='c', quantity=[10], cost=2)],
                                         productions=[])

        nodes_expected['c'] = OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                                         productions=[],
                                         borders=[])

        res = solve(study, kind='lp')

        assert_study(self, Result(nodes_expected), res)

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
        study = Study(node_names=['a', 'b', 'c']) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[10], type='load')) \
            .add_on_node('a', data=Production(cost=10, quantity=[20], type='nuclear')) \
            .add_on_node('b', data=Consumption(cost=10 ** 6, quantity=[5], type='load')) \
            .add_on_node('b', data=Production(cost=20, quantity=[15], type='nuclear')) \
            .add_on_node('c', data=Consumption(cost=10 ** 6, quantity=[20], type='load')) \
            .add_on_node('c', data=Production(cost=10, quantity=[10], type='nuclear')) \
            .add_border(src='a', dest='b', quantity=[20], cost=2) \
            .add_border(src='b', dest='c', quantity=[20], cost=2)

        nodes_expected = {}
        nodes_expected['a'] = OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[10], type='load')],
                                         productions=[OutputProduction(cost=10, quantity=[20], type='nuclear')],
                                         borders=[OutputBorder(dest='b', quantity=[10], cost=2)])

        nodes_expected['b'] = OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[5], type='load')],
                                         productions=[OutputProduction(cost=20, quantity=[5], type='nuclear')],
                                         borders=[OutputBorder(dest='c', quantity=[10], cost=2)])

        nodes_expected['c'] = OutputNode(consumptions=[OutputConsumption(cost=10 ** 6, quantity=[20], type='load')],
                                         productions=[OutputProduction(cost=10, quantity=[10], type='nuclear')],
                                         borders=[])

        res = solve(study, kind='lp')

        assert_study(self, Result(nodes_expected), res)
