#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import hashlib
import unittest

import plotly.graph_objects as go
from plotly.offline.offline import plot

from hadar.analyzer.result import ResultAnalyzer
from hadar.optimizer.input import Study, Production, Consumption
from hadar.optimizer.optimizer import LPOptimizer
from hadar.viewer.html import HTMLPlotting


class TestHTMLPlotting(unittest.TestCase):
    def setUp(self) -> None:
        self.study = Study(['a', 'b'], horizon=3) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[20, 10, 2], name='load')) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[30, 15, 3], name='car')) \
            .add_on_node('a', data=Production(cost=10, quantity=[60, 30, 5], name='prod')) \
        \
            .add_on_node('b', data=Consumption(cost=10 ** 6, quantity=[40, 20, 2], name='load')) \
            .add_on_node('b', data=Production(cost=20, quantity=[10, 5, 1], name='prod')) \
            .add_on_node('b', data=Production(cost=20, quantity=[20, 10, 2], name='nuclear')) \
            .add_link(src='a', dest='b', quantity=[10, 10, 10], cost=2)

        optimizer = LPOptimizer()
        self.result = optimizer.solve(study=self.study)

        self.agg = ResultAnalyzer(self.study, self.result)
        self.plot = HTMLPlotting(agg=self.agg, unit_symbol='MW', time_start='2020-02-01', time_end='2020-02-02',
                                 node_coord={'a': [2.33, 48.86], 'b': [4.38, 50.83]})

        self.hash = hashlib.sha3_256()

    def test_stack(self):
        fig = self.plot.stack(node='a', scn=0)
        self.assert_fig_hash('d9f9f004b98ca62be934d69d4fd0c1a302512242', fig)

    def test_map_exchanges(self):
        fig = self.plot.exchanges_map(t=0, scn=0)
        self.assert_fig_hash('9aa34f28665ea9e6766b271ffbc677d3cda6810b', fig)

    def assert_fig_hash(self, expected: str, fig: go.Figure):
        h = hashlib.sha1()
        h.update(TestHTMLPlotting.get_html(fig))
        self.assertEqual(expected, h.hexdigest())

    @staticmethod
    def get_html(fig: go.Figure) -> bytes:
        html = plot(fig, include_plotlyjs=False, include_mathjax=False, output_type='div')
        # plotly use a random id. We need to extract it and replace it by constant
        # uuid can be find at ... <div id="xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx" class="plotly-graph-div" ...
        uuid = html.split('" class="plotly-graph-div"')[0][-36:]
        return html.replace(uuid, '#####').encode('ascii')
