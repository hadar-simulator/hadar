#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from matplotlib.cm import coolwarm

from hadar.analyzer.result import ResultAnalyzer, NodeIndex, SrcIndex, TimeIndex, DestIndex, NameIndex
from hadar.viewer.abc import ABCPlotting


__all__ = ['HTMLPlotting']

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

    def stack(self, node: str, scn: int = 0, prod_kind: str = 'used', cons_kind: str = 'asked'):
        """
        Plot with production stacked with area and consumptions stacked by dashed lines.

        :param node: select node to plot.
        :param scn: scenario index to plot.
        :param prod_kind: select which prod to stack : available ('avail') or 'used'
        :param cons_kind: select which cons to stacl : 'asked' or 'given'
        :return: plotly figure or jupyter widget to plot
        """
        fig = go.Figure()
        c, p, b = self.agg.get_elements_inside(node=node)
        stack = np.zeros(self.agg.horizon)

        # stack production with area
        if p > 0:
            prod = self.agg.agg_prod(self.agg.iscn[scn], self.agg.inode[node], self.agg.iname, self.agg.itime)\
                .sort_values('cost', ascending=True)
            for i, name in enumerate(prod.index.get_level_values('name').unique()):
                stack += prod.loc[name][prod_kind].sort_index().values
                fig.add_trace(go.Scatter(x=self.time_index, y=stack.copy(), name=name, mode='none',
                                         fill='tozeroy' if i == 0 else 'tonexty'))

        # add import in production stack
        balance = self.agg.get_balance(node=node)[scn]
        im = -np.clip(balance, None, 0)
        if not (im == 0).all():
            stack += im
            fig.add_trace(go.Scatter(x=self.time_index, y=stack.copy(), name='import', mode='none', fill='tonexty'))

        # Reset stack
        stack = np.zeros_like(stack)
        cons_lines = []
        # Stack consumptions with line
        if c > 0:
            cons = self.agg.agg_cons(self.agg.iscn[scn], self.agg.inode[node], self.agg.iname, self.agg.itime)\
                .sort_values('cost', ascending=False)
            for i, name in enumerate(cons.index.get_level_values('name').unique()):
                stack += cons.loc[name][cons_kind].sort_index().values
                cons_lines.append([name, stack.copy()])

        # Add export in consumption stack
        exp = np.clip(balance, 0, None)
        if not (exp == 0).all():
            stack += exp
            cons_lines.append(['export', stack.copy()])

        # Plot line in the reverse sens to avoid misunderstood during graphics analyze
        for i, (name, stack) in enumerate(cons_lines[::-1]):
            fig.add_trace(go.Scatter(x=self.time_index, y=stack.copy(), line_color=self.cmap_cons[i % 10],
                                     name= name, line=dict(width=2)))

        fig.update_layout(title_text='Stack for node %s' % node,
                          yaxis_title="Quantity %s" % self.unit, xaxis_title="time")
        return fig

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