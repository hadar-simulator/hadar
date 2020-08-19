#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import numpy as np

from hadar.optimizer.output import Result


def assert_result(self, expected: Result, result: Result):
    for name_network, network in expected.networks.items():
        if name_network not in result.networks.keys():
            self.fail('Network {} expected but not'.format(name_network))

        for name_node, node in network.nodes.items():
            if name_node not in result.networks[name_network].nodes.keys():
                self.fail('Node {} expected but not'.format(name_node))
            res = result.networks[name_network].nodes[name_node]

            # Consumptions
            for cons_expected, cons_res in zip(node.consumptions, res.consumptions):
                self.assertEqual(cons_expected.name, cons_res.name,
                                 "Consumption for node {} has different name".format(name_node))
                np.testing.assert_array_equal(cons_expected.quantity, cons_res.quantity,
                                 'Consumption {} for node {} has different quantity'.format(cons_expected.name, name_node))
                np.testing.assert_array_equal(cons_expected.cost, cons_res.cost,
                                 'Consumption {} for node {} has different cost'.format(cons_expected.name, name_node))

            # Productions
            for prod_expected, prod_res in zip(node.productions, res.productions):
                self.assertEqual(prod_expected.name, prod_res.name,
                                 "Production for node {} has different name".format(name_node))
                np.testing.assert_array_equal(prod_expected.quantity, prod_res.quantity,
                                 'Production {} for node {} has different quantity'.format(prod_expected.name, name_node))
                np.testing.assert_array_equal(prod_expected.cost, prod_res.cost,
                                 'Production {} for node {} has different cost'.format(prod_expected.name, name_node))

            # Storage
            for stor_expected, stor_res in zip(node.storages, res.storages):
                self.assertEqual(stor_expected.name, stor_res.name,
                                 'Storage for node {} has different name'.format(name_node))
                np.testing.assert_array_almost_equal(stor_expected.flow_in, stor_res.flow_in, 4,
                                'Storage {} for node {} has different flow in'.format(stor_res.name, name_node))
                np.testing.assert_array_almost_equal(stor_expected.flow_out, stor_res.flow_out, 4,
                                'Storage {} for node {} has different flow out'.format(stor_res.name, name_node))
                np.testing.assert_array_almost_equal(stor_expected.capacity, stor_res.capacity, 4,
                                'Storage {} for node {} has different capacity'.format(stor_res.name, name_node))

            # Links
            for link_expected, link_res in zip(node.links, res.links):
                self.assertEqual(link_expected.dest, link_res.dest,
                                 "Link for node {} has different name".format(name_node))
                np.testing.assert_array_equal(link_expected.quantity, link_res.quantity,
                                 'Link {} for node {} has different quantity'.format(link_expected.dest, name_node))
                np.testing.assert_array_equal(link_expected.cost, link_res.cost,
                                 'Link {} for node {} has different cost'.format(link_expected.dest, name_node))

    # Converter
    for name, exp in expected.converters.items():
        self.assertTrue(name in result.converters, 'Converter {} not in result'.format(name))
        for src, flow in exp.flow_src.items():
            self.assertTrue(src in result.converters[name].flow_src, 'Converter {} has not src {} in result'.format(name, src))
            np.testing.assert_array_equal(flow, result.converters[name].flow_src[src],
                                          'converter {} as different source {}'.format(name, src))

        np.testing.assert_array_equal(exp.flow_dest, result.converters[name].flow_dest,
                                      'Converter {} has different flow dest'.format(name))
