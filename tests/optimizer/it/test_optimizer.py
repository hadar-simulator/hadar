#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest

import hadar as hd
from hadar.optimizer.output import OutputNetwork
from tests.utils import assert_result


class TestOptimizer(unittest.TestCase):

    def setUp(self) -> None:
        self.optimizer = hd.LPOptimizer()

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
        study = hd.Study(horizon=3, nb_scn=2)\
            .network()\
                .node('a')\
                    .consumption(name='load', cost=10 ** 6, quantity=[[30, 6, 6], [6, 30, 30]])\
                    .production(name='nuclear', cost=20, quantity=[[15, 3, 3], [3, 15, 15]])\
                    .production(name='solar', cost=10, quantity=[[10, 2, 2], [2, 10, 10]])\
                    .production(name='oil', cost=30, quantity=[[10, 2, 2], [2, 10, 10]])\
            .build()

        nodes_expected = dict()
        nodes_expected['a'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[30, 6, 6], [6, 30, 30]], name='load')],
            productions=[
                hd.OutputProduction(name='nuclear', cost=20, quantity=[[15, 3, 3], [3, 15, 15]]),
                hd.OutputProduction(name='solar', cost=10, quantity=[[10, 2, 2], [2, 10, 10]]),
                hd.OutputProduction(name='oil', cost=30, quantity=[[5, 1, 1], [1, 5, 5]])],
            storages=[],
            links=[])

        res = self.optimizer.solve(study)
        assert_result(self, hd.Result(networks={'default': OutputNetwork(nodes_expected)}, converters={}), res)

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
        study = hd.Study(horizon=2)\
            .network()\
                .node('a')\
                    .consumption(cost=10 ** 6, quantity=[20, 200], name='load')\
                    .production(cost=10, quantity=[30, 300], name='prod')\
                .node('b')\
                    .consumption(cost=10 ** 6, quantity=[20, 200], name='load')\
                    .production(cost=20, quantity=[10, 100], name='prod')\
                .link(src='a', dest='b', quantity=[10, 100], cost=2)\
            .build()

        nodes_expected = {}
        nodes_expected['a'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[20, 200]], name='load')],
            productions=[hd.OutputProduction(cost=10, quantity=[[30, 300]], name='prod')],
            storages=[],
            links=[hd.OutputLink(dest='b', quantity=[[10, 100]], cost=2)])

        nodes_expected['b'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[20, 200]], name='load')],
            productions=[hd.OutputProduction(cost=20, quantity=[[10, 100]], name='prod')],
            storages=[],
            links=[])

        res = self.optimizer.solve(study)
        assert_result(self, hd.Result(networks={'default': OutputNetwork(nodes_expected)}, converters={}), res)

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
        study = hd.Study(horizon=1)\
            .network()\
                .node('a')\
                    .consumption(cost=10 ** 6, quantity=10, name='load')\
                    .production(cost=10, quantity=30, name='nuclear')\
                .node('b')\
                    .consumption(cost=10 ** 6, quantity=10, name='load')\
                    .production(cost=20, quantity=10, name='nuclear')\
                .node('c')\
                    .consumption(cost=10 ** 6, quantity=10, name='load')\
                    .production(cost=20, quantity=10, name='nuclear')\
                .link(src='a', dest='b', quantity=20, cost=2)\
                .link(src='a', dest='c', quantity=20, cost=2)\
            .build()

        nodes_expected = {}
        nodes_expected['a'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10]], name='load')],
            productions=[hd.OutputProduction(cost=10, quantity=[[30]], name='nuclear')],
            storages=[],
            links=[hd.OutputLink(dest='b', quantity=[[10]], cost=2),
                   hd.OutputLink(dest='c', quantity=[[10]], cost=2)])

        nodes_expected['b'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10]], name='load')],
            productions=[hd.OutputProduction(cost=20, quantity=[[0]], name='nuclear')],
            storages=[],
            links=[])

        nodes_expected['c'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10]], name='load')],
            productions=[hd.OutputProduction(cost=20, quantity=[[0]], name='nuclear')],
            storages=[],
            links=[])

        res = self.optimizer.solve(study)

        assert_result(self, hd.Result(networks={'default': OutputNetwork(nodes_expected)}, converters={}), res)

    def test_exchange_link_saturation(self):
        """
        Capacity
        |           A           | ---->  |           B           | ---->  |           C           |
        | nuclear: 30 @ 10      | 20     |  load: 10             | 15     | load: 20              |


        Adequacy
        |           A           | ---->  |           B           | ---->  |           C           |
        | nuclear: 20           | 20     |  load: 10             | 10     | load: 10              |

        :return:
        """
        study = hd.Study(horizon=1)\
            .network()\
                .node('a').production(cost=10, quantity=[30], name='nuclear')\
                .node('b').consumption(cost=10 ** 6, quantity=[10], name='load')\
                .node('c').consumption(cost=10 ** 6, quantity=[20], name='load')\
                .link(src='a', dest='b', quantity=[20], cost=2)\
                .link(src='b', dest='c', quantity=[15], cost=2)\
            .build()

        nodes_expected = {}
        nodes_expected['a'] = hd.OutputNode(productions=[hd.OutputProduction(cost=10, quantity=[[20]], name='nuclear')],
                                            links=[hd.OutputLink(dest='b', quantity=[[20]], cost=2)],
                                            storages=[], consumptions=[])

        nodes_expected['b'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10]], name='load')],
            links=[hd.OutputLink(dest='c', quantity=[[10]], cost=2)],
            storages=[],
            productions=[])

        nodes_expected['c'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10]], name='load')],
            productions=[],
            storages=[],
            links=[])

        res = self.optimizer.solve(study)

        assert_result(self, hd.Result(networks={'default': OutputNetwork(nodes_expected)}, converters={}), res)

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
        study = hd.Study(horizon=1)\
            .network()\
                .node('a')\
                    .consumption(cost=10 ** 6, quantity=10, name='load')\
                    .production(cost=10, quantity=20, name='nuclear')\
                .node('b')\
                    .consumption(cost=10 ** 6, quantity=5, name='load')\
                    .production(cost=20, quantity=15, name='nuclear')\
                .node('c')\
                    .consumption(cost=10 ** 6, quantity=20, name='load')\
                    .production(cost=10, quantity=10, name='nuclear')\
                .link(src='a', dest='b', quantity=20, cost=2)\
                .link(src='b', dest='c', quantity=20, cost=2)\
            .build()

        nodes_expected = {}
        nodes_expected['a'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10]], name='load')],
            productions=[hd.OutputProduction(cost=10, quantity=[[20]], name='nuclear')],
            storages=[],
            links=[hd.OutputLink(dest='b', quantity=[[10]], cost=2)])

        nodes_expected['b'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[5]], name='load')],
            productions=[hd.OutputProduction(cost=20, quantity=[[5]], name='nuclear')],
            storages=[],
            links=[hd.OutputLink(dest='c', quantity=[[10]], cost=2)])

        nodes_expected['c'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[20]], name='load')],
            productions=[hd.OutputProduction(cost=10, quantity=[[10]], name='nuclear')],
            storages=[],
            links=[])

        res = self.optimizer.solve(study)

        assert_result(self, hd.Result(networks={'default': OutputNetwork(nodes_expected)}, converters={}), res)


    def test_many_links_on_node(self):
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
        study = hd.Study(horizon=2)\
            .network()\
                .node('a')\
                    .consumption(cost=10 ** 6, quantity=10, name='load')\
                    .production(cost=80, quantity=20, name='gas')\
                .node('b')\
                    .consumption(cost=10 ** 6, quantity=[15, 25], name='load')\
                .node('c')\
                    .production(cost=50, quantity=30, name='nuclear')\
                .link(src='a', dest='b', quantity=20, cost=10)\
                .link(src='c', dest='a', quantity=20, cost=10)\
                .link(src='c', dest='b', quantity=15, cost=10)\
            .build()


        nodes_expected = {}
        nodes_expected['a'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[10, 10]], name='load')],
            productions=[hd.OutputProduction(cost=80, quantity=[[0, 5]], name='gas')],
            storages=[], links=[hd.OutputLink(dest='b', quantity=[[0, 10]], cost=10)])

        nodes_expected['b'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[15, 25]], name='load')],
            storages=[], productions=[], links=[])

        nodes_expected['c'] = hd.OutputNode(
            productions=[hd.OutputProduction(cost=50, quantity=[[25, 30]], name='nuclear')],
            storages=[], links=[], consumptions=[])

        res = self.optimizer.solve(study)

        assert_result(self, hd.Result(networks={'default': OutputNetwork(nodes_expected)}, converters={}), res)

    def test_storage(self):
        """
                Capacity
        |          A           | --------> |          B           |
        | nuclear: 10 @ 20     |  10       | load: 20, 10, 0, 10  |
        |                      |           | storage: 0 @ 30     |
        :return:
        """

        study = hd.Study(horizon=4)\
            .network()\
                .node('a')\
                    .production(name='nuclear', cost=20, quantity=[10, 10, 10, 0]) \
                .node('b')\
                    .consumption(name='load', cost=10 ** 6, quantity=[20, 10, 0, 10]) \
                    .storage(name='cell', capacity=30, flow_in=20, flow_out=20,
                             init_capacity=15, eff=.5)\
            .link(src='a', dest='b', cost=1, quantity=10)\
            .build()

        nodes_expected = dict()
        nodes_expected['a'] = hd.OutputNode(
            productions=[hd.OutputProduction(cost=20, quantity=[[10, 10, 10, 0]], name='nuclear')],
            storages=[], consumptions=[], links=[hd.OutputLink(dest='b', quantity=[[10, 10, 10, 0]], cost=1)])

        nodes_expected['b'] = hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10 ** 6, quantity=[[20, 10, 0, 10]], name='load')],
            storages=[hd.OutputStorage(name='cell', capacity=[[5, 5, 10, 0]],
                                       flow_in=[[0, 0, 10, 0]], flow_out=[[10, 0, 0, 10]])],
            productions=[], links=[])

        res = self.optimizer.solve(study)

        assert_result(self, hd.Result(networks={'default': OutputNetwork(nodes_expected)}, converters={}), res)

    def test_multi_energies(self):
        study = hd.Study(horizon=1)\
            .network('elec')\
                .node('a')\
                    .consumption(name='load', cost=10**6, quantity=10)\
            .network('gas')\
                .node('b')\
                    .production(name='central', cost=10, quantity=50)\
                    .to_converter(name='conv', ratio=0.8)\
            .network('coat')\
                .node('c')\
                    .production(name='central', cost=10, quantity=50)\
                    .to_converter(name='conv', ratio=0.5)\
            .converter(name='conv', to_network='elec', to_node='a', max=50)\
            .build()

        networks_expected = dict()
        networks_expected['elec'] = hd.OutputNetwork(nodes={'a': hd.OutputNode(
            consumptions=[hd.OutputConsumption(cost=10**6, quantity=[[10]], name='load')],
            storages=[], productions=[], links=[])})

        networks_expected['gas'] = hd.OutputNetwork(nodes={'b': hd.OutputNode(
            productions=[hd.OutputProduction(cost=10, quantity=[[12.5]], name='central')],
            storages=[], consumptions=[], links=[])})

        networks_expected['coat'] = hd.OutputNetwork(nodes={'c': hd.OutputNode(
            productions=[hd.OutputProduction(cost=10, quantity=[[20]], name='central')],
            storages=[], consumptions=[], links=[])})

        converter_expected = hd.OutputConverter(name='conv', flow_src={('gas', 'b'): [[12.5]], ('coat', 'c'): [[20]]}, flow_dest=[[10]])

        res = self.optimizer.solve(study)

        assert_result(self, hd.Result(networks=networks_expected, converters={'conv': converter_expected}), res)