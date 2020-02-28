from typing import Dict, List

import plotly.graph_objects as go
import matplotlib

from hadar.aggregator.result import *
from hadar.viewer.abc import ABCPlotting


class HTMLPlotting(ABCPlotting):
    def __init__(self, agg, unit_quantity: str = '',
                 time_start=None, time_end=None,
                 cmap=matplotlib.cm.coolwarm,
                 node_coord: Dict[str, List[float]] = None,
                 map_element_size: int = 1):

        self.agg = agg
        self.unit = '(%s)' % unit_quantity if unit_quantity != '' else ''
        self.coord = node_coord
        self.size = map_element_size

        # Create time_index
        time = [time_start is None, time_end is None]
        if time == [True, False] or time == [False, True]:
            raise ValueError('You have to give both time_start and time_end')
        elif time == [False, False]:
            self.time_index = pd.date_range(start=time_start, end=time_end, periods=self.agg.study.horizon)
        else:
            self.time_index = np.arange(self.agg.study.horizon)

        # Create colors scale
        self.cmap = cmap
        self.cmap_plotly = HTMLPlotting.matplotlib_to_plotly(cmap, 255)

    @classmethod
    def matplotlib_to_plotly(cls, cmap, res: int):
        h = 1.0 / (res - 1)
        pl_colorscale = []
        for k in range(res):
            C = (np.array(cmap(k * h)[:3]) * 255).astype(np.uint8)
            pl_colorscale.append([k * h, 'rgb' + str((C[0], C[1], C[2]))])
        return pl_colorscale

    def stack(self, node: str):
        fig = go.Figure()
        stack = np.zeros(self.agg.study.horizon)

        # stack production with area
        prod = self.agg.agg_prod(NodeIndex(node), TypeIndex(), TimeIndex()).sort_values('cost', ascending=True)
        for i, type in enumerate(prod.index.get_level_values('type').unique()):
            stack += prod.loc[type]['used'].values
            fig.add_trace(go.Scatter(x=self.time_index, y=stack, name=type, mode='markers',
                                     fill='tozeroy' if i == 0 else 'tonexty'))

        # add import in production stack
        balance = self.agg.get_balance(node=node)
        im = -np.clip(balance, None, 0)
        if not (im == 0).all():
            stack += im
            fig.add_trace(go.Scatter(x=self.time_index, y=stack, name='import', mode='markers', fill='tonexty'))

        # Reset stack
        stack = np.zeros_like(stack)
        # Stack consumptions with line
        cons = self.agg.agg_cons(NodeIndex(node), TypeIndex(), TimeIndex()).sort_values('cost', ascending=False)
        for i, type in enumerate(cons.index.get_level_values('type').unique()):
            stack += cons.loc[type]['given'].values
            fig.add_trace(go.Scatter(x=self.time_index, y=stack, name=type, line=dict(width=4, dash='dash')))

        # Add export in consumption stack
        exp = np.clip(balance, 0, None)
        if not (exp == 0).all():
            stack += exp
            fig.add_trace(go.Scatter(x=self.time_index, y=stack, name='export', line=dict(width=4, dash='dash')))

        fig.update_layout(title_text='Stack error for node %s' % node,
                          yaxis_title="Quantity %s" % self.unit, xaxis_title="time")
        return fig

    def plot_links(self, fig, start, end, color: str, qt: float) -> go.Figure:
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
        A = E - v * 0.4
        B = A - v / n * self.size * 0.5 - w / n * self.size * 0.25
        C = A - v / n * self.size * 0.5 + w / n * self.size * 0.25

        # plot arrow
        fig.add_trace(go.Scattergeo(lat=[B[1], A[1], C[1]], hoverinfo='text',
                                    lon=[B[0], A[0], C[0]], text=str(qt), mode='lines',
                                    line=dict(width=4 * self.size, color=color)))

    def exchanges_map(self, t: int, limit: int = None) -> go.Figure:
        if self.coord is None:
            raise ValueError('Please provide node coordinate by setting param node_coord in Plotting constructor')

        nodes = self.agg.result.nodes.keys()
        balances = [self.agg.get_balance(node=node)[t] for node in nodes]
        if limit is None:
            limit = max(max(balances), -min(balances))

        fig = go.Figure()

        # print links
        borders = self.agg.agg_border(SrcIndex(), DestIndex(), TimeIndex())
        for src in borders.index.get_level_values('src').unique():
            for dest in borders.loc[src].index.get_level_values('dest').unique():
                exchange = borders.loc[src, dest, t]['used']  # forward
                exchange -= borders.loc[dest, src, t]['used'] if (dest, src, t) in borders.index else 0  # backward

                color = 'rgb' + str(self.cmap(abs(exchange) / 2 / limit + 0.5)[:-1])
                if exchange > 0:
                    self.plot_links(fig=fig, start=src, end=dest, color=color, qt=exchange)
                else:
                    self.plot_links(fig=fig, start=dest, end=src, color=color, qt=-exchange)

        # print nodes
        text = ['%s: %i' % (n, b) for n, b in zip(nodes, balances)]
        lon = [self.coord[node][0] for node in nodes]
        lat = [self.coord[node][1] for node in nodes]

        fig.add_trace(go.Scattergeo(lon=lon, lat=lat, hoverinfo='text', text=text, mode='markers',
                                    marker=dict(size=15 * self.size,
                                                colorscale=self.cmap_plotly, cmin=-limit, color=balances,
                                                cmax=limit, colorbar_title="Net Position")))
        # Config plot
        fig.update_layout(title_text='mercator', showlegend=False, height=600,
                          geo=dict(projection_type='equirectangular', showland=True,
                                   landcolor='rgb(150, 150, 150)', countrycolor='rgb(0, 0, 0)'))

        return fig