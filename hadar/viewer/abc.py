#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
from typing import List, Tuple, Dict

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

from hadar.analyzer.result import ResultAnalyzer


class ABCElementPlotting(ABC):
    """
    Abstract interface to implement to plot graphics
    """
    @abstractmethod
    def timeline(self, df: pd.DataFrame, title: str):
        """
        Plot timeline with all scenarios.

        :param df: dataframe with scenario on columns and time on index
        :param title: title to plot
        :return:
        """
        pass

    @abstractmethod
    def monotone(self, y: np.ndarray, title: str):
        """
        Plot monotone.

        :param y: value vector
        :param title: title to plot
        :return:
        """
        pass

    @abstractmethod
    def gaussian(self, rac: np.ndarray, qt: np.ndarray, title: str):
        """
        Plot gaussian.

        :param rac: Remain Available Capacities matrix (to plot green or red point)
        :param qt: value vector
        :param title: title to plot
        :return:
        """
        pass

    @abstractmethod
    def stack(self, areas: List[Tuple[str, np.ndarray]], lines: List[Tuple[str, np.ndarray]], title: str):
        """
        Plot stack.

        :param areas: list of timelines to stack with area
        :param lines: list of timelines to stack with line
        :param title: title to plot
        :return:
        """
        pass

    @abstractmethod
    def matrix(self, data: np.ndarray, title):
        """
        Plot matrix (heatmap)

        :param data: 2D matrix to plot
        :param title: title to plot
        :return:
        """
        pass

    def map_exchange(self, nodes, lines, limit, title, zoom):
        """
        Plot map with exchanges as arrow.

        :param nodes: node to set on map
        :param lines: arrow to se on map
        :param limit: colorscale limit to use
        :param title: title to plot
        :param zoom: zoom to set on map
        :return:
        """
        pass


class FluentAPISelector(ABC):
    def __init__(self, plotting: ABCElementPlotting, agg: ResultAnalyzer):
        self.plotting = plotting
        self.agg = agg

    @staticmethod
    def not_both(t: int, scn: int):
        if t is not None and scn is not None:
            raise ValueError('you have to specify time or scenario index but not both')


class ConsumptionFluentAPISelector(FluentAPISelector):
    """
    Consumption level of fluent api.
    """
    def __init__(self, plotting: ABCElementPlotting, agg: ResultAnalyzer, name: str, node: str, kind: str):
        FluentAPISelector.__init__(self, plotting, agg)
        self.name = name
        self.node = node
        self.kind = kind

    def timeline(self):
        """
        Plot timeline graphics.
        :return:
        """
        cons = self.agg.network().node(self.node).consumption(self.name).scn().time()[self.kind]
        title = 'Consumptions %s for %s on node %s' % (self.kind, self.name, self.node)
        return self.plotting.timeline(cons, title)

    def monotone(self, t: int = None, scn: int = None):
        """
        Plot monotone graphics.

        :param t: focus on t index
        :param scn: focus on scn index if t not given
        :return:
        """
        FluentAPISelector.not_both(t, scn)

        if t is not None:
            y = self.agg.network().node(self.node).consumption(self.name).time(t).scn()[self.kind].values
            title = 'Monotone consumption of %s on node %s at t=%0d' % (self.name, self.node, t)
        elif scn is not None:
            y = self.agg.network().node(self.node).consumption(self.name).scn(scn).time()[self.kind].values
            title = 'Monotone consumption of %s on node %s at scn=%0d' % (self.name, self.node, scn)

        return self.plotting.monotone(y, title)

    def gaussian(self, t: int = None, scn: int = None):
        """
        Plot gaussian graphics

        :param t: focus on t index
        :param scn: focus on scn index if t not given
        :return:
        """
        FluentAPISelector.not_both(t, scn)

        if t is None:
            cons = self.agg.network().node(self.node).consumption(self.name).scn(scn).time()[self.kind].values
            rac = self.agg.get_rac()[scn, :]
            title = 'Gaussian consumption of %s on node %s at scn=%0d' % (self.name, self.node, scn)
        elif scn is None:
            cons = self.agg.network().node(self.node).consumption(self.name).time(t).scn()[self.kind].values
            rac = self.agg.get_rac()[:, t]
            title = 'Gaussian consumption of %s on node %s at t=%0d' % (self.name, self.node, t)

        return self.plotting.gaussian(rac=rac, qt=cons, title=title)


class ProductionFluentAPISelector(FluentAPISelector):
    """
    Production level of fluent api
    """
    def __init__(self, plotting: ABCElementPlotting, agg: ResultAnalyzer, name: str, node: str, kind: str):
        FluentAPISelector.__init__(self, plotting, agg)
        self.name = name
        self.node = node
        self.kind = kind

    def timeline(self):
        """
        Plot timeline graphics.
        :return:
        """
        prod = self.agg.network().node(self.node).production(self.name).scn().time()[self.kind]
        title = 'Production %s for %s on node %s' % (self.kind, self.name, self.node)
        return self.plotting.timeline(prod, title)

    def monotone(self, t: int = None, scn: int = None):
        """
        Plot monotone graphics.

        :param t: focus on t index
        :param scn: focus on scn index if t not given
        :return:
        """
        FluentAPISelector.not_both(t, scn)

        if t is not None:
            y = self.agg.network().node(self.node).production(self.name).time(t).scn()[self.kind].values
            title = 'Monotone production of %s on node %s at t=%0d' % (self.name, self.node, t)
        elif scn is not None:
            y = self.agg.network().node(self.node).production(self.name).scn(scn).time()[self.kind].values
            title = 'Monotone production of %s on node %s at scn=%0d' % (self.name, self.node, scn)

        return self.plotting.monotone(y, title)

    def gaussian(self, t: int = None, scn: int = None):
        """
        Plot gaussian graphics

        :param t: focus on t index
        :param scn: focus on scn index if t not given
        :return:
        """
        FluentAPISelector.not_both(t, scn)

        if t is None:
            prod = self.agg.network().node(self.node).production(self.name).scn(scn).time()[self.kind].values
            rac = self.agg.get_rac()[scn, :]
            title = 'Gaussian production of %s on node %s at scn=%0d' % (self.name, self.node, scn)
        elif scn is None:
            prod = self.agg.network().node(self.node).production(self.name).time(t).scn()[self.kind].values
            rac = self.agg.get_rac()[:, t]
            title = 'Gaussian production of %s on node %s at t=%0d' % (self.name, self.node, t)

        return self.plotting.gaussian(rac=rac, qt=prod, title=title)


class LinkFluentAPISelector(FluentAPISelector):
    """
    Link level of fluent api
    """
    def __init__(self, plotting: ABCElementPlotting, agg: ResultAnalyzer, src: str, dest: str, kind: str):
        FluentAPISelector.__init__(self, plotting, agg)
        self.src = src
        self.dest = dest
        self.kind = kind

    def timeline(self):
        """
        Plot timeline graphics.
        :return:
        """
        links = self.agg.network().node(self.src).link(self.dest).scn().time()[self.kind]
        title = 'Link %s from %s to %s' % (self.kind, self.src, self.dest)
        return self.plotting.timeline(links, title)

    def monotone(self, t: int = None, scn: int = None):
        """
        Plot monotone graphics.

        :param t: focus on t index
        :param scn: focus on scn index if t not given
        :return:
        """
        FluentAPISelector.not_both(t, scn)

        if t is not None:
            y = self.agg.network().node(self.src).link(self.dest).time(t).scn()[self.kind].values
            title = 'Monotone link from %s to %s at t=%0d' % (self.src, self.dest, t)
        elif scn is not None:
            y = self.agg.network().node(self.src).link(self.dest).scn(scn).time()[self.kind].values
            title = 'Monotone link from %s to %s at scn=%0d' % (self.src, self.dest, scn)

        return self.plotting.monotone(y, title)

    def gaussian(self, t: int = None, scn: int = None):
        """
        Plot gaussian graphics

        :param t: focus on t index
        :param scn: focus on scn index if t not given
        :return:
        """
        FluentAPISelector.not_both(t, scn)

        if t is None:
            prod = self.agg.network().node(self.src).link(self.dest).scn(scn).time()[self.kind].values
            rac = self.agg.get_rac()[scn, :]
            title = 'Gaussian link from %s to %s at t=%0d' % (self.src, self.dest, scn)
        elif scn is None:
            prod = self.agg.network().node(self.src).link(self.dest).time(t).scn()[self.kind].values
            rac = self.agg.get_rac()[:, t]
            title = 'Gaussian link from %s to %s at t=%0d' % (self.src, self.dest, t)

        return self.plotting.gaussian(rac=rac, qt=prod, title=title)


class NodeFluentAPISelector(FluentAPISelector):
    """
    Node level of fluent api
    """
    def __init__(self, plotting: ABCElementPlotting, agg: ResultAnalyzer, node: str):
        FluentAPISelector.__init__(self, plotting, agg)
        self.node = node

    def stack(self, scn: int = 0, prod_kind: str = 'used', cons_kind: str = 'asked'):
        """
        Plot with production stacked with area and consumptions stacked by dashed lines.

        :param node: select node to plot.
        :param scn: scenario index to plot.
        :param prod_kind: select which prod to stack : available ('avail') or 'used'
        :param cons_kind: select which cons to stack : 'asked' or 'given'
        :return: plotly figure or jupyter widget to plot
        """
        c, p, b = self.agg.get_elements_inside(node=self.node)

        areas = []
        # stack production with area
        if p > 0:
            prod = self.agg.network().scn(scn).node(self.node).production().time().sort_values('cost', ascending=False)
            for i, name in enumerate(prod.index.get_level_values('name').unique()):
                areas.append((name, prod.loc[name][prod_kind].sort_index().values))

        # add import in production stack
        balance = self.agg.get_balance(node=self.node)[scn]
        im = -np.clip(balance, None, 0)
        if not (im == 0).all():
            areas.append(('import', im))

        lines = []
        # Stack consumptions with line
        if c > 0:
            cons = self.agg.network().scn(scn).node(self.node).consumption().time().sort_values('cost', ascending=False)
            for i, name in enumerate(cons.index.get_level_values('name').unique()):
                lines.append((name, cons.loc[name][cons_kind].sort_index().values))

        # Add export in consumption stack
        exp = np.clip(balance, 0, None)
        if not (exp == 0).all():
            lines.append(('export', exp))

        title = 'Stack for node %s' % self.node

        return self.plotting.stack(areas, lines, title)

    def consumption(self, name: str, kind: str = 'given') -> ConsumptionFluentAPISelector:
        """
        Go to consumption level of fluent API

        :param name: select consumption name
        :param kind: kind of data 'asked' or 'given'
        :return:
        """
        return ConsumptionFluentAPISelector(plotting=self.plotting, agg=self.agg, node=self.node, name=name, kind=kind)

    def production(self, name: str, kind: str = 'used') -> ProductionFluentAPISelector:
        """
         Go to production level of fluent API

         :param name: select production name
         :param kind: kind of data available ('avail') or 'used'
         :return:
         """
        return ProductionFluentAPISelector(plotting=self.plotting, agg=self.agg, node=self.node, name=name, kind=kind)

    def link(self, dest: str, kind: str = 'used'):
        """
         got to link level of fluent API

         :param dest: select destination node name
         :param kind: kind of data available ('avail') or 'used'
         :return:
         """
        return LinkFluentAPISelector(plotting=self.plotting, agg=self.agg, src=self.node, dest=dest, kind=kind)


class NetworkFluentAPISelector(FluentAPISelector):
    """
    Network level of fluent API
    """

    def rac_matrix(self):
        """
        plot RAC matrix graphics

        :return:
        """
        rac = self.agg.get_rac()
        pct = (rac >= 0).sum() / rac.size * 100
        title = "RAC Matrix %0d %% passed" % pct

        return self.plotting.matrix(data=rac, title=title)

    def map(self, t: int, zoom: int, scn: int = 0, limit: int = None):
        """
        Plot map exchange graphics

        :param t: t index to focus
        :param zoom: zoom to set
        :param scn: scn index to focus
        :param limit: color scale limite to use
        :return:
        """
        nodes = {node: self.agg.get_balance(node=node)[scn, t] for node in self.agg.nodes}

        if limit is None:
            limit = max(max(nodes.values()), -min(nodes.values()))

        lines = {}
        # Compute lines
        links = self.agg.network().scn(scn).time(t).node().link()
        for src in links.index.get_level_values('node').unique():
            for dest in links.loc[src].index.get_level_values('dest').unique():
                exchange = links.loc[src, dest]['used']  # forward
                exchange -= links.loc[dest, src]['used'] if (dest, src) in links.index else 0  # backward

                if exchange >= 0:
                    lines[(src, dest)] = exchange
                else:
                    lines[(dest, src)] = -exchange

        title = 'Exchange map at t=%0d scn=%0d' % (t, scn)
        return self.plotting.map_exchange(nodes, lines, limit, title, zoom)

    def node(self, node: str):
        """
        Go to node level fo fluent API
        :param node: node name
        :return: NodeFluentAPISelector
        """
        return NodeFluentAPISelector(plotting=self.plotting, agg=self.agg, node=node)


class ABCPlotting(ABC):
    """
    Abstract method to plot optimizer result.
    """

    def __init__(self, agg: ResultAnalyzer,
                 unit_symbol: str = '',
                 time_start=None, time_end=None,
                 node_coord: Dict[str, List[float]] = None):
        """
        Create instance.

        :param agg: ResultAggragator instence to use
        :param unit_symbol: symbol on quantity unit used. ex. MW, litter, Go, ...
        :param time_start: time to use as the start of study horizon
        :param time_end: time to use as the end of study horizon
        :param node_coord: nodes coordinates to use for map plotting
        :param map_element_size: size on element draw on map. default as 1.
        """
        self.plotting = None
        self.agg = agg
        self.unit = '(%s)' % unit_symbol if unit_symbol != '' else ''
        self.coord = node_coord

        # Create time_index
        time = [time_start is None, time_end is None]
        if time == [True, False] or time == [False, True]:
            raise ValueError('You have to give both time_start and time_end')
        elif time == [False, False]:
            self.time_index = pd.date_range(start=time_start, end=time_end, periods=self.agg.horizon)
        else:
            self.time_index = np.arange(self.agg.horizon)

    def network(self):
        """
        Entry point to use fluent API.

        :return: NetworkFluentAPISelector
        """
        return NetworkFluentAPISelector(plotting=self.plotting, agg=self.agg)
