from typing import Union, TypeVar, List, Generic, Tuple, Type

import pandas as pd
import numpy as np

from hadar.solver.output import Result, Study

T = TypeVar('T')


class Index(Generic[T]):
    """
    Generic Index to use to select and rank data.
    """
    def __init__(self, column, index: Union[List[T], T] = None):
        """
        Initiate instance.

        :param column: column name link to this index
        :param index: list of index or element to filter from data. None by default to say keep all data.
        """
        self.all = False
        self.column = column
        if index is None:
            self.all = True
        elif not isinstance(index, list):
            self.index = [index]
        else:
            self.index = index

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
    def __init__(self, index: Union[List[str], str] = None):
        Index.__init__(self, column='node', index=index)


class SrcIndex(Index[str]):
    """Index implementation to filter src node"""
    def __init__(self, index: Union[List[str], str] = None):
        Index.__init__(self, column='src', index=index)


class DestIndex(Index[str]):
    """Index implementation to filter destination node"""
    def __init__(self, index: Union[List[str], str] = None):
        Index.__init__(self, column='dest', index=index)


class TypeIndex(Index[str]):
    """Index implementation to filter type of elements"""
    def __init__(self, index: Union[List[str], str] = None):
        Index.__init__(self, column='type', index=index)


class TimeIndex(Index[int]):
    """Index implementation to filter by time step"""
    def __init__(self, index: Union[List[int], int] = None, start: int = None, end: int = None):
        """
        Create instance.

        :param index: one element or list on element to filter.
        :param start: start datetime to filter (to use instead of index)
        :param end: end datetime to filter (to use instead of index)
        """
        if index is None and start is None and end is None:
            Index.__init__(self, column='t')
        elif index is None:
            if start is None:
                raise ValueError('Please give an start index')
            if end is None:
                raise ValueError('Please give an end index')
            index = list(range(start, end))
        Index.__init__(self, column='t', index=index)


class ResultAggregator:
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

        self.consumption = self._build_consumption()
        self.production = self._build_production()
        self.border = self._build_border()

    def _build_consumption(self):
        """
        Flat all data to build global consumption dataframe
        columns: | cost | type | node | asked | given | t |
        """
        h = self.study.horizon
        s = h * sum([len(n.consumptions) for n in self.result.nodes.values()])
        cons = {'cost': np.empty(s), 'asked': np.empty(s), 'given': np.empty(s),
                'type': np.empty(s), 'node': np.empty(s), 't': np.empty(s)}
        cons = pd.DataFrame(data=cons)

        n_cons = 0
        for n, name in enumerate(self.result.nodes.keys()):
            for i, c in enumerate(self.result.nodes[name].consumptions):
                slices = cons.index[n_cons * h: (n_cons + 1) * h]
                cons.loc[slices, 'cost'] = c.cost
                cons.loc[slices, 'type'] = c.type
                cons.loc[slices, 'node'] = name
                cons.loc[slices, 'asked'] = self.study.nodes[name].consumptions[i].quantity
                cons.loc[slices, 'given'] = c.quantity
                cons.loc[slices, 't'] = np.arange(h)

                n_cons += 1

        return cons

    def _build_production(self):
        """
        Flat all data to build global production dataframe
        columns: | cost | avail | used | type | node | t |
        """
        h = self.study.horizon
        s = h * sum([len(n.productions) for n in self.result.nodes.values()])
        prod = {'cost': np.empty(s), 'avail': np.empty(s), 'used': np.empty(s),
                'type': np.empty(s), 'node': np.empty(s), 't': np.empty(s)}
        prod = pd.DataFrame(data=prod)

        n_prod = 0
        for n, name in enumerate(self.result.nodes.keys()):
            for i, c in enumerate(self.result.nodes[name].productions):
                slices = prod.index[n_prod * h: (n_prod + 1) * h]
                prod.loc[slices, 'cost'] = c.cost
                prod.loc[slices, 'type'] = c.type
                prod.loc[slices, 'node'] = name
                prod.loc[slices, 'avail'] = self.study.nodes[name].productions[i].quantity
                prod.loc[slices, 'used'] = c.quantity
                prod.loc[slices, 't'] = np.arange(h)

                n_prod += 1

        return prod

    def _build_border(self):
        """
        Flat all data to build global border dataframe
        columns: | cost | avail | used | src | dest | t |
        """
        h = self.study.horizon
        s = h * sum([len(n.borders) for n in self.result.nodes.values()])
        border = {'cost': np.empty(s), 'avail': np.empty(s), 'used': np.empty(s),
                  'src': np.empty(s), 'dest': np.empty(s), 't': np.empty(s)}
        border = pd.DataFrame(data=border)

        n_border = 0
        for n, name in enumerate(self.result.nodes.keys()):
            for i, c in enumerate(self.result.nodes[name].borders):
                slices = border.index[n_border * h: (n_border + 1) * h]
                border.loc[slices, 'cost'] = c.cost
                border.loc[slices, 'dest'] = c.dest
                border.loc[slices, 'src'] = name
                border.loc[slices, 'avail'] = self.study.nodes[name].borders[i].quantity
                border.loc[slices, 'used'] = c.quantity
                border.loc[slices, 't'] = np.arange(h)

                n_border += 1

        return border

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
            return ResultAggregator._remove_useless_index_level(df, indexes[1:])
        else:
            return df

    @staticmethod
    def _pivot(i0: Index, i1: Index, i2: Index, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pivot table by appling filter and index hirarchy asked by indexes.

        :param i0: first level index
        :param i1: second level index
        :param i2: third level index
        :param df: dataframe to pivot
        :return: pivot table
        """
        indexes = [i0.column, i1.column, i2.column]
        pt = pd.pivot_table(data=df[i0.filter(df) & i1.filter(df) & i2.filter(df)],
                            index=indexes, aggfunc=lambda x: x.iloc[0])

        return ResultAggregator._remove_useless_index_level(df=pt, indexes=[i0, i1, i2])

    @staticmethod
    def _assert_index(i0: Index, i1: Index, i2: Index, type: Type):
        """
        Check indexes cohesion. Raise ValueError exception if indexes are wrong.

        :param i0: first level index
        :param i1: second level index
        :param i2: third level index
        :param type: type to check inside index
        :return:
        """
        if not (isinstance(i0, type) or isinstance(i1, type) or isinstance(i2, type)):
            raise ValueError('Indexes must contain a {}'.format(type.__class__.__name__))

    def agg_cons(self, i0: Index, i1: Index, i2: Index) -> pd.DataFrame:
        """
        Aggregate consumption according to index level and filter.

        :param i0: first level index. Index type must be [NodeIndex, TypeIndex, TimeIndex]
        :param i1: second level index. Index type must be [NodeIndex, TypeIndex, TimeIndex]
        :param i2: third level index. Index type must be [NodeIndex, TypeIndex, TimeIndex]
        :return: dataframe with hierarchical and filter index level asked
        """
        ResultAggregator._assert_index(i0, i1, i2, TimeIndex)
        ResultAggregator._assert_index(i0, i1, i2, NodeIndex)
        ResultAggregator._assert_index(i0, i1, i2, TypeIndex)

        return ResultAggregator._pivot(i0, i1, i2, self.consumption)

    def agg_prod(self, i0: Index, i1: Index, i2: Index) -> pd.DataFrame:
        """
        Aggregate production according to index level and filter.

        :param i0: first level index. Index type must be [NodeIndex, TypeIndex, TimeIndex]
        :param i1: second level index. Index type must be [NodeIndex, TypeIndex, TimeIndex]
        :param i2: third level index. Index type must be [NodeIndex, TypeIndex, TimeIndex]
        :return: dataframe with hierarchical and filter index level asked
        """
        ResultAggregator._assert_index(i0, i1, i2, TimeIndex)
        ResultAggregator._assert_index(i0, i1, i2, NodeIndex)
        ResultAggregator._assert_index(i0, i1, i2, TypeIndex)

        return ResultAggregator._pivot(i0, i1, i2, self.production)

    def agg_border(self, i0: Index, i1: Index, i2: Index) -> pd.DataFrame:
        """
        Aggregate border according to index level and filter.

        :param i0: first level index. Index type must be [DestIndex, SrcIndex, TimeIndex]
        :param i1: second level index. Index type must be [DestIndex, SrcIndex, TimeIndex]
        :param i2: third level index. Index type must be [DestIndex, SrcIndex, TimeIndex]
        :return: dataframe with hierarchical and filter index level asked
        """
        ResultAggregator._assert_index(i0, i1, i2, TimeIndex)
        ResultAggregator._assert_index(i0, i1, i2, SrcIndex)
        ResultAggregator._assert_index(i0, i1, i2, DestIndex)

        return ResultAggregator._pivot(i0, i1, i2, self.border)

    def get_elements_inside(self, node: str):
        """
        Get numbers of elements by node.

        :param node: node name
        :return: (nb of consumptions, nb of productions, nb of border (export))
        """
        return len(self.result.nodes[node].consumptions),\
               len(self.result.nodes[node].productions),\
               len(self.result.nodes[node].borders)

    def get_balance(self, node: str) -> np.ndarray:
        """
        Compute balance over time on asked node.

        :param node: node asked
        :return: timeline array with balance exchanges value
        """
        balance = np.zeros(self.study.horizon)

        im = pd.pivot_table(self.border[self.border['dest'] == node][['used', 't']], index='t', aggfunc=np.sum)
        if im.size > 0:
            balance += -im['used'].values

        exp = pd.pivot_table(self.border[self.border['src'] == node][['used', 't']], index='t', aggfunc=np.sum)
        if exp.size > 0:
            balance += exp['used'].values
        return balance

    def get_cost(self, node: str) -> np.ndarray:
        cost = np.zeros(self.horizon)
        c, p, b = self.get_elements_inside(node)
        if c:
            cons = self.agg_cons(NodeIndex(node), TimeIndex(), TypeIndex())
            cost += ((cons['asked'] - cons['given'])*cons['cost']).groupby(axis=0, level=0).sum().sort_index().values

        if p:
            prod = self.agg_prod(NodeIndex(node), TimeIndex(), TypeIndex())
            cost += (prod['used']*prod['cost']).groupby(axis=0, level=0).sum().sort_index().values

        if b:
            border = self.agg_border(SrcIndex(node), TimeIndex(), DestIndex())
            cost += (border['used']*border['cost']).groupby(axis=0, level=0).sum().sort_index().values

        return cost

    @property
    def horizon(self) -> int:
        """
        Shortcut to get study horizon.

        :return: study horizon
        """
        return self.study.horizon

    @property
    def nodes(self) -> List[str]:
        """
        Shortcut to get list of node names

        :return: nodes name
        """
        return self.result.nodes.keys()
