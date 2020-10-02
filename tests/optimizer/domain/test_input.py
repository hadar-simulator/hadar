#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import json
import unittest

from hadar.optimizer.domain.input import (
    Study,
    Consumption,
    Production,
    Link,
    Storage,
    Converter,
)
from hadar.optimizer.domain.numeric import NumericalValueFactory


class TestStudy(unittest.TestCase):
    def setUp(self) -> None:
        self.study = (
            Study(horizon=1)
            .network()
            .node("a")
            .consumption(name="load", cost=20, quantity=10)
            .production(name="nuclear", cost=20, quantity=10)
            .to_converter(name="converter", ratio=1)
            .node("b")
            .link(src="b", dest="a", cost=20, quantity=10)
            .network("gas")
            .node("b")
            .production(name="nuclear", cost=20, quantity=10)
            .storage(
                name="store",
                capacity=100,
                flow_in=10,
                flow_out=10,
                cost=1,
                init_capacity=4,
                eff=0.1,
            )
            .node("a")
            .consumption(name="load", cost=20, quantity=10)
            .link(src="b", dest="a", cost=20, quantity=10)
            .converter(name="converter", to_network="gas", to_node="b", cost=10, max=10)
            .build()
        )

        self.factory = NumericalValueFactory(
            horizon=self.study.horizon, nb_scn=self.study.nb_scn
        )

    def test_create_study(self):
        c = Consumption(
            name="load", cost=self.factory.create(20), quantity=self.factory.create(10)
        )
        p = Production(
            name="nuclear",
            cost=self.factory.create(20),
            quantity=self.factory.create(10),
        )
        s = Storage(
            name="store",
            capacity=self.factory.create(100),
            flow_in=self.factory.create(10),
            flow_out=self.factory.create(10),
            cost=self.factory.create(1),
            init_capacity=4,
            eff=self.factory.create(0.1),
        )
        l = Link(
            dest="a", cost=self.factory.create(20), quantity=self.factory.create(10)
        )
        v = Converter(
            name="converter",
            src_ratios={("default", "a"): self.factory.create(1)},
            dest_network="gas",
            dest_node="b",
            cost=self.factory.create(10),
            max=self.factory.create(10),
        )

        self.assertEqual(c, self.study.networks["default"].nodes["a"].consumptions[0])
        self.assertEqual(p, self.study.networks["default"].nodes["a"].productions[0])
        self.assertEqual(l, self.study.networks["default"].nodes["b"].links[0])

        self.assertEqual(c, self.study.networks["gas"].nodes["a"].consumptions[0])
        self.assertEqual(p, self.study.networks["gas"].nodes["b"].productions[0])
        self.assertEqual(s, self.study.networks["gas"].nodes["b"].storages[0])
        self.assertEqual(l, self.study.networks["gas"].nodes["b"].links[0])

        self.assertEqual(v, self.study.converters["converter"])

        self.assertEqual(1, self.study.horizon)

    def test_wrong_production_quantity(self):
        def test():
            study = (
                Study(horizon=1)
                .network()
                .node("fr")
                .production(name="solar", cost=1, quantity=-10)
                .build()
            )

        self.assertRaises(ValueError, test)

    def test_wrong_production_name(self):
        def test():
            study = (
                Study(horizon=1)
                .network()
                .node("fr")
                .production(name="solar", cost=1, quantity=-10)
                .production(name="solar", cost=1, quantity=-10)
                .build()
            )

        self.assertRaises(ValueError, test)

    def test_wrong_consumption_quantity(self):
        def test():
            study = (
                Study(horizon=1)
                .network()
                .node("fr")
                .consumption(name="load", cost=1, quantity=-10)
                .build()
            )

        self.assertRaises(ValueError, test)

    def test_wrong_consumption_name(self):
        def test():
            study = (
                Study(horizon=1)
                .network()
                .node("fr")
                .consumption(name="load", cost=1, quantity=-10)
                .consumption(name="load", cost=1, quantity=-10)
                .build()
            )

    def test_wrong_storage_flow(self):
        def test_in():
            study = (
                Study(horizon=1)
                .network()
                .node("fr")
                .storage(name="store", capacity=1, flow_in=-1, flow_out=1)
                .build()
            )

        def test_out():
            study = (
                Study(horizon=1)
                .network()
                .node("fr")
                .storage(name="store", capacity=1, flow_in=1, flow_out=-1)
                .build()
            )

        self.assertRaises(ValueError, test_in)
        self.assertRaises(ValueError, test_out)

    def test_wrong_storage_capacity(self):
        def test_capacity():
            study = (
                Study(horizon=1)
                .network()
                .node("fr")
                .storage(name="store", capacity=-1, flow_in=1, flow_out=1)
                .build()
            )

        def test_init_capacity():
            study = (
                Study(horizon=1)
                .network()
                .node("fr")
                .storage(
                    name="store", capacity=1, flow_in=1, flow_out=1, init_capacity=-1
                )
                .build()
            )

        self.assertRaises(ValueError, test_capacity)
        self.assertRaises(ValueError, test_init_capacity)

    def test_wrong_storage_eff(self):
        def test():
            study = (
                Study(horizon=1)
                .network()
                .node("fr")
                .storage(name="store", capacity=1, flow_in=1, flow_out=1, eff=-1)
                .build()
            )

        self.assertRaises(ValueError, test)

    def test_wrong_link_quantity(self):
        def test():
            study = (
                Study(horizon=1)
                .network()
                .node("fr")
                .node("be")
                .link(src="fr", dest="be", cost=10, quantity=-10)
                .build()
            )

        self.assertRaises(ValueError, test)

    def test_wrong_link_dest_not_node(self):
        def test():
            study = (
                Study(horizon=1)
                .network()
                .node("fr")
                .node("be")
                .link(src="fr", dest="it", cost=10, quantity=10)
                .build()
            )

        self.assertRaises(ValueError, test)

    def test_wrong_link_dest_not_unique(self):
        def test():
            study = (
                Study(horizon=1)
                .network()
                .node("fr")
                .node("be")
                .link(src="fr", dest="be", cost=10, quantity=10)
                .link(src="fr", dest="be", cost=10, quantity=10)
                .build()
            )

        self.assertRaises(ValueError, test)

    def test_wrong_converter_dest(self):
        def test_network():
            study = (
                Study(horizon=1)
                .network("elec")
                .node("a")
                .converter(name="conv", to_network="gas", to_node="a", max=1)
                .build()
            )

        def test_node():
            study = (
                Study(horizon=1)
                .network("gas")
                .node("a")
                .converter(name="conv", to_network="gas", to_node="b", max=1)
                .build()
            )

        self.assertRaises(ValueError, test_network)
        self.assertRaises(ValueError, test_node)

    def test_wrong_converter_src(self):
        def test():
            study = (
                Study(horizon=1)
                .network()
                .node("a")
                .to_converter(name="conv", ratio=1)
                .to_converter(name="conv", ratio=2)
                .converter(name="conv", to_node="", to_network="", max=1)
                .build()
            )

        self.assertRaises(ValueError, test)

    def test_serialization(self):
        d = self.study.to_json()
        j = json.dumps(d)
        s = json.loads(j)
        s = Study.from_json(s)
        self.assertEqual(self.study, s)
