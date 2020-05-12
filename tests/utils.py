#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import numpy as np

from hadar.optimizer.output import Result


def assert_study(self, expected: Result, result: Result):
    for name, node in expected.nodes.items():
        if name not in result.nodes.keys():
            self.fail('Node {} expected but not'.format(name))
        res = result.nodes[name]

        # Consumptions
        for cons_expected, cons_res in zip(node.consumptions, res.consumptions):
            self.assertEqual(cons_expected.name, cons_res.name,
                             "Consumption for node {} has different name".format(name))
            np.testing.assert_array_equal(cons_expected.quantity, cons_res.quantity,
                             'Consumption {} for node {} has different quantity'.format(cons_expected.name, name))
            self.assertEqual(cons_expected.cost, cons_res.cost,
                             'Consumption {} for node {} has different cost'.format(cons_expected.name, name))

        # Productions
        for prod_expected, prod_res in zip(node.productions, res.productions):
            self.assertEqual(prod_expected.name, prod_res.name,
                             "Production for node {} has different name".format(name))
            np.testing.assert_array_equal(prod_expected.quantity, prod_res.quantity,
                             'Production {} for node {} has different quantity'.format(prod_expected.name, name))
            self.assertEqual(prod_expected.cost, prod_res.cost,
                             'Production {} for node {} has different cost'.format(prod_expected.name, name))

        # Links
        for link_expected, link_res in zip(node.links, res.links):
            self.assertEqual(link_expected.dest, link_res.dest,
                             "Link for node {} has different name".format(name))
            np.testing.assert_array_equal(link_expected.quantity, link_res.quantity,
                             'Link {} for node {} has different quantity'.format(link_expected.dest, name))
            self.assertEqual(link_expected.cost, link_res.cost,
                             'Link {} for node {} has different cost'.format(link_expected.dest, name))


def plot(d):

    print('=============================================================================================')
    print("Node ", d.state.name, 'rac=', d.state.rac, 'cost=', d.state.cost)
    print('\nEvents')
    print('\tname\tmes')
    for event in d.events:
        print('\t{name: <8}{mes}'.format(name=event.name, mes=event.message))

    print(d.state.consumptions)
    print(d.state.productions)
    print(d.state.exchanges)
