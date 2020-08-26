#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import json
import unittest

from hadar.optimizer.output import *


class TestResult(unittest.TestCase):
    def test_json(self):
        result = Result(networks={'default': OutputNetwork(nodes={'a': OutputNode(
                            consumptions=[OutputConsumption(name='load', cost=[[1]], quantity=[[1]])],
                            productions=[OutputProduction(name='prod', cost=[[1]], quantity=[[1]])],
                            links=[OutputLink(dest='b', cost=[[1]], quantity=[[1]])],
                            storages=[OutputStorage(name='cell', capacity=[[1]], flow_in=[[1]], flow_out=[[1]])])})},
                        converters={'cell': OutputConverter(name='conv', flow_src={('elec', 'b'): [[1]]}, flow_dest=[[1]])})

        string = json.dumps(result.to_json())
        r = Result.from_json(json.loads(string))
        self.assertEqual(result, r)