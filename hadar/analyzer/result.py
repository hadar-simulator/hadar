#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

from typing import Union, TypeVar, List, Generic, Type

import pandas as pd
import numpy as np

from hadar.optimizer.output import Result, OutputNode
from hadar.optimizer.input import Study

__all__ = ['ResultAnalyzer']


T = TypeVar('T')


class Index(Generic[T]):
    """
    Generic Index to use to select and rank data.
    """
    def __init__(self, column):
        """
        Initiate instance.

        :param column: column name link to this index
        :param index: list of index or element to filter from data. None by default to say keep all data.
        """
        self.all = True
        self.column = column

    def __getitem__(self, index):
        if isinstance(index, list):
            index = tuple(index)
        if not isinstance(index, tuple):
            index = tuple([index])

        if len(index) == 0:
            self.all = True
        else:
            self.index = index
            self.all = False
        return self

    def filter(self, df: pd.DataFrame) -> pd.Series:
        """
        Filter dataframe. Filter columns with columns attributes with index values.

        :param df: dataframe to filter
        :return: Series of boolean to set row to keep
        """
        if self.all:
            return df[self.column].notnull()
        return df[self.column].isin(self.index)

    def is_alone(self):
        """
        Ask if index filter element is alone.

        :return: if index filter only one value return True else False
        """
        return not self.all and len(self.index) <= 1


class NodeIndex(Index[str]):
    """Index implementation to filter nodes"""
    def __init__(self):
        Index.__init__(self, column='node')


class SrcIndex(Index[str]):
    """Index implementation to filter src node"""
    def __init__(self):
        Index.__init__(self, column='src')


class DestIndex(Index[str]):
    """Index implementation to filter destination node"""
    def __init__(self):
        Index.__init__(self, column='dest')


class NameIndex(Index[str]):
    """Index implementation to filter name of elements"""
    def __init__(self):
        Index.__init__(self, column='name')


class IntIndex(Index[int]):
    """Index implementation to handle int index with slice"""
    def __init__(self, column: str):
        """
        Create instance.

        :param index: one element or list on element to filter.
        :param start: start datetime to filter (to use instead of index)
        :param end: end datetime to filter (to use instead of index)
        """
        Index.__init__(self, column=column)

    def __getitem__(self, index):
        if isinstance(index, slice):
            index = tuple(range(index.start, index.stop, index.step if index.step else 1))
        return Index.__getitem__(self, index)


class TimeIndex(IntIndex):
    """Index implementation to filter by time step"""
    def __init__(self):
        IntIndex.__init__(self, column='t')


class ScnIndex(IntIndex):
    """index implementation to filter by scenario"""
    def __init__(self):
        IntIndex.__init__(self, column='scn')


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
        self.link = ResultAnalyzer.link(self.study, self.result)

    @staticmethod
    def _build_consumption(study: Study, result: Result):
        """
        Flat all data to build global consumption dataframe
        columns: | cost | name | node | asked | given | t |
        """
        h = study.horizon
        scn = study.nb_scn
        s = scn * h * sum([len(n.consumptions) for n in study.nodes.values()])
        cons = {'cost': np.empty(s), 'asked': np.empty(s), 'given': np.empty(s),
                'name': np.empty(s), 'node': np.empty(s), 't': np.empty(s), 'scn': np.empty(s)}
        cons = pd.DataFrame(data=cons)

        n_cons = 0
        for n, name in enumerate(result.nodes.keys()):
            for i, c in enumerate(result.nodes[name].consumptions):
                slices = cons.index[n_cons * h * scn: (n_cons + 1) * h * scn]
                cons.loc[slices, 'cost'] = c.cost
                cons.loc[slices, 'name'] = c.name
                cons.loc[slices, 'node'] = name
                cons.loc[slices, 'asked'] = study.nodes[name].consumptions[i].quantity.flatten()
                cons.loc[slices, 'given'] = c.quantity.flatten()
                cons.loc[slices, 't'] = np.tile(np.arange(h), scn)
                cons.loc[slices, 'scn'] = np.repeat(np.arange(scn), h)

                n_cons += 1

        return cons

    @staticmethod
    def _build_production(study: Study, result: Result):
        """
        Flat all data to build global production dataframe
        columns: | cost | avail | used | name | node | t |
        """
        h = study.horizon
        scn = study.nb_scn
        s = scn * h * sum([len(n.productions) for n in result.nodes.values()])
        prod = {'cost': np.empty(s), 'avail': np.empty(s), 'used': np.empty(s),
                'name': np.empty(s), 'node': np.empty(s), 't': np.empty(s), 'scn': np.empty(s)}
        prod = pd.DataFrame(data=prod)

        n_prod = 0
        for n, name in enumerate(result.nodes.keys()):
            for i, c in enumerate(result.nodes[name].productions):
                slices = prod.index[n_prod * h * scn: (n_prod + 1) * h * scn]
                prod.loc[slices, 'cost'] = c.cost
                prod.loc[slices, 'name'] = c.name
                prod.loc[slices, 'node'] = name
                prod.loc[slices, 'avail'] = study.nodes[name].productions[i].quantity.flatten()
                prod.loc[slices, 'used'] = c.quantity.flatten()
                prod.loc[slices, 't'] = np.tile(np.arange(h), scn)
                prod.loc[slices, 'scn'] = np.repeat(np.arange(scn), h)

                n_prod += 1

        return prod

    @staticmethod
    def link(study: Study, result: Result):
        """
        Flat all data to build global link dataframe
        columns: | cost | avail | used | src | dest | t |
        """
        h = study.horizon
        scn = study.nb_scn
        s = h * scn * sum([len(n.links) for n in result.nodes.values()])
        link = {'cost': np.empty(s), 'avail': np.empty(s), 'used': np.empty(s),
                  'src': np.empty(s), 'dest': np.empty(s), 't': np.empty(s), 'scn': np.empty(s)}
        link = pd.DataFrame(data=link)

        n_link = 0
        for n, name in enumerate(result.nodes.keys()):
            for i, c in enumerate(result.nodes[name].links):
                slices = link.index[n_link * h * scn: (n_link + 1) * h * scn]
                link.loc[slices, 'cost'] = c.cost
                link.loc[slices, 'dest'] = c.dest
                link.loc[slices, 'src'] = name
                link.loc[slices, 'avail'] = study.nodes[name].links[i].quantity.flatten()
                link.loc[slices, 'used'] = c.quantity.flatten()
                link.loc[slices, 't'] = np.tile(np.arange(h), scn)
                link.loc[slices, 'scn'] = np.repeat(np.arange(scn), h)

                n_link += 1

        return link

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
    def _pivot(i0: Index, i1: Index, i2: Index, i3: Index, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pivot table by appling filter and index hirarchy asked by indexes.

        :param i0: first level index
        :param i1: second level index
        :param i2: third level index
        :param i3: fourth level index
        :param df: dataframe to pivot
        :return: pivot table
        """
        indexes = [i0.column, i1.column, i2.column, i3.column]
        pt = pd.pivot_table(data=df[i0.filter(df) & i1.filter(df) & i2.filter(df) & i3.filter(df)],
                            index=indexes, aggfunc=lambda x: x.iloc[0])

        return ResultAnalyzer._remove_useless_index_level(df=pt, indexes=[i0, i1, i2, i3])

    @staticmethod
    def _assert_index(i0: Index, i1: Index, i2: Index, i3: Index, type: Type):
        """
        Check indexes cohesion. Raise ValueError exception if indexes are wrong.

        :param i0: first level index
        :param i1: second level index
        :param i2: third level index
        :param i3: fourth level index
        :param type: type to check inside index
        :return:
        """
        if not (isinstance(i0, type) or isinstance(i1, type) or isinstance(i2, type) or isinstance(i3, type)):
            raise ValueError('Indexes must contain a {}'.format(type.__class__.__name__))

    def agg_cons(self, i0: Index, i1: Index, i2: Index, i3: Index) -> pd.DataFrame:
        """
        Aggregate consumption according to index level and filter.

        :param i0: first level index. Index type must be [NodeIndex, NameIndex, TimeIndex, ScnIndex]]
        :param i1: second level index. Index type must be [NodeIndex, NameIndex, TimeIndex, ScnIndex]]
        :param i2: third level index. Index type must be [NodeIndex, NameIndex, TimeIndex, ScnIndex]]
        :param i3 fourth level index. Index type must be [NodeIndex, NameIndex, TimeIndex, ScnIndex]
        :return: dataframe with hierarchical and filter index level asked
        """
        ResultAnalyzer._assert_index(i0, i1, i2, i3, TimeIndex)
        ResultAnalyzer._assert_index(i0, i1, i2, i3, NodeIndex)
        ResultAnalyzer._assert_index(i0, i1, i2, i3, NameIndex)
        ResultAnalyzer._assert_index(i0, i1, i2, i3, ScnIndex)

        return ResultAnalyzer._pivot(i0, i1, i2, i3, self.consumption)

    def agg_prod(self, i0: Index, i1: Index, i2: Index, i3: Index) -> pd.DataFrame:
        """
        Aggregate production according to index level and filter.

        :param i0: first level index. Index type must be [NodeIndex, NameIndex, TimeIndex, ScnIndex]]
        :param i1: second level index. Index type must be [NodeIndex, NameIndex, TimeIndex, ScnIndex]]
        :param i2: third level index. Index type must be [NodeIndex, NameIndex, TimeIndex, ScnIndex]]
        :param i3 fourth level index. Index type must be [NodeIndex, NameIndex, TimeIndex, ScnIndex]
        :return: dataframe with hierarchical and filter index level asked
        """
        ResultAnalyzer._assert_index(i0, i1, i2, i3, TimeIndex)
        ResultAnalyzer._assert_index(i0, i1, i2, i3, NodeIndex)
        ResultAnalyzer._assert_index(i0, i1, i2, i3, NameIndex)
        ResultAnalyzer._assert_index(i0, i1, i2, i3, ScnIndex)

        return ResultAnalyzer._pivot(i0, i1, i2, i3, self.production)

    def agg_link(self, i0: Index, i1: Index, i2: Index, i3: Index) -> pd.DataFrame:
        """
        Aggregate link according to index level and filter.

        :param i0: first level index. Index type must be [DestIndex, SrcIndex, TimeIndex, ScnIndex]
        :param i1: second level index. Index type must be [DestIndex, SrcIndex, TimeIndex, ScnIndex]
        :param i2: third level index. Index type must be [DestIndex, SrcIndex, TimeIndex, ScnIndex]
        :param i3 fourth level index. Index type must be [DestIndex, ScrIndex, TimeIndex, ScnIndex]
        :return: dataframe with hierarchical and filter index level asked
        """
        ResultAnalyzer._assert_index(i0, i1, i2, i3, TimeIndex)
        ResultAnalyzer._assert_index(i0, i1, i2, i3, SrcIndex)
        ResultAnalyzer._assert_index(i0, i1, i2, i3, DestIndex)
        ResultAnalyzer._assert_index(i0, i1, i2, i3, ScnIndex)

        return ResultAnalyzer._pivot(i0, i1, i2, i3, self.link)

    def get_elements_inside(self, node: str):
        """
        Get numbers of elements by node.

        :param node: node name
        :return: (nb of consumptions, nb of productions, nb of links (export))
        """
        return len(self.result.nodes[node].consumptions),\
               len(self.result.nodes[node].productions),\
               len(self.result.nodes[node].links)

    def get_balance(self, node: str) -> np.ndarray:
        """
        Compute balance over time on asked node.

        :param node: node asked
        :return: timeline array with balance exchanges value
        """
        balance = np.zeros((self.nb_scn, self.study.horizon))

        im = pd.pivot_table(self.link[self.link['dest'] == node][['used', 'scn', 't']], index=['scn', 't'], aggfunc=np.sum)
        if im.size > 0:
            balance += -im['used'].values.reshape(self.nb_scn, self.horizon)

        exp = pd.pivot_table(self.link[self.link['src'] == node][['used', 'scn', 't']], index=['scn', 't'], aggfunc=np.sum)
        if exp.size > 0:
            balance += exp['used'].values.reshape(self.nb_scn, self.horizon)
        return balance

    def get_cost(self, node: str) -> np.ndarray:
        cost = np.zeros((self.nb_scn,  self.horizon))
        c, p, b = self.get_elements_inside(node)
        if c:
            cons = self.agg_cons(self.inode[node], self.iscn, self.itime, self.iname)
            cost += ((cons['asked'] - cons['given'])*cons['cost']).groupby(axis=0, level=(0, 1))\
                .sum().sort_index(level=(0, 1)).values.reshape(self.nb_scn, self.horizon)

        if p:
            prod = self.agg_prod(self.inode[node], self.iscn, self.itime, self.iname)
            cost += (prod['used']*prod['cost']).groupby(axis=0, level=(0, 1))\
                .sum().sort_index(level=(0, 1)).values.reshape(self.nb_scn, self.horizon)

        if b:
            link = self.agg_link(self.isrc[node], self.iscn, self.itime, self.idest)
            cost += (link['used']*link['cost']).groupby(axis=0, level=(0, 1))\
                .sum().sort_index(level=(0, 1)).values.reshape(self.nb_scn, self.horizon)

        return cost

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

    @property
    def nodes(self) -> List[str]:
        """
        Shortcut to get list of node names

        :return: nodes name
        """
        return self.result.nodes.keys()

    @property
    def inode(self) -> NodeIndex:
        """
        Get a node index to specify node slice to aggregate consumption or production.

        :return: new instance of NodeIndex()
        """
        return NodeIndex()

    @property
    def iname(self) -> NameIndex:
        """
        Get a name index to specify name slice to aggregate consumption or production.

        :return: new instance of NameIndex()
        """
        return NameIndex()

    @property
    def isrc(self) -> SrcIndex:
        """
        Get a source index to specify source slice to aggregate link.

        :return: new instance of SrcIndex()
        """
        return SrcIndex()

    @property
    def idest(self) -> DestIndex:
        """
        Get a destination index to specify destination slice to aggregate link.

        :return: new instance of DestIndex()
        """
        return DestIndex()

    @property
    def itime(self) -> TimeIndex:
        """
        Get a time index to specify time slice to aggregate consumption, production or link.

        :return: new instance of TimeIndex()
        """
        return TimeIndex()

    @property
    def iscn(self) -> ScnIndex:
        """
        Get a scenario index to specify scenario slice to aggregate consumption, production or link.

        :return: new instance of ScnIndex()
        """
        return ScnIndex()
