#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import unittest
import numpy as np
from hadar.optimizer.input import Study, Consumption, Production, Link


class TestStudy(unittest.TestCase):
    def test_create_study(self):
        c = Consumption(name='load', cost=20, quantity=10)
        p = Production(name='nuclear', cost=20, quantity=10)
        l = Link(dest='a', cost=20, quantity=10)

        study = Study(['a', 'b'], horizon=1) \
            .add_on_node(node='a', data=c) \
            .add_on_node(node='a', data=p) \
            .add_link(src='b', dest='a', cost=20, quantity=10)

        self.assertEqual(c, study.nodes['a'].consumptions[0])
        self.assertEqual(p, study.nodes['a'].productions[0])
        self.assertEqual(l, study.nodes['b'].links[0])
        self.assertEqual(1, study.horizon)

    def test_wrong_node_list(self):
        def test():
            study = Study(node_names=['fr', 'be', 'de', 'be'], horizon=1)

        self.assertRaises(ValueError, test)

    def test_wrong_production_cost(self):
        def test():
            study = Study(node_names=['fr'], horizon=1) \
                .add_on_node(node='fr', data=Production(name='solar', cost=-1, quantity=10))

        self.assertRaises(ValueError, test)

    def test_wrong_production_quantity(self):
        def test():
            study = Study(node_names=['fr'], horizon=1) \
                .add_on_node(node='fr', data=Production(name='solar', cost=10, quantity=-1))

        self.assertRaises(ValueError, test)

    def test_wrong_production_name(self):
        def test():
            study = Study(node_names=['fr'], horizon=1) \
                .add_on_node(node='fr', data=Production(name='solar', cost=10, quantity=10)) \
                .add_on_node(node='fr', data=Production(name='solar', cost=10, quantity=10))

        self.assertRaises(ValueError, test)

    def test_wrong_consumption_cost(self):
        def test():
            study = Study(node_names=['fr'], horizon=1) \
                .add_on_node(node='fr', data=Consumption(name='load', cost=-10, quantity=10))

        self.assertRaises(ValueError, test)

    def test_wrong_consumption_quantity(self):
        def test():
            study = Study(node_names=['fr'], horizon=1) \
                .add_on_node(node='fr', data=Consumption(name='load', cost=10, quantity=-10))

        self.assertRaises(ValueError, test)

    def test_wrong_consumption_name(self):
        def test():
            study = Study(node_names=['fr'], horizon=1) \
                .add_on_node(node='fr', data=Consumption(name='load', cost=10, quantity=10)) \
                .add_on_node(node='fr', data=Consumption(name='load', cost=10, quantity=10))

        self.assertRaises(ValueError, test)

    def test_wrong_link_cost(self):
        def test():
            study = Study(node_names=['fr', 'be'], horizon=1) \
                .add_link(src='fr', dest='be', cost=-10, quantity=10)

        self.assertRaises(ValueError, test)

    def test_wrong_link_quantity(self):
        def test():
            study = Study(node_names=['fr', 'be'], horizon=1) \
                .add_link(src='fr', dest='be', cost=10, quantity=-10)

        self.assertRaises(ValueError, test)

    def test_wrong_link_dest_not_node(self):
        def test():
            study = Study(node_names=['fr', 'be'], horizon=1) \
                .add_link(src='fr', dest='it', cost=10, quantity=10)

        self.assertRaises(ValueError, test)

    def test_wrong_link_dest_not_unique(self):
        def test():
            study = Study(node_names=['fr', 'be'], horizon=1) \
                .add_link(src='fr', dest='be', cost=10, quantity=10) \
                .add_link(src='fr', dest='be', cost=10, quantity=10)

        self.assertRaises(ValueError, test)

    def test_validate_quantity_perfect_size(self):
        # Input
        study = Study(node_names=['a'], horizon=10, nb_scn=2)
        i = np.ones((2, 10))

        # Test
        r = study._validate_quantity(i)
        np.testing.assert_array_equal(i, r)

    def test_validate_quantity_expend_scn(self):
        # Input
        study = Study(node_names=[], horizon=5, nb_scn=2)
        i = [1, 2, 3, 4, 5]

        # Expect
        exp = np.array([[1, 2, 3, 4, 5],
                        [1, 2, 3, 4, 5]])

        # Test
        res = study._validate_quantity(i)
        np.testing.assert_array_equal(exp, res)

    def test_validate_quantity_expend_horizon(self):
        # Input
        study = Study(node_names=[], horizon=2, nb_scn=5)
        i = [[1], [2], [3], [4], [5]]

        # Expect
        exp = np.array([[1, 1],
                        [2, 2],
                        [3, 3],
                        [4, 4],
                        [5, 5]])

        # Test
        res = study._validate_quantity(i)
        np.testing.assert_array_equal(exp, res)

    def test_validate_quantity_expend_both(self):
        # Input
        study = Study(node_names=[], horizon=2, nb_scn=3)
        i = 1

        # Expect
        exp = np.ones((3, 2))

        # Test
        res = study._validate_quantity(i)
        np.testing.assert_array_equal(exp, res)

    def test_validate_quantity_wrong_size(self):
        # Input
        study = Study(node_names=[], horizon=2)
        self.assertRaises(ValueError, lambda: study._validate_quantity([4, 5, 1]))

    def test_validate_quantity_negative(self):
        # Input
        study = Study(node_names=[], horizon=3)
        self.assertRaises(ValueError, lambda: study._validate_quantity([4, -5, 1]))