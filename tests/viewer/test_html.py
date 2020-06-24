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
        fig = self.plot.node('a').stack(scn=0)
        self.assert_fig_hash('d9f9f004b98ca62be934d69d4fd0c1a302512242', fig)

    def test_map_exchanges(self):
        fig = self.plot.network().map(t=0, scn=0, zoom=1.6)
        # Used this line to plot map: plot(fig)
        self.assert_fig_hash('49d81d1457b2ac78e1fc6ae4c1fc6215b8a0bbe4', fig)

    def test_plot_timeline(self):
        fig = self.plot.consumption(node='a', name='load').timeline()
        self.assert_fig_hash('ba776202b252c9df5c81ca869b2e2d85e56e5589', fig)

        fig = self.plot.production(node='b', name='nuclear').timeline()
        self.assert_fig_hash('33baf5d01fda12b6a2d025abf8421905fc24abe1', fig)

        fig = self.plot.link(src='a', dest='b').timeline()
        self.assert_fig_hash('0c87d1283db5250858b14e2240d30f9059459e65', fig)

    def test_plot_monotone(self):
        fig = self.plot.consumption(node='a', name='load').monotone(scn=0)
        self.assert_fig_hash('1ffa51a52b066aab8cabb817c11fd1272549eb9d', fig)

        fig = self.plot.production(node='b', name='nuclear').monotone(t=0)
        self.assert_fig_hash('e059878aac45330810578482df8c3d19261f7f75', fig)

        fig = self.plot.link(src='a', dest='b').monotone(scn=0)
        self.assert_fig_hash('1d5dba9e2189c741e5daa36d69ff1a879f169964', fig)

    def test_rac_heatmap(self):
        fig = self.plot.network().rac_matrix()
        self.assert_fig_hash('2b87a4e781e9eeb532f5d2b091c474bb0de625fd', fig)

    def test_gaussian(self):
        fig = self.plot.consumption(node='a', name='load').gaussian(scn=0)
        self.assert_fig_hash('4f3676a65cde6c268233679e1d0e6207df62764d', fig)

        fig = self.plot.production(node='b', name='nuclear').gaussian(t=0)
        # Fail devops self.assert_fig_hash('45ffe15df1d72829ebe2283c9c4b65ee8465c978', fig)

        fig = self.plot.link(src='a', dest='b').gaussian(scn=0)
        self.assert_fig_hash('52620565ce8ea670b18707cccf30594b5c3d58ea', fig)

    def assert_fig_hash(self, expected: str, fig: go.Figure):
        actual = hashlib.sha1(TestHTMLPlotting.get_html(fig)).hexdigest()
        if expected != actual:
            fig.show()
        self.assertEqual(expected, actual)

    @staticmethod
    def get_html(fig: go.Figure) -> bytes:
        html = plot(fig, include_plotlyjs=False, include_mathjax=False, output_type='div')
        # plotly use a random id. We need to extract it and replace it by constant
        # uuid can be find at ... <div id="xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx" class="plotly-graph-div" ...
        uuid = html.split('" class="plotly-graph-div"')[0][-36:]
        return html.replace(uuid, '#####').encode('ascii')
