#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

from hadar.analyzer.result import ResultAnalyzer


class ElementPlotting(ABC):
    @abstractmethod
    def timeline(self, df: pd.DataFrame, title: str):
        pass

    @abstractmethod
    def monotone(self, y: np.ndarray, title: str):
        pass

    @abstractmethod
    def gaussian(self, rac: np.ndarray, qt: np.ndarray, title: str):
        pass


class Element(ABC):
    def __init__(self, plotting: ElementPlotting, agg: ResultAnalyzer):
        self.plotting = plotting
        self.agg = agg

    @abstractmethod
    def timeline(self):
        pass

    @abstractmethod
    def monotone(self, t: int = None, scn: int = None):
        if t is not None and scn is not None:
            raise ValueError('you have to specify time or scenario index but not both')

    @abstractmethod
    def gaussian(self, t: int = None, scn: int = None):
        if t is not None and scn is not None:
            raise ValueError('you have to specify time or scenario index but not both')


class ConsumptionElement(Element):
    def __init__(self, plotting: ElementPlotting, agg: ResultAnalyzer, name: str, node: str, kind: str):
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
        if t is not None and scn is not None:
            raise ValueError('you have to specify time or scenario index but not both')

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
    def __init__(self, plotting: ElementPlotting, agg: ResultAnalyzer, name: str, node: str, kind: str):
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
        Element.monotone(self, t, scn)

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
    def __init__(self, plotting: ElementPlotting, agg: ResultAnalyzer, src: str, dest: str, kind: str):
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
        Element.monotone(self, t, scn)

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
        pass


class ABCPlotting(ABC):
    """
    Abstract method to plot optimizer result.
    """

    @abstractmethod
    def stack(self, node: str):
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
    def links(self, src: str, dest: str, kind: str = 'used') -> LinkElement:
        pass

    @abstractmethod
    def rac_heatmap(self):
        pass
