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
        self.study = Study(['a', 'b'], horizon=3, nb_scn=2) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[[20, 10, 2], [10, 5, 3]], name='load')) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[[30, 15, 3], [15, 7, 2]], name='car')) \
            .add_on_node('a', data=Production(cost=10, quantity=[[60, 30, 5], [30, 15, 3]], name='prod')) \
        \
            .add_on_node('b', data=Consumption(cost=10 ** 6, quantity=[[40, 20, 2], [20, 10, 1]], name='load')) \
            .add_on_node('b', data=Production(cost=20, quantity=[[10, 5, 1], [5, 3, 1]], name='prod')) \
            .add_on_node('b', data=Production(cost=30, quantity=[[20, 10, 2], [10, 5, 1]], name='nuclear')) \
            .add_link(src='a', dest='b', quantity=[[10, 10, 10], [5, 5, 5]], cost=2)

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

    def test_plot_timeline(self):
        fig = self.plot.consumptions(node='a', name='load')
        self.assert_fig_hash('7787e0487f8f4012dc8b8f0cf979ffbb09fffb63', fig)

        fig = self.plot.productions(node='b', name='nuclear')
        self.assert_fig_hash('44e414ef08a43add5ef68b5c533b47145fab0ba2', fig)

        fig = self.plot.links(src='a', dest='b')
        self.assert_fig_hash('6375e591679d12907f440a8c23eb850a037d9cd8', fig)

    def test_plot_monotone(self):
        fig = self.plot.monotone_consumption(node='a', name='load', scn=0)
        self.assert_fig_hash('753619bf85b387f3b0f304688bb578efe39db3e9', fig)

        fig = self.plot.monotone_production(node='b', name='nuclear', t=0)
        self.assert_fig_hash('0a99228bf1a0743b604e9082b0ba7db86f3993f3', fig)

        fig = self.plot.monotone_link(src='a', dest='b', scn=0)
        self.assert_fig_hash('2e2410dad5800c9658846c40421dbe83c9e5f3f9', fig)

    def test_rac_heatmap(self):
        fig = self.plot.rac_heatmap()
        self.assert_fig_hash('1fa715af27e4ab85b033cff41f5edff72f4bca88', fig)

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
