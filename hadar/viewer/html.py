#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from matplotlib.cm import coolwarm

from hadar.analyzer.result import ResultAnalyzer
from hadar.viewer.abc import ABCPlotting, ABCElementPlotting

__all__ = ['HTMLPlotting']


class HTMLElementPlotting(ABCElementPlotting):
    def __init__(self, unit: str, time_index, node_coord: Dict[str, List[float]] = None):
        self.unit = unit
        self.time_index = time_index
        self.coord = node_coord

        self.cmap = coolwarm
        self.cmap_plotly = HTMLElementPlotting.matplotlib_to_plotly(self.cmap, 255)

        self.cmap_cons = ['brown', 'blue', 'darkgoldenrod', 'darkmagenta', 'darkorange', 'cadetblue', 'forestgreen',
                          'indigo', 'olive', 'darkred']

    @classmethod
    def matplotlib_to_plotly(cls, cmap, res: int):
        """
        Convert matplotlib color scale to plotly color scale.

        :param cmap: matplotlib color scale function
        :param res: resolution to use
        :return: list of string use by plotly
        """
        h = 1.0 / (res - 1)
        pl_colorscale = []
        for k in range(res):
            C = (np.array(cmap(k * h)[:3]) * 255).astype(np.uint8)
            pl_colorscale.append([k * h, 'rgb' + str((C[0], C[1], C[2]))])
        return pl_colorscale

    def timeline(self, df: pd.DataFrame, title: str):
        scenarios = df.index.get_level_values('scn').unique()
        alpha = max(0.01, 1 / scenarios.size)
        color = 'rgba(0, 0, 0, %.2f)' % alpha

        fig = go.Figure()
        for scn in scenarios:
            fig.add_trace(go.Scatter(x=self.time_index, y=df.loc[scn], mode='lines', hoverinfo='name',
                                     name='scn %0d' % scn, line=dict(color=color)))

        fig.update_layout(title_text=title,
                          yaxis_title="Quantity %s" % self.unit, xaxis_title="time", showlegend=False)

        return fig

    def monotone(self, y: np.ndarray, title: str):
        y.sort()
        y = y[::-1]
        x = np.linspace(0, 100, y.size)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=y, mode='markers'))
        fig.update_layout(title_text=title,
                          yaxis_title="Quantity %s" % self.unit, xaxis_title="%", showlegend=False)

        return fig

    def gaussian(self, rac: np.ndarray, qt: np.ndarray, title: str):
        #    1                    /  x - m \ 2
        # --------- * exp -0.5 * | -------- |
        # o * √2*Pi               \    o   /
        def _gaussian(x, m, o):
            return np.exp(-0.5 * np.power((x - m) / o, 2)) / o / 1.772454

        x = np.linspace(np.min(qt) * 0, np.max(qt) * 1.2, 100)
        m = np.mean(qt)
        o = np.std(qt)

        green = qt[rac >= 0]
        red = qt[rac < 0]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=_gaussian(x, m, o), mode='lines', hoverinfo='none', line=dict(color='grey')))
        fig.add_trace(go.Scatter(x=green, y=_gaussian(green, m, o), hovertemplate='%{x:.2f} ' + self.unit,
                                 name='passed', mode='markers', marker=dict(color='green', size=10)))
        fig.add_trace(go.Scatter(x=red, y=_gaussian(red, m, o), hovertemplate='%{x:.2f} ' + self.unit,
                                 name='failed', mode='markers', marker=dict(color='red', size=10)))
        fig.update_layout(title_text=title, yaxis=dict(visible=False),
                          yaxis_title='', xaxis_title="Quantity %s" % self.unit, showlegend=False)

        return fig

    def stack(self, areas: List[Tuple[str, np.ndarray]], lines: List[Tuple[str, np.ndarray]], title: str):
        fig = go.Figure()

        # Stack areas
        stack = np.zeros_like(self.time_index, dtype=float)
        for i, (name, data) in enumerate(areas):
            stack += data
            fig.add_trace(go.Scatter(x=self.time_index, y=stack.copy(), name=name, mode='none',
                                     fill='tozeroy' if i == 0 else 'tonexty'))

        # Stack lines.
        # Bottom line have to be top frontward. So we firstly stack lines then plot in reverse set.
        stack = np.zeros_like(self.time_index, dtype=float)
        stacked_lines = []
        for i, (name, data) in enumerate(lines):
            stack += data
            stacked_lines.append((name, stack.copy()))

        for i, (name, data) in enumerate(stacked_lines[::-1]):
            fig.add_trace(go.Scatter(x=self.time_index, y=data, line_color=self.cmap_cons[i % 10],
                                     name=name, line=dict(width=2)))

        fig.update_layout(title_text=title, yaxis_title="Quantity %s" % self.unit, xaxis_title="time")
        return fig

    def matrix(self, data: np.ndarray, title):
        def sdt(x):
            x[x > 0] /= np.max(x[x > 0])
            x[x < 0] /= -np.min(x[x < 0])
            return x

        fig = go.Figure(data=go.Heatmap(
            z=sdt(data.copy()),
            x=self.time_index,
            y=np.arange(data.shape[0]),
            hoverinfo='text',
            text=data,
            colorscale='RdBu', zmid=0,
            showscale=False))

        fig.update_layout(title_text=title, yaxis_title="scenarios", xaxis_title="time", showlegend=False)

        return fig

    def map_exchange(self, nodes, lines, limit, title, size):
        if self.coord is None:
            raise ValueError('Please provide node coordinate by setting param node_coord in Plotting constructor')

        fig = go.Figure()
        # Add node circle
        keys = nodes.keys()
        node_qt = [nodes[k] for k in keys]
        node_coords = np.array([self.coord[n] for n in keys])
        center = np.mean(node_coords, axis=0)

        # Plot arrows
        for (src, dest), qt in lines.items():
            color = 'rgb' + str(self.cmap(abs(qt) / 2 / limit + 0.5)[:-1])
            self._plot_links(fig, src, dest, color, qt, size)

        # Plot nodes
        fig.add_trace(go.Scattermapbox(
            mode="markers",
            lon=node_coords[:, 0],
            lat=node_coords[:, 1],
            hoverinfo='text', text=node_qt,
            marker=dict(size=20, colorscale=self.cmap_plotly, cmin=-limit, color=node_qt,
                        cmax=limit, colorbar_title="Net Position %s" % self.unit)))

        fig.update_layout(showlegend=False,
                          title_text=title,
                          mapbox=dict(
                              style="carto-positron",
                              center={'lon': center[0], 'lat': center[1]},
                              zoom=1 / size / 0.07))
        return fig

    def _plot_links(self, fig: go.Figure, start: str, end: str, color: str, qt: float, size: float):
        """
        Plot line with arrow to a figure.

        :param fig: figure to use
        :param start: start node
        :param end: end node
        :param color: color to use
        :param qt: quantity to set inside label
        :return:
        """
        S = np.array([self.coord[start][0], self.coord[start][1]])
        E = np.array([self.coord[end][0], self.coord[end][1]])

        # plot line
        fig.add_trace(go.Scattermapbox(lat=[S[1], E[1]], hoverinfo='skip',
                                       lon=[S[0], E[0]], mode='lines',
                                       line=dict(width=2 * size, color=color)))
        # vector flow direction
        v = E - S
        n = np.linalg.norm(v)
        # Get orthogonal vector
        w = np.array([v[1], -v[0]])
        # Compute triangle points
        A = E - v * 0.1
        B = A - v / 10 - w / 10
        C = A - v / 10 + w / 10

        # plot arrow
        fig.add_trace(go.Scattermapbox(lat=[B[1], A[1], C[1], B[1], None], hoverinfo='text', fill='toself',
                                       lon=[B[0], A[0], C[0], B[0], None], text=str(qt), mode='lines',
                                       line=dict(width=2 * size, color=color)))


class HTMLPlotting(ABCPlotting):
    """
    Plotting implementation interactive html graphics. (Use plotly)
    """

    def __init__(self, agg: ResultAnalyzer, unit_symbol: str = '',
                 time_start=None, time_end=None,
                 node_coord: Dict[str, List[float]] = None):
        """
        Create instance.

        :param agg: ResultAggragator instence to use
        :param unit_symbol: symbol on quantity unit used. ex. MW, litter, Go, ...
        :param time_start: time to use as the start of study horizon
        :param time_end: time to use as the end of study horizon
        :param cmap: matplotlib color map to use (coolwarm as default)
        :param node_coord: nodes coordinates to use for map plotting
        :param map_element_size: size on element draw on map. default as 1.
        """
        ABCPlotting.__init__(self, agg, unit_symbol, time_start, time_end, node_coord)
        self.plotting = HTMLElementPlotting(self.unit, self.time_index, self.coord)


