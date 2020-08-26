#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
from functools import reduce
from typing import TypeVar, List, Generic, Type

import numpy as np
import pandas as pd

from hadar.optimizer.input import Study
from hadar.optimizer.output import Result

__all__ = ['ResultAnalyzer', 'NetworkFluentAPISelector']

T = TypeVar('T')


class Index(Generic[T]):
    """
    Generic Index to use to select and rank data.
    """

    def __init__(self, column, index=None):
        """
        Initiate instance.

        :param column: column name link to this index
        :param index: list of index or element to filter from data. None by default to say keep all data.
        """
        self.column = column
        if index is None:
            self.all = True
        elif isinstance(index, list):
            self.index = tuple(index)
            self.all = len(index) == 0
        elif not isinstance(index, tuple):
            self.index = tuple([index])
            self.all = False
        else:
            self.index = index
            self.all = False

    def filter(self, df: pd.DataFrame) -> pd.Series:
        """
        Filter dataframe. Filter columns with columns attributes with index values.

        :param df: dataframe to filter
        :return: Series of boolean to set row to keep
        """
        if self.all:
            return df[self.column].notnull()
        return df[self.column].isin(self.index)

    def is_alone(self) -> bool:
        """
        Ask if index filter element is alone.

        :return: if index filter only one value return True else False
        """
        return not self.all and len(self.index) <= 1


class ProdIndex(Index[str]):
    """Index implementation to filter productions"""

    def __init__(self, index):
        Index.__init__(self, column='name', index=index)


class ConsIndex(Index[str]):
    """ Index implementation to filter consumptions"""

    def __init__(self, index):
        Index.__init__(self, column='name', index=index)


class StorIndex(Index[str]):
    """ Index implementation to filter storage"""

    def __init__(self, index):
        Index.__init__(self, column='name', index=index)


class LinkIndex(Index[str]):
    """Index implementation to filter destination node"""

    def __init__(self, index):
        Index.__init__(self, column='dest', index=index)


class SrcConverter(Index[str]):
    """Index implementation to filter source converter"""

    def __init__(self, index):
        Index.__init__(self, column='name', index=index)


class DestConverter(Index[str]):
    """Index implementation to filter destination converter"""

    def __init__(self, index):
        Index.__init__(self, column='name', index=index)


class NodeIndex(Index[str]):
    """Index implementation to filter node"""

    def __init__(self, index):
        Index.__init__(self, column='node', index=index)


class NetworkIndex(Index[str]):
    """Index implementation fo filter network"""

    def __init__(self, index):
        Index.__init__(self, column='network', index=index)


class IntIndex(Index[int]):
    """Index implementation to handle int index with slice"""

    def __init__(self, column: str, index):
        """
        Create instance.

        :param index: one element or list on element to filter.
        :param start: start datetime to filter (to use instead of index)
        :param end: end datetime to filter (to use instead of index)
        """
        if isinstance(index, slice):
            start = 0 if index.start is None else index.start
            stop = -1 if index.start is None else index.stop
            step = 1 if index.step is None else index.step
            index = tuple(range(start, stop, step))
        Index.__init__(self, column=column, index=index)


class TimeIndex(IntIndex):
    """Index implementation to filter by time step"""

    def __init__(self, index):
        IntIndex.__init__(self, column='t', index=index)


class ScnIndex(IntIndex):
    """index implementation to filter by scenario"""

    def __init__(self, index):
        IntIndex.__init__(self, column='scn', index=index)


class ResultAnalyzer:
    """
    Single object to encapsulate all postprocessing aggregation.
    """

    def __init__(self, study: Study, result: Result):
        """
        Create an instance.

        :param study: study to use
        :param result: result of study used
        """
        self.result = result
        self.study = study

        self.consumption = ResultAnalyzer._build_consumption(self.study, self.result)
        self.production = ResultAnalyzer._build_production(self.study, self.result)
        self.storage = ResultAnalyzer._build_storage(self.study, self.result)
        self.link = ResultAnalyzer._build_link(self.study, self.result)
        self.src_converter = ResultAnalyzer._build_src_converter(self.study, self.result)
        self.dest_converter = ResultAnalyzer._build_dest_converter(self.study, self.result)

    @staticmethod
    def _build_consumption(study: Study, result: Result):
        """
        Flat all data to build global consumption dataframe
        columns: | cost | name | node | network | asked | given | t | scn |
        """

        h = study.horizon
        scn = study.nb_scn
        elements = sum([sum([len(n.consumptions) for n in net.nodes.values()]) for net in study.networks.values()])
        size = scn * h * elements
        cons = {'cost': np.empty(size, dtype=float), 'asked': np.empty(size, dtype=float),
                'given': np.empty(size, dtype=float),
                'name': np.empty(size, dtype=str), 'node': np.empty(size, dtype=str),
                'network': np.empty(size, dtype=str),
                't': np.empty(size, dtype=float), 'scn': np.empty(size, dtype=float)}
        cons = pd.DataFrame(data=cons)

        n_cons = 0
        for n, net in result.networks.items():
            for node in net.nodes.keys():
                for i, c in enumerate(net.nodes[node].consumptions):
                    slices = cons.index[n_cons * h * scn: (n_cons + 1) * h * scn]
                    cons.loc[slices, 'cost'] = c.cost.flatten()
                    cons.loc[slices, 'name'] = c.name
                    cons.loc[slices, 'node'] = node
                    cons.loc[slices, 'network'] = n
                    cons.loc[slices, 'asked'] = study.networks[n].nodes[node].consumptions[i].quantity.flatten()
                    cons.loc[slices, 'given'] = c.quantity.flatten()
                    cons.loc[slices, 't'] = np.tile(np.arange(h), scn)
                    cons.loc[slices, 'scn'] = np.repeat(np.arange(scn), h)

                    n_cons += 1

        return cons

    @staticmethod
    def _build_production(study: Study, result: Result):
        """
        Flat all data to build global production dataframe
        columns: | cost | avail | used | network | name | node | t |
        """
        h = study.horizon
        scn = study.nb_scn
        elements = sum([sum([len(n.productions) for n in net.nodes.values()]) for net in study.networks.values()])
        size = scn * h * elements
        prod = {'cost': np.empty(size, dtype=float), 'avail': np.empty(size, dtype=float),
                'used': np.empty(size, dtype=float),
                'name': np.empty(size, dtype=str), 'node': np.empty(size, dtype=str),
                'network': np.empty(size, dtype=str),
                't': np.empty(size, dtype=float), 'scn': np.empty(size, dtype=float)}
        prod = pd.DataFrame(data=prod)

        n_prod = 0
        for n, net in result.networks.items():
            for node in net.nodes.keys():
                for i, c in enumerate(net.nodes[node].productions):
                    slices = prod.index[n_prod * h * scn: (n_prod + 1) * h * scn]
                    prod.loc[slices, 'cost'] = c.cost.flatten()
                    prod.loc[slices, 'name'] = c.name
                    prod.loc[slices, 'node'] = node
                    prod.loc[slices, 'network'] = n
                    prod.loc[slices, 'avail'] = study.networks[n].nodes[node].productions[i].quantity.flatten()
                    prod.loc[slices, 'used'] = c.quantity.flatten()
                    prod.loc[slices, 't'] = np.tile(np.arange(h), scn)
                    prod.loc[slices, 'scn'] = np.repeat(np.arange(scn), h)

                    n_prod += 1

        return prod

    @staticmethod
    def _build_storage(study: Study, result: Result):
        """
        Flat all data to build global storage dataframe
        :param study:
        :param result:
        :return:
        """
        h = study.horizon
        scn = study.nb_scn
        elements = sum([sum([len(n.storages) for n in net.nodes.values()]) for net in study.networks.values()])
        size = h * scn * elements

        stor = {'max_capacity': np.empty(size, dtype=float), 'capacity': np.empty(size, dtype=float),
                'max_flow_in': np.empty(size, dtype=float), 'flow_in': np.empty(size, dtype=float),
                'max_flow_out': np.empty(size, dtype=float), 'flow_out': np.empty(size, dtype=float),
                'cost': np.empty(size, dtype=float),
                'init_capacity': np.empty(size, dtype=float), 'eff': np.empty(size, dtype=float),
                'name': np.empty(size, dtype=str), 'node': np.empty(size, dtype=str),
                'network': np.empty(size, dtype=str),
                't': np.empty(size, dtype=float), 'scn': np.empty(size, dtype=float)}

        stor = pd.DataFrame(data=stor)

        n_stor = 0
        for n, net in result.networks.items():
            for node in net.nodes.keys():
                for i, c in enumerate(net.nodes[node].storages):
                    slices = stor.index[n_stor * h * scn: (n_stor + 1) * h * scn]
                    study_stor = study.networks[n].nodes[node].storages[i]

                    stor.loc[slices, 'max_capacity'] = study_stor.capacity
                    stor.loc[slices, 'capacity'] = c.capacity.flatten()
                    stor.loc[slices, 'max_flow_in'] = study_stor.flow_in
                    stor.loc[slices, 'flow_in'] = c.flow_in.flatten()
                    stor.loc[slices, 'max_flow_out'] = study_stor.flow_out
                    stor.loc[slices, 'flow_out'] = c.flow_out.flatten()
                    stor.loc[slices, 'cost'] = study_stor.cost
                    stor.loc[slices, 'init_capacity'] = study_stor.init_capacity
                    stor.loc[slices, 'eff'] = study_stor.eff
                    stor.loc[slices, 'network'] = n
                    stor.loc[slices, 'name'] = c.name
                    stor.loc[slices, 'node'] = node
                    stor.loc[slices, 't'] = np.tile(np.arange(h), scn)
                    stor.loc[slices, 'scn'] = np.repeat(np.arange(scn), h)

        return stor

    @staticmethod
    def _build_link(study: Study, result: Result):
        """
        Flat all data to build global link dataframe
        columns: | cost | avail | used | node | dest | t |
        """
        h = study.horizon
        scn = study.nb_scn
        elements = sum([sum([len(n.links) for n in net.nodes.values()]) for net in study.networks.values()])
        size = h * scn * elements

        link = {'cost': np.empty(size, dtype=float), 'avail': np.empty(size, dtype=float),
                'used': np.empty(size, dtype=float),
                'node': np.empty(size, dtype=str), 'dest': np.empty(size, dtype=str),
                'network': np.empty(size, dtype=str),
                't': np.empty(size, dtype=float), 'scn': np.empty(size, dtype=float)}
        link = pd.DataFrame(data=link)

        n_link = 0
        for n, net in result.networks.items():
            for node in net.nodes.keys():
                for i, c in enumerate(net.nodes[node].links):
                    slices = link.index[n_link * h * scn: (n_link + 1) * h * scn]
                    link.loc[slices, 'cost'] = c.cost.flatten()
                    link.loc[slices, 'dest'] = c.dest
                    link.loc[slices, 'node'] = node
                    link.loc[slices, 'network'] = n
                    link.loc[slices, 'avail'] = study.networks[n].nodes[node].links[i].quantity.flatten()
                    link.loc[slices, 'used'] = c.quantity.flatten()
                    link.loc[slices, 't'] = np.tile(np.arange(h), scn)
                    link.loc[slices, 'scn'] = np.repeat(np.arange(scn), h)

                    n_link += 1

        return link

    @staticmethod
    def _build_dest_converter(study: Study, result: Result):
        h = study.horizon
        scn = study.nb_scn
        elements = sum([len(v.src_ratios) for v in study.converters.values()])
        size = h * scn * elements

        dest_conv = {'name': np.empty(size, dtype=str), 'network': np.empty(size, dtype=str),
                     'node': np.empty(size, dtype=str), 'flow': np.empty(size, dtype=float),
                     'cost': np.empty(size, dtype=float), 'max': np.empty(size, dtype=float)}
        dest_conv = pd.DataFrame(data=dest_conv)

        for i, (name, v) in enumerate(study.converters.items()):
            slices = dest_conv.index[i * h * scn: (i + 1) * h * scn]
            dest_conv.loc[slices, 'name'] = v.name
            dest_conv.loc[slices, 'cost'] = v.cost
            dest_conv.loc[slices, 'max'] = v.max
            dest_conv.loc[slices, 'network'] = v.dest_network
            dest_conv.loc[slices, 'node'] = v.dest_node
            dest_conv.loc[slices, 'flow'] = result.converters[name].flow_dest.flatten()
            dest_conv.loc[slices, 't'] = np.tile(np.arange(h), scn)
            dest_conv.loc[slices, 'scn'] = np.repeat(np.arange(scn), h)

        return dest_conv

    @staticmethod
    def _build_src_converter(study: Study, result: Result):
        h = study.horizon
        scn = study.nb_scn
        elements = sum([len(v.src_ratios) for v in study.converters.values()])
        size = h * scn * elements

        src_conv = {'name': np.empty(size, dtype=str), 'network': np.empty(size, dtype=str),
                    'node': np.empty(size, dtype=str), 'ratio': np.empty(size, dtype=float),
                    'flow': np.empty(size, dtype=float), 'max': np.empty(size, dtype=float)}
        src_conv = pd.DataFrame(data=src_conv)

        s = 0
        for name, v in study.converters.items():
            src_size = len(v.src_ratios)
            e = s + h * scn * src_size
            slices = src_conv.index[s:e]
            src_conv.loc[slices, 'name'] = v.name
            src_conv.loc[slices, 'max'] = v.max
            src_conv.loc[slices, 't'] = np.tile(np.arange(h), scn * src_size)
            src_conv.loc[slices, 'scn'] = np.repeat(np.arange(scn), h * src_size)

            for i_src, (net, node) in enumerate(v.src_ratios.keys()):
                e = s + h * scn * (i_src + 1)
                slices = src_conv.index[s:e]
                src_conv.loc[slices, 'network'] = net
                src_conv.loc[slices, 'node'] = node
                src_conv.loc[slices, 'ratio'] = v.src_ratios[(net, node)]
                src_conv.loc[slices, 'flow'] = result.converters[name].flow_src[(net, node)].flatten()
                s = e
            s = e

        src_conv.loc[:, 'max'] /= src_conv[
            'ratio']  # max value is for output. Need to divide by ratio to find max for src

        return src_conv

    @staticmethod
    def _remove_useless_index_level(df: pd.DataFrame, indexes: List[Index]) -> pd.DataFrame:
        """
        If top index level has only on element then remove this index level. Do it recursively.

        :param df: dataframe with multi-index
        :param indexes: indexes level used
        :return: dataframe trimed with useless index(es) level
        """
        # TODO refactor without the help of indexes
        if indexes[0].is_alone() and indexes[0].index[0] in df.index:
            df = df.loc[indexes[0].index[0]].copy()
            return ResultAnalyzer._remove_useless_index_level(df, indexes[1:])
        else:
            return df

    @staticmethod
    def _pivot(indexes, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pivot table by appling filter and index hirarchy asked by indexes.

        :param names: list of index
        :return: pivot table
        """
        names = [i.column for i in indexes]
        mask = reduce(lambda a, b: a & b, (i.filter(df) for i in indexes))
        pt = pd.pivot_table(data=df[mask], index=names, aggfunc=lambda x: x.iloc[0])

        return ResultAnalyzer._remove_useless_index_level(df=pt, indexes=indexes)

    @staticmethod
    def check_index(indexes: List[Index], type: Type):
        """
        Check indexes cohesion
        :param indexes: list fo indexes
        :param type: Index type to check inside list
        :return: true if at least one type is in list False else
        """
        return any(isinstance(i, type) for i in indexes)

    @staticmethod
    def _assert_index(indexes: List[Index], type: Type):
        """
        Check indexes cohesion. Raise Value Error if not

        :param indexes: list fo indexes
        :param type: Index type to check inside list
        :return: true if at least one type is in list False else
        """
        if not ResultAnalyzer.check_index(indexes, type):
            raise ValueError('Indexes must contain a {}'.format(type.__class__.__name__))

    def filter(self, indexes: List[Index]) -> pd.DataFrame:
        """
        Aggregate according to index level and filter.
        """
        ResultAnalyzer._assert_index(indexes, TimeIndex)
        ResultAnalyzer._assert_index(indexes, NodeIndex)
        ResultAnalyzer._assert_index(indexes, NetworkIndex)
        ResultAnalyzer._assert_index(indexes, ScnIndex)

        if ResultAnalyzer.check_index(indexes, ConsIndex):
            return ResultAnalyzer._pivot(indexes, self.consumption)

        if ResultAnalyzer.check_index(indexes, ProdIndex):
            return ResultAnalyzer._pivot(indexes, self.production)

        if ResultAnalyzer.check_index(indexes, StorIndex):
            return ResultAnalyzer._pivot(indexes, self.storage)

        if ResultAnalyzer.check_index(indexes, LinkIndex):
            return ResultAnalyzer._pivot(indexes, self.link)

        if ResultAnalyzer.check_index(indexes, SrcConverter):
            return ResultAnalyzer._pivot(indexes, self.src_converter)

        if ResultAnalyzer.check_index(indexes, DestConverter):
            return ResultAnalyzer._pivot(indexes, self.dest_converter)

    def network(self, name='default'):
        """
        Entry point for fluent api
        :param name: network name. 'default' as default
        :return: Fluent API Selector
        """
        return NetworkFluentAPISelector([NetworkIndex(index=name)], self)

    def get_elements_inside(self, node: str, network: str = 'default'):
        """
        Get numbers of elements by node.

        :param network: network name
        :param node: node name
        :return: (nb of consumptions, nb of productions, nb of storages, nb of links (export), nb of converters (export), nb of converters (import)
        """
        n = self.study.networks[network].nodes[node]
        return len(n.consumptions), \
               len(n.productions), \
               len(n.storages), \
               len(n.links), \
               sum((network, node) in conv.src_ratios for conv in self.study.converters.values()), \
               sum((network == conv.dest_network) and (node == conv.dest_node) for conv in self.study.converters.values())

    def get_balance(self, node: str, network: str = 'default') -> np.ndarray:
        """
        Compute balance over time on asked node.

        :param node: node asked
        :param network: network asked. Default is 'default'
        :return: timeline array with balance exchanges value
        """
        balance = np.zeros((self.nb_scn, self.study.horizon))

        mask = (self.link['dest'] == node) & (self.link['network'] == network)
        im = pd.pivot_table(self.link[mask][['used', 'scn', 't']], index=['scn', 't'], aggfunc=np.sum)
        if im.size > 0:
            balance += -im['used'].values.reshape(self.nb_scn, self.horizon)

        mask = (self.link['node'] == node) & (self.link['network'] == network)
        exp = pd.pivot_table(self.link[mask][['used', 'scn', 't']], index=['scn', 't'], aggfunc=np.sum)
        if exp.size > 0:
            balance += exp['used'].values.reshape(self.nb_scn, self.horizon)
        return balance

    def get_cost(self, node: str, network: str = 'default') -> np.ndarray:
        """
        Compute adequacy cost on a node.

        :param node: node name
        :param network: network name, 'default' as default
        :return: matrix (scn, time)
        """
        cost = np.zeros((self.nb_scn, self.horizon))
        c, p, s, l, _, v = self.get_elements_inside(node, network)
        if c:
            cons = self.network(network).node(node).scn().time().consumption()
            cost += ((cons['asked'] - cons['given']) * cons['cost']).groupby(axis=0, level=(0, 1)) \
                .sum().sort_index(level=(0, 1)).values.reshape(self.nb_scn, self.horizon)

        if p:
            prod = self.network(network).node(node).scn().time().production()
            cost += (prod['used'] * prod['cost']).groupby(axis=0, level=(0, 1)) \
                .sum().sort_index(level=(0, 1)).values.reshape(self.nb_scn, self.horizon)

        if s:
            stor = self.network(network).node(node).scn().time().storage()
            cost += (stor['capacity'] * stor['cost']).groupby(axis=0, level=(0, 1)) \
                .sum().sort_index(level=(0, 1)).values.reshape(self.nb_scn, self.horizon)

        if l:
            link = self.network(network).node(node).scn().time().link()
            cost += (link['used'] * link['cost']).groupby(axis=0, level=(0, 1)) \
                .sum().sort_index(level=(0, 1)).values.reshape(self.nb_scn, self.horizon)

        if v:
            conv = self.network(network).node(node).scn().time().from_converter()
            cost += (conv['flow'] * conv['cost']).groupby(axis=0, level=(0, 1)) \
                .sum().sort_index(level=(0, 1)).values.reshape(self.nb_scn, self.horizon)

        return cost

    def get_rac(self, network='default') -> np.ndarray:
        """
        Compute Remain Availabale Capacities on network.

        :param network: selecto network to compute. Default is default.
        :return: matrix (scn, time)
        """
        def fill_width_zeros(arr: np.ndarray) -> np.ndarray:
            return np.zeros((self.nb_scn, self.horizon)) if arr.size == 0 else arr
        prod_used = self.production[self.production['network'] == network] \
            .drop(['avail', 'cost'], axis=1) \
            .pivot_table(index='scn', columns='t', aggfunc=np.sum) \
            .values
        prod_used = fill_width_zeros(prod_used)

        prod_avail = self.production[self.production['network'] == network] \
            .drop(['used', 'cost'], axis=1) \
            .pivot_table(index='scn', columns='t', aggfunc=np.sum) \
            .values
        prod_avail = fill_width_zeros(prod_avail)

        cons_asked = self.consumption[self.consumption['network'] == network] \
            .drop(['given', 'cost'], axis=1) \
            .pivot_table(index='scn', columns='t', aggfunc=np.sum) \
            .values
        cons_asked = fill_width_zeros(cons_asked)

        cons_given = self.consumption[self.consumption['network'] == network] \
            .drop(['asked', 'cost'], axis=1) \
            .pivot_table(index='scn', columns='t', aggfunc=np.sum) \
            .values
        cons_given = fill_width_zeros(cons_given)

        return (prod_avail - prod_used) - (cons_asked - cons_given)

    @property
    def horizon(self) -> int:
        """
        Shortcut to get study horizon.

        :return: study horizon
        """
        return self.study.horizon

    @property
    def nb_scn(self) -> int:
        """
        Shortcut to get study number of scenarios.

        :return: study number of scenarios
        """
        return self.study.nb_scn

    def nodes(self, network: str = 'default') -> List[str]:
        """
        Shortcut to get list of node names

        :param network: network selected
        :return: nodes name
        """
        return list(self.result.networks[network].nodes.keys())


class NetworkFluentAPISelector:
    """
    Fluent Api Selector to analyze network element.

    User can join network, node, consumption, production, link, time, scn to create filter and organize hierarchy.
    Join can me in any order, except:
    - join begin by network
    - join is unique only one element of node, time, scn are expected for each query
    - production, consumption and link are excluded themself, only on of them are expected for each query
    """
    FULL_DESCRIPTION = 5  # Need 5 indexes to describe completely a query

    def __init__(self, indexes: List[Index], analyzer: ResultAnalyzer):
        self.indexes = indexes
        self.analyzer = analyzer

        if not ResultAnalyzer.check_index(indexes, ConsIndex) \
                and not ResultAnalyzer.check_index(indexes, ProdIndex) \
                and not ResultAnalyzer.check_index(indexes, StorIndex) \
                and not ResultAnalyzer.check_index(indexes, LinkIndex) \
                and not ResultAnalyzer.check_index(indexes, SrcConverter) \
                and not ResultAnalyzer.check_index(indexes, DestConverter):
            self.consumption = lambda x=None: self._append(ConsIndex(x))
            self.production = lambda x=None: self._append(ProdIndex(x))
            self.link = lambda x=None: self._append(LinkIndex(x))
            self.storage = lambda x=None: self._append(StorIndex(x))
            self.to_converter = lambda x=None: self._append(SrcConverter(x))
            self.from_converter = lambda x=None: self._append(DestConverter(x))

        if not ResultAnalyzer.check_index(indexes, NodeIndex):
            self.node = lambda x=None: self._append(NodeIndex(x))

        if not ResultAnalyzer.check_index(indexes, TimeIndex):
            self.time = lambda x=None: self._append(TimeIndex(x))

        if not ResultAnalyzer.check_index(indexes, ScnIndex):
            self.scn = lambda x=None: self._append(ScnIndex(x))

    def _find_index_by_type(self, type: Type):
        return [i for i in self.indexes if isinstance(i, type)][0]

    def _append(self, index: Index):
        """
        Decide what to do between finish query and start analyze or resume query

        :param index:
        :return:
        """
        self.indexes.append(index)
        if len(self.indexes) == NetworkFluentAPISelector.FULL_DESCRIPTION:
            return self.analyzer.filter(self.indexes)
        else:
            return NetworkFluentAPISelector(self.indexes, self.analyzer)
