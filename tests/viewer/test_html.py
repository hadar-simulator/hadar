import unittest
import hashlib
import pandas as pd
import numpy as np

import plotly.graph_objects as go
from plotly.offline.offline import plot

from hadar.solver.input import *
from hadar.solver.output import *
from hadar.solver.study import solve
from hadar.aggregator.result import *
from hadar.viewer.html import HTMLPlotting


class TestHTMLPlotting(unittest.TestCase):
    def setUp(self) -> None:
        self.study = Study(['a', 'b']) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[20, 2], type='load')) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[30, 3], type='car')) \
            .add_on_node('a', data=Production(cost=10, quantity=[60, 3], type='prod')) \
            .add_on_node('b', data=Consumption(cost=10 ** 6, quantity=[40, 2], type='load')) \
            .add_on_node('b', data=Production(cost=20, quantity=[10, 1], type='prod')) \
            .add_on_node('b', data=Production(cost=20, quantity=[20, 2], type='nuclear')) \
            .add_border(src='a', dest='b', quantity=[10, 1], cost=2)

        self.result = solve(study=self.study)

        self.agg = ResultAggregator(self.study, self.result)
        self.plot = HTMLPlotting(agg=self.agg, unit_symbol='MW', time_start='2020-02-01', time_end='2020-02-02',
                                 node_coord={'a': [2.33, 48.86], 'b': [4.38, 50.83]})

        self.hash = hashlib.sha3_256()

    def test_stack(self):
        fig = self.plot.stack('a')
        self.assert_fig('6ef4b03c8b7e95b00e483fbc58e084486b293d06', fig)

    def test_map_exchanges(self):
        fig = self.plot.exchanges_map(0)
        self.assert_fig('9aa34f28665ea9e6766b271ffbc677d3cda6810b', fig)

    def assert_fig(self, expected: str, fig: go.Figure):
        h = hashlib.sha1()
        h.update(TestHTMLPlotting.get_html(fig).encode('ascii'))
        self.assertEqual(expected, h.hexdigest())

    @staticmethod
    def get_html(fig: go.Figure):
        html = plot(fig, include_plotlyjs=False, include_mathjax=False, output_type='div')
        # plotly use a random id. We need to extract it and replace it by constant
        # uuid can be find at ... <div id="xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx" class="plotly-graph-div" ...
        uuid = html.split('" class="plotly-graph-div"')[0][-36:]
        return html.replace(uuid, '#####')