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
        self.study = Study(horizon=3, nb_scn=2)\
            .network()\
                .node('a')\
                    .consumption(cost=10 ** 6, quantity=[[20, 10, 2], [10, 5, 3]], name='load')\
                    .consumption(cost=10 ** 6, quantity=[[30, 15, 3], [15, 7, 2]], name='car')\
                    .production(cost=10, quantity=[[60, 30, 5], [30, 15, 3]], name='prod')\
                .node('b')\
                    .consumption(cost=10 ** 6, quantity=[[40, 20, 2], [20, 10, 1]], name='load')\
                    .production(cost=20, quantity=[[10, 5, 1], [5, 3, 1]], name='prod')\
                    .production(cost=30, quantity=[[20, 10, 2], [10, 5, 1]], name='nuclear')\
                .link(src='a', dest='b', quantity=[[10, 10, 10], [5, 5, 5]], cost=2)\
            .build()

        optimizer = LPOptimizer()
        self.result = optimizer.solve(study=self.study)

        self.agg = ResultAnalyzer(self.study, self.result)
        self.plot = HTMLPlotting(agg=self.agg, unit_symbol='MW', time_start='2020-02-01', time_end='2020-02-02',
                                 node_coord={'a': [2.33, 48.86], 'b': [4.38, 50.83]})

        self.hash = hashlib.sha3_256()

    def test_network(self):
        fig = self.plot.network().map(t=0, scn=0, zoom=1.6)
        # Used this line to plot map: plot(fig)
        self.assert_fig_hash('49d81d1457b2ac78e1fc6ae4c1fc6215b8a0bbe4', fig)

        fig = self.plot.network().rac_matrix()
        self.assert_fig_hash('2b87a4e781e9eeb532f5d2b091c474bb0de625fd', fig)

    def test_node(self):
        fig = self.plot.network().node('a').stack(scn=0)
        self.assert_fig_hash('d9f9f004b98ca62be934d69d4fd0c1a302512242', fig)

    def test_consumption(self):
        fig = self.plot.network().node('a').consumption('load').timeline()
        self.assert_fig_hash('ba776202b252c9df5c81ca869b2e2d85e56e5589', fig)

        fig = self.plot.network().node('a').consumption('load').monotone(scn=0)
        self.assert_fig_hash('1ffa51a52b066aab8cabb817c11fd1272549eb9d', fig)

        fig = self.plot.network().node('a').consumption('load').gaussian(scn=0)
        self.assert_fig_hash('4f3676a65cde6c268233679e1d0e6207df62764d', fig)

    def test_production(self):
        fig = self.plot.network().node('b').production('nuclear').timeline()
        self.assert_fig_hash('33baf5d01fda12b6a2d025abf8421905fc24abe1', fig)

        fig = self.plot.network().node('b').production('nuclear').monotone(t=0)
        self.assert_fig_hash('e059878aac45330810578482df8c3d19261f7f75', fig)

        fig = self.plot.network().node('b').production('nuclear').gaussian(t=0)
        # Fail devops self.assert_fig_hash('45ffe15df1d72829ebe2283c9c4b65ee8465c978', fig)

    def test_link(self):
        fig = self.plot.network().node('a').link('b').timeline()
        self.assert_fig_hash('97f413ea2fa9908abebf381ec588a7e60b906884', fig)

        fig = self.plot.network().node('a').link('b').monotone(scn=0)
        self.assert_fig_hash('08b0e0d8414bee2c5083a298af00fe86d0eba6b0', fig)

        fig = self.plot.network().node('a').link('b').gaussian(scn=0)
        self.assert_fig_hash('5151ade23440beeea9ff144245f81b057c0fa2cd', fig)

    def test_storage(self):
        study = Study(horizon=4)\
            .network()\
                .node('a')\
                    .production(name='nuclear', cost=20, quantity=[10, 10, 10, 0]) \
                .node('b')\
                    .consumption(name='load', cost=10 ** 6, quantity=[20, 10, 0, 10]) \
                    .storage(name='cell', capacity=30, flow_in=10, flow_out=10, init_capacity=15, eff=.5) \
            .link(src='a', dest='b', cost=1, quantity=10)\
            .build()

        optimizer = LPOptimizer()
        res = optimizer.solve(study)
        plot = HTMLPlotting(agg=ResultAnalyzer(study, res), unit_symbol='MW', time_start='2020-02-01', time_end='2020-02-02')

        fig = plot.network().node('b').stack()
        self.assert_fig_hash('94760e8b7d07704cfe4132a918b4075f5f594d69', fig)

        fig = plot.network().node('b').storage('cell').candles(scn=0)
        self.assert_fig_hash('594ae603876c2d1bc91899e89d6de50bf37071ee', fig)

        fig = plot.network().node('b').storage('cell').monotone(scn=0)
        self.assert_fig_hash('f020d7954b2fa2245001a4b34530d65ddbd87382', fig)

    def test_converter(self):
        study = Study(horizon=2)\
            .network('elec')\
                .node('a')\
                    .consumption(name='load', cost=10**6, quantity=[10, 30])\
            .network('gas')\
                .node('b')\
                    .production(name='central', cost=10, quantity=50)\
                    .to_converter(name='conv', ratio=0.8)\
            .network('coat')\
                .node('c')\
                    .production(name='central', cost=10, quantity=60)\
                    .to_converter(name='conv', ratio=0.5)\
            .converter(name='conv', to_network='elec', to_node='a', max=50)\
            .build()

        optim = LPOptimizer()
        res = optim.solve(study)
        plot = HTMLPlotting(agg=ResultAnalyzer(study, res), unit_symbol='MW', time_start='2020-02-01',
                            time_end='2020-02-02')

        fig = plot.network('elec').node('a').stack()
        self.assert_fig_hash('0969b8b1bde6695a4c8cc78fdc5a42928f7af956', fig)

        fig = plot.network('gas').node('b').stack()
        self.assert_fig_hash('d9a5c9f13c932048f1bcb22ec849a7a4e79b577b', fig)

        fig = plot.network('elec').node('a').from_converter('conv').timeline()
        self.assert_fig_hash('5a42ce7a62c12c092631f0a9b63f807ada94ed79', fig)

        fig = plot.network('gas').node('b').to_converter('conv').timeline()
        self.assert_fig_hash('77de14a806dff91a118d395b3e0d998335d64cd7', fig)

        fig = plot.network('gas').node('b').to_converter('conv').monotone(scn=0)
        self.assert_fig_hash('3f6ac9f5e1c8ca611d39b7c62f527e4bfd5a573a', fig)

        fig = plot.network('elec').node('a').from_converter('conv').gaussian(scn=0)
        self.assert_fig_hash('32a6e175600822c833a9b7f3008aa35230b0b646', fig)

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
