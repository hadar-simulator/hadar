#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest

import hadar as hd
from tests.utils import assert_study


class TestSolver(unittest.TestCase):

    def setUp(self) -> None:
        self.solver = hd.LPSolver()

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
        study = hd.Study(['a'], horizon=3, nb_scn=2) \
            .add_on_node(node='a', data=hd.Consumption(type='load', cost=10 ** 6, quantity=[[30, 6, 6], [6, 30, 30]])) \
            .add_on_node(node='a', data=hd.Production(type='nuclear', cost=20, quantity=[[15, 3, 3], [3, 15, 15]])) \
            .add_on_node(node='a', data=hd.Production(type='solar', cost=10, quantity=[[10, 2, 2], [2, 10, 10]])) \
            .add_on_node(node='a', data=hd.Production(type='oil', cost=30, quantity=[[10, 2, 2], [2, 10, 10]]))

        nodes_expected = dict()
        nodes_expected['a'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[30, 6, 6], [6, 30, 30]], type='load')],
            productions=[
                hd.OutputProduction(type='nuclear', cost=20, quantity=[[15, 3, 3], [3, 15, 15]]),
                hd.OutputProduction(type='solar', cost=10, quantity=[[10, 2, 2], [2, 10, 10]]),
                hd.OutputProduction(type='oil', cost=30, quantity=[[5, 1, 1], [1, 5, 5]])],
            borders=[])

        res = self.solver.solve(study)
        assert_study(self, hd.Result(nodes_expected), res)

    def test_exchange_two_nodes(self):
        """
        Capacity
        |          A           | --------> |          B           |
        | load: 20             |  10       | load: 20             |
        | nuclear: 30 @ 10     |           | nuclear: 10 @ 20     |


        Adequacy
        |          A           | --------> |          B           |
        | load: 20             | 10        | load: 20             |
        | nuclear: 30          |           | nuclear: 10          |

        :return:
        """
        # Input
        study = hd.Study(['a', 'b'], horizon=2) \
            .add_on_node('a', data=hd.Consumption(cost=10 ** 6, quantity=[20, 200], type='load')) \
            .add_on_node('a', data=hd.Production(cost=10, quantity=[30, 300], type='prod')) \
            .add_on_node('b', data=hd.Consumption(cost=10 ** 6, quantity=[20, 200], type='load')) \
            .add_on_node('b', data=hd.Production(cost=20, quantity=[10, 100], type='prod')) \
            .add_border(src='a', dest='b', quantity=[10, 100], cost=2)

        nodes_expected = {}
        nodes_expected['a'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[20, 200]], type='load')],
            productions=[hd.OutputProduction(cost=10, quantity=[[30, 300]], type='prod')],
            borders=[hd.OutputBorder(dest='b', quantity=[[10, 100]], cost=2)])

        nodes_expected['b'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[20, 200]], type='load')],
            productions=[hd.OutputProduction(cost=20, quantity=[[10, 100]], type='prod')],
            borders=[])

        res = self.solver.solve(study)
        assert_study(self, hd.Result(nodes_expected), res)

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
        study = hd.Study(node_names=['a', 'b', 'c'], horizon=1) \
            .add_on_node('a', data=hd.Consumption(cost=10 ** 6, quantity=[10], type='load')) \
            .add_on_node('a', data=hd.Production(cost=10, quantity=[30], type='nuclear')) \
            .add_on_node('b', data=hd.Consumption(cost=10 ** 6, quantity=[10], type='load')) \
            .add_on_node('b', data=hd.Production(cost=20, quantity=[10], type='nuclear')) \
            .add_on_node('c', data=hd.Consumption(cost=10 ** 6, quantity=[10], type='load')) \
            .add_on_node('c', data=hd.Production(cost=20, quantity=[10], type='nuclear')) \
            .add_border(src='a', dest='b', quantity=[20], cost=2) \
            .add_border(src='a', dest='c', quantity=[20], cost=2)

        nodes_expected = {}
        nodes_expected['a'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10]], type='load')],
            productions=[hd.OutputProduction(cost=10, quantity=[[30]], type='nuclear')],
            borders=[hd.OutputBorder(dest='b', quantity=[[10]], cost=2),
                     hd.OutputBorder(dest='c', quantity=[[10]], cost=2)])

        nodes_expected['b'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10]], type='load')],
            productions=[hd.OutputProduction(cost=20, quantity=[[0]], type='nuclear')],
            borders=[])

        nodes_expected['c'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10]], type='load')],
            productions=[hd.OutputProduction(cost=20, quantity=[[0]], type='nuclear')],
            borders=[])

        res = self.solver.solve(study)

        assert_study(self, hd.Result(nodes_expected), res)

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
        study = hd.Study(node_names=['a', 'b', 'c'], horizon=1) \
            .add_on_node('a', data=hd.Production(cost=10, quantity=[30], type='nuclear')) \
            .add_on_node('b', data=hd.Consumption(cost=10 ** 6, quantity=[10], type='load')) \
            .add_on_node('c', data=hd.Consumption(cost=10 ** 6, quantity=[20], type='load')) \
            .add_border(src='a', dest='b', quantity=[20], cost=2) \
            .add_border(src='b', dest='c', quantity=[15], cost=2)

        nodes_expected = {}
        nodes_expected['a'] = hd.OutputNode(productions=[hd.OutputProduction(cost=10, quantity=[[20]], type='nuclear')],
                                            borders=[hd.OutputBorder(dest='b', quantity=[[20]], cost=2)],
                                            consumptions=[])

        nodes_expected['b'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10]], type='load')],
            borders=[hd.OutputBorder(dest='c', quantity=[[10]], cost=2)],
            productions=[])

        nodes_expected['c'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10]], type='load')],
            productions=[],
            borders=[])

        res = self.solver.solve(study)

        assert_study(self, hd.Result(nodes_expected), res)

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
        study = hd.Study(node_names=['a', 'b', 'c'], horizon=1) \
            .add_on_node('a', data=hd.Consumption(cost=10 ** 6, quantity=[10], type='load')) \
            .add_on_node('a', data=hd.Production(cost=10, quantity=[20], type='nuclear')) \
            .add_on_node('b', data=hd.Consumption(cost=10 ** 6, quantity=[5], type='load')) \
            .add_on_node('b', data=hd.Production(cost=20, quantity=[15], type='nuclear')) \
            .add_on_node('c', data=hd.Consumption(cost=10 ** 6, quantity=[20], type='load')) \
            .add_on_node('c', data=hd.Production(cost=10, quantity=[10], type='nuclear')) \
            .add_border(src='a', dest='b', quantity=[20], cost=2) \
            .add_border(src='b', dest='c', quantity=[20], cost=2)

        nodes_expected = {}
        nodes_expected['a'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10]], type='load')],
            productions=[hd.OutputProduction(cost=10, quantity=[[20]], type='nuclear')],
            borders=[hd.OutputBorder(dest='b', quantity=[[10]], cost=2)])

        nodes_expected['b'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[5]], type='load')],
            productions=[hd.OutputProduction(cost=20, quantity=[[5]], type='nuclear')],
            borders=[hd.OutputBorder(dest='c', quantity=[[10]], cost=2)])

        nodes_expected['c'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[20]], type='load')],
            productions=[hd.OutputProduction(cost=10, quantity=[[10]], type='nuclear')],
            borders=[])

        res = self.solver.solve(study)

        assert_study(self, hd.Result(nodes_expected), res)


    def test_many_borders_on_node(self):
        """
        Capacity
        |           A           | -------->  |           B           |
        | load: 10              |  20 @ 10   | load: 15, 25          |
        | gas:  20 @ 80         |               /\
                    /\                          |
                    |                           |
                    | 20 @ 10                   | 20 @ 10
                    |                           |
        |           C           | ---------------
        | nuclear: 30 @ 50      |


        Adequacy
        |           A           | -------------> |           B           |
        | load: 10              |  0, 10 @ 10    | load: 15, 25          |
        | gas:  0, 5 @ 80       |                   /\
                    /\                              |
                    |                               |
                    | 20 @ 10                       | 15 @ 10
                    |                               |
        |           C           | -------------------
        | nuclear: 25, 30 @ 50  |

        :return:
        """
        study = hd.Study(node_names=['a', 'b', 'c'], horizon=2) \
            .add_on_node('a', data=hd.Consumption(cost=10 ** 6, quantity=10, type='load')) \
            .add_on_node('a', data=hd.Production(cost=80, quantity=20, type='gas')) \
            .add_on_node('b', data=hd.Consumption(cost=10 ** 6, quantity=[15, 25], type='load')) \
            .add_on_node('c', data=hd.Production(cost=50, quantity=30, type='nuclear')) \
            .add_border(src='a', dest='b', quantity=20, cost=10) \
            .add_border(src='c', dest='a', quantity=20, cost=10) \
            .add_border(src='c', dest='b', quantity=15, cost=10)


        nodes_expected = {}
        nodes_expected['a'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10, 10]], type='load')],
            productions=[hd.OutputProduction(cost=80, quantity=[[0, 5]], type='gas')],
            borders=[hd.OutputBorder(dest='b', quantity=[[0, 10]], cost=10)])

        nodes_expected['b'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[15, 25]], type='load')],
            productions=[], borders=[])

        nodes_expected['c'] = hd.OutputNode(
            productions=[hd.OutputProduction(cost=50, quantity=[[25, 30]], type='nuclear')],
            borders=[], consumptions=[])

        res = self.solver.solve(study)

        assert_study(self, hd.Result(nodes_expected), res)