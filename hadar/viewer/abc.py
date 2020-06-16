#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
from typing import List, Tuple

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

from hadar.analyzer.result import ResultAnalyzer


class ABCElementPlotting(ABC):
    @abstractmethod
    def timeline(self, df: pd.DataFrame, title: str):
        pass

    @abstractmethod
    def monotone(self, y: np.ndarray, title: str):
        pass

    @abstractmethod
    def gaussian(self, rac: np.ndarray, qt: np.ndarray, title: str):
        pass

    @abstractmethod
    def stack(self, areas: List[Tuple[str, np.ndarray]], lines: List[Tuple[str, np.ndarray]], title: str):
        pass

    @abstractmethod
    def matrix(self, data: np.ndarray, title):
        pass


class Element(ABC):
    def __init__(self, plotting: ABCElementPlotting, agg: ResultAnalyzer):
        self.plotting = plotting
        self.agg = agg

    @staticmethod
    def not_both(t: int, scn: int):
        if t is not None and scn is not None:
            raise ValueError('you have to specify time or scenario index but not both')


class ConsumptionElement(Element):
    def __init__(self, plotting: ABCElementPlotting, agg: ResultAnalyzer, name: str, node: str, kind: str):
        Element.__init__(self, plotting, agg)
        self.name = name
        self.node = node
        self.kind = kind

    def timeline(self):
        cons = self.agg.agg_cons(self.agg.inode[self.node], self.agg.iname[self.name],
                                 self.agg.iscn, self.agg.itime)[self.kind]
        title = 'Consumptions %s for %s on node %s' % (self.kind, self.name, self.node)
        return self.plotting.timeline(cons, title)

    def monotone(self, t: int = None, scn: int = None):
        Element.not_both(t, scn)

        if t is not None:
            y = self.agg.agg_cons(self.agg.inode[self.node], self.agg.iname[self.name],
                                  self.agg.itime[t], self.agg.iscn)[self.kind].values
            title = 'Monotone consumption of %s on node %s at t=%0d' % (self.name, self.node, t)
        elif scn is not None:
            y = self.agg.agg_cons(self.agg.inode[self.node], self.agg.iname[self.name],
                                  self.agg.iscn[scn], self.agg.itime)[self.kind].values
            title = 'Monotone consumption of %s on node %s at t=%0d' % (self.name, self.node, scn)

        return self.plotting.monotone(y, title)

    def gaussian(self, t: int = None, scn: int = None):
        Element.not_both(t, scn)

        if t is None:
            cons = self.agg.agg_cons(self.agg.inode[self.node], self.agg.iname[self.name],
                                     self.agg.iscn[scn], self.agg.itime)[self.kind].values
            rac = self.agg.get_rac()[scn, :]
            title = 'Gaussian consumption of %s on node %s at scn=%0d' % (self.name, self.node, scn)
        elif scn is None:
            cons = self.agg.agg_cons(self.agg.inode[self.node], self.agg.iname[self.name],
                                     self.agg.itime[t], self.agg.iscn)[self.kind].values
            rac = self.agg.get_rac()[:, t]
            title = 'Gaussian consumption of %s on node %s at t=%0d' % (self.name, self.node, t)

        return self.plotting.gaussian(rac=rac, qt=cons, title=title)


class ProductionElement(Element):
    def __init__(self, plotting: ABCElementPlotting, agg: ResultAnalyzer, name: str, node: str, kind: str):
        Element.__init__(self, plotting, agg)
        self.name = name
        self.node = node
        self.kind = kind

    def timeline(self):
        prod = self.agg.agg_prod(self.agg.inode[self.node], self.agg.iname[self.name],
                                 self.agg.iscn, self.agg.itime)[self.kind]
        title = 'Production %s for %s on node %s' % (self.kind, self.name, self.node)
        return self.plotting.timeline(prod, title)

    def monotone(self, t: int = None, scn: int = None):
        Element.not_both(t, scn)

        if t is not None:
            y = self.agg.agg_prod(self.agg.inode[self.node], self.agg.iname[self.name],
                                  self.agg.itime[t], self.agg.iscn)[self.kind].values
            title = 'Monotone production of %s on node %s at t=%0d' % (self.name, self.node, t)
        elif scn is not None:
            y = self.agg.agg_prod(self.agg.inode[self.node], self.agg.iname[self.name],
                                  self.agg.iscn[scn], self.agg.itime)[self.kind].values
            title = 'Monotone production of %s on node %s at t=%0d' % (self.name, self.node, scn)

        return self.plotting.monotone(y, title)

    def gaussian(self, t: int = None, scn: int = None):
        Element.not_both(t, scn)

        if t is None:
            prod = self.agg.agg_prod(self.agg.inode[self.node], self.agg.iname[self.name],
                                     self.agg.iscn[scn], self.agg.itime)[self.kind].values
            rac = self.agg.get_rac()[scn, :]
            title = 'Gaussian production of %s on node %s at scn=%0d' % (self.name, self.node, scn)
        elif scn is None:
            prod = self.agg.agg_prod(self.agg.inode[self.node], self.agg.iname[self.name],
                                     self.agg.itime[t], self.agg.iscn)[self.kind].values
            rac = self.agg.get_rac()[:, t]
            title = 'Gaussian production of %s on node %s at t=%0d' % (self.name, self.node, t)

        return self.plotting.gaussian(rac=rac, qt=prod, title=title)


class LinkElement(Element):
    def __init__(self, plotting: ABCElementPlotting, agg: ResultAnalyzer, src: str, dest: str, kind: str):
        Element.__init__(self, plotting, agg)
        self.src = src
        self.dest = dest
        self.kind = kind

    def timeline(self):
        links = self.agg.agg_link(self.agg.isrc[self.src], self.agg.idest[self.dest], self.agg.iscn,
                                  self.agg.itime)[self.kind]
        title = 'Link %s from %s to %s' % (self.kind, self.src, self.dest)
        return self.plotting.timeline(links, title)

    def monotone(self, t: int = None, scn: int = None):
        Element.not_both(t, scn)

        if t is not None:
            y = self.agg.agg_link(self.agg.isrc[self.src], self.agg.idest[self.dest],
                                  self.agg.itime[t], self.agg.iscn)[self.kind].values
            title = 'Monotone link from %s to %s at t=%0d' % (self.src, self.dest, t)
        elif scn is not None:
            y = self.agg.agg_link(self.agg.isrc[self.src], self.agg.idest[self.dest],
                                  self.agg.iscn[scn], self.agg.itime)[self.kind].values
            title = 'Monotone link from %s to %s at t=%0d' % (self.src, self.dest, scn)

        return self.plotting.monotone(y, title)

    def gaussian(self, t: int = None, scn: int = None):
        Element.not_both(t, scn)

        if t is None:
            prod = self.agg.agg_link(self.agg.isrc[self.src], self.agg.idest[self.dest],
                                     self.agg.iscn[scn], self.agg.itime)[self.kind].values
            rac = self.agg.get_rac()[scn, :]
            title = 'Gaussian link from %s to %s at t=%0d' % (self.src, self.dest, scn)
        elif scn is None:
            prod = self.agg.agg_prod(self.agg.isrc[self.src], self.agg.idest[self.dest],
                                     self.agg.itime[t], self.agg.iscn)[self.kind].values
            rac = self.agg.get_rac()[:, t]
            title = 'Gaussian link from %s to %s at t=%0d' % (self.src, self.dest, t)

        return self.plotting.gaussian(rac=rac, qt=prod, title=title)


class NodeElement(Element):
    def __init__(self, plotting: ABCElementPlotting, agg: ResultAnalyzer, node: str):
        Element.__init__(self, plotting, agg)
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
            prod = self.agg.agg_prod(self.agg.iscn[scn], self.agg.inode[self.node], self.agg.iname, self.agg.itime) \
                .sort_values('cost', ascending=True)
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
            cons = self.agg.agg_cons(self.agg.iscn[scn], self.agg.inode[self.node], self.agg.iname, self.agg.itime) \
                .sort_values('cost', ascending=False)
            for i, name in enumerate(cons.index.get_level_values('name').unique()):
                lines.append((name, cons.loc[name][cons_kind].sort_index().values))

        # Add export in consumption stack
        exp = np.clip(balance, 0, None)
        if not (exp == 0).all():
            lines.append(('export', exp))

        title = 'Stack for node %s' % self.node

        return self.plotting.stack(areas, lines, title)


class NetworkElement(Element):
    def rac_matrix(self):
        rac = self.agg.get_rac()
        pct = (rac >= 0).sum() / rac.size * 100
        title = "RAC Matrix %0d %% passed" % pct

        return self.plotting.matrix(data=rac, title=title)

class ABCPlotting(ABC):
    """
    Abstract method to plot optimizer result.
    """

    @abstractmethod
    def node(self, node: str) -> NodeElement:
        pass

    @abstractmethod
    def exchanges_map(self, t: int, limit: int):
        pass

    @abstractmethod
    def consumption(self, node: str, name: str, kind: str = 'given') -> ConsumptionElement:
        pass

    @abstractmethod
    def production(self, node: str, name: str, kind: str = 'used') -> ProductionElement:
        pass

    @abstractmethod
    def link(self, src: str, dest: str, kind: str = 'used') -> LinkElement:
        pass

    @abstractmethod
    def network(self):
        pass
