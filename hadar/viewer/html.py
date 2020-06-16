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

from hadar.analyzer.result import ResultAnalyzer, NodeIndex, SrcIndex, TimeIndex, DestIndex, NameIndex
from hadar.viewer.abc import ABCPlotting, ConsumptionElement, ABCElementPlotting, ProductionElement, LinkElement, \
    NodeElement

__all__ = ['HTMLPlotting']


class HTMLElementPlotting(ABCElementPlotting):
    def __init__(self, unit: str, time_index):
        self.unit = unit
        self.time_index = time_index

        self.cmap_cons = ['brown', 'blue', 'darkgoldenrod', 'darkmagenta', 'darkorange', 'cadetblue', 'forestgreen',
                          'indigo', 'olive', 'darkred']

    def timeline(self, df: pd.DataFrame, title: str):
        scenarios = df.index.get_level_values('scn').unique()
        alpha = max(10, 255 / scenarios.size)
        color = 'rgba(100, 100, 100, %d)' % alpha

        fig = go.Figure()
        for scn in scenarios:
            fig.add_trace(go.Scatter(x=self.time_index, y=df.loc[scn], mode='lines', hoverinfo='name',
                                     name='scn %0d' % scn, line=dict(color=color)))

        fig.update_layout(title_text=title,
                          yaxis_title="Quantity %s" % self.unit, xaxis_title="time", showlegend=False)

        return fig

    def monotone(self, y: np.ndarray, title: str):
        y.sort()
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
        fig.add_trace(go.Scatter(x=green, y=_gaussian(red, m, o), hovertemplate='%{x:.2f} ' + self.unit,
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


class HTMLPlotting(ABCPlotting):
    """
    Plotting implementation interactive html graphics. (Use plotly)
    """

    def __init__(self, agg: ResultAnalyzer, unit_symbol: str = '',
                 time_start=None, time_end=None,
                 cmap=coolwarm,
                 node_coord: Dict[str, List[float]] = None,
                 map_element_size: int = 1):
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

        self.agg = agg
        self.unit = '(%s)' % unit_symbol if unit_symbol != '' else ''
        self.coord = node_coord
        self.size = map_element_size

        # Create time_index
        time = [time_start is None, time_end is None]
        if time == [True, False] or time == [False, True]:
            raise ValueError('You have to give both time_start and time_end')
        elif time == [False, False]:
            self.time_index = pd.date_range(start=time_start, end=time_end, periods=self.agg.horizon)
        else:
            self.time_index = np.arange(self.agg.horizon)

        # Create colors scale
        self.cmap = cmap
        self.cmap_plotly = HTMLPlotting.matplotlib_to_plotly(cmap, 255)

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

    def node(self, node: str):
        return NodeElement(plotting=HTMLElementPlotting(unit=self.unit, time_index=self.time_index), agg=self.agg, node=node)

    def _plot_links(self, fig: go.Figure, start: str, end: str, color: str, qt: float):
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
        fig.add_trace(go.Scattergeo(lat=[S[1], E[1]], hoverinfo='skip',
                                    lon=[S[0], E[0]], mode='lines',
                                    line=dict(width=4 * self.size, color=color)))
        # vector flow direction
        v = E - S
        n = np.linalg.norm(v)
        # Get orthogonal vector
        w = np.array([v[1], -v[0]])
        # Compute triangle points
        A = E - v * 0.5
        B = A - v / n * self.size * 0.5 - w / n * self.size * 0.25
        C = A - v / n * self.size * 0.5 + w / n * self.size * 0.25

        # plot arrow
        fig.add_trace(go.Scattergeo(lat=[B[1], A[1], C[1]], hoverinfo='text',
                                    lon=[B[0], A[0], C[0]], text=str(qt), mode='lines',
                                    line=dict(width=4 * self.size, color=color)))

    def exchanges_map(self, t: int, scn: int = 0, limit: int = None):
        """
        Plot a map with node (color are balance) and arrow between nodes (color for quantity).

        :param t: timestep to plot
        :param scn: scenario index to plot
        :param limit: limite to use as min/max for color scale. If not provided we use min/max from dataset.
        :return: plotly figure or jupyter widget to plot
        """
        if self.coord is None:
            raise ValueError('Please provide node coordinate by setting param node_coord in Plotting constructor')

        balances = [self.agg.get_balance(node=node)[scn, t] for node in self.agg.nodes]
        if limit is None:
            limit = max(max(balances), -min(balances))

        fig = go.Figure()

        # plot links
        links = self.agg.agg_link(self.agg.iscn[scn], self.agg.isrc, self.agg.idest, self.agg.itime)
        for src in links.index.get_level_values('src').unique():
            for dest in links.loc[src].index.get_level_values('dest').unique():
                exchange = links.loc[src, dest, t]['used']  # forward
                exchange -= links.loc[dest, src, t]['used'] if (dest, src, t) in links.index else 0  # backward

                color = 'rgb' + str(self.cmap(abs(exchange) / 2 / limit + 0.5)[:-1])
                if exchange > 0:
                    self._plot_links(fig=fig, start=src, end=dest, color=color, qt=exchange)
                else:
                    self._plot_links(fig=fig, start=dest, end=src, color=color, qt=-exchange)

        # plot nodes
        text = ['%s: %i' % (n, b) for n, b in zip(self.agg.nodes, balances)]
        lon = [self.coord[node][0] for node in self.agg.nodes]
        lat = [self.coord[node][1] for node in self.agg.nodes]

        fig.add_trace(go.Scattergeo(lon=lon, lat=lat, hoverinfo='text', text=text, mode='markers',
                                    marker=dict(size=15 * self.size,
                                                colorscale=self.cmap_plotly, cmin=-limit, color=balances,
                                                cmax=limit, colorbar_title="Net Position %s" % self.unit)))
        # Config plot
        fig.update_layout(title_text='Exchanges Map', showlegend=False, height=600,
                          geo=dict(projection_type='equirectangular', showland=True, showcountries=True,
                                   resolution=50, landcolor='rgb(200, 200, 200)', countrycolor='rgb(0, 0, 0)',
                                   fitbounds='locations'))

        return fig

    def consumption(self, node: str, name: str, kind: str = 'given') -> ConsumptionElement:
        """
        Plot all timelines consumption scenario.

        :param node: selected node name
        :param name: select consumption name
        :param kind: kind of data 'asked' or 'given'
        :return:
        """
        return ConsumptionElement(plotting=HTMLElementPlotting(self.unit, self.time_index), agg=self.agg,
                                  node=node, name=name, kind=kind)

    def production(self, node: str, name: str, kind: str = 'used') -> ProductionElement:
        """
         Plot all timelines production scenario.

         :param node: selected node name
         :param name: select production name
         :param kind: kind of data available ('avail') or 'used'
         :return:
         """
        return ProductionElement(plotting=HTMLElementPlotting(self.unit, self.time_index), agg=self.agg,
                                 node=node, name=name, kind=kind)

    def links(self, src: str, dest: str, kind: str = 'used'):
        """
         Plot all timelines links scenario.

         :param src: selected source node name
         :param dest: select destination node name
         :param kind: kind of data available ('avail') or 'used'
         :return:
         """
        return LinkElement(plotting=HTMLElementPlotting(self.unit, self.time_index), agg=self.agg,
                           src=src, dest=dest, kind=kind)

    def rac_heatmap(self):
        rac = self.agg.get_rac()
        pct = (rac >= 0).sum() / rac.size * 100

        fig = go.Figure(data=go.Heatmap(
            z=rac,
            x=self.time_index,
            y=np.arange(self.agg.nb_scn),
            colorscale='RdBu', zmid=0))

        fig.update_layout(title_text="RAC Matrix %0d %% passed" % pct,
                          yaxis_title="scenarios", xaxis_title="time", showlegend=False)

        return fig
