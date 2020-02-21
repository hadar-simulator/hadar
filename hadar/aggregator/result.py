from typing import Union, TypeVar, List, Generic, Tuple, Type

import pandas as pd
import numpy as np

from solver.output import Result, Study

T = TypeVar('T')


class Index(Generic[T]):
    def __init__(self, column, index: Union[List[T], T] = None):
        self.all = False
        self.column = column
        if index is None:
            self.all = True
        elif not isinstance(index, list):
            self.index = [index]
        else:
            self.index = index

    def filter(self, df: pd.DataFrame) -> pd.Series:
        if self.all:
            return df[self.column].notnull()
        return df[self.column].isin(self.index)


class NodeIndex(Index[str]):
    def __init__(self, index: Union[List[str], str] = None):
        Index.__init__(self, column='node', index=index)


class TypeIndex(Index[str]):
    def __init__(self, index: Union[List[str], str] = None):
        Index.__init__(self, column='type', index=index)


class TimeIndex(Index[int]):
    def __init__(self, index: Union[List[int], int] = None, start: int = None, end: int = None):
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
    def __init__(self, study: Study, result: Result):
        self.result = result
        self.study = study

        self.consumption = self._build_consumption()
        self.production = self._build_production()
        self.border = self._build_border()

    def _build_consumption(self):
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
    def _pivot(i0: Index, i1: Index, i2: Index, df: pd.DataFrame) -> pd.DataFrame:
        return pd.pivot_table(data=df[i0.filter(df) & i1.filter(df) & i2.filter(df)],
                              index=[i0.column, i1.column, i2.column], aggfunc=lambda x: x[0])

    @staticmethod
    def _check_index(i0: Index, i1: Index, i2: Index, type: Type):
        if not (isinstance(i0, type) or isinstance(i1, type) or isinstance(i2, type)):
            raise ValueError('Indexes must contain a {}'.format(type.__class__.__name__))

    def agg_cons(self, i0: Index, i1: Index, i2: Index) -> pd.DataFrame:
        ResultAggregator._check_index(i0, i1, i2, TimeIndex)
        ResultAggregator._check_index(i0, i1, i2, NodeIndex)
        ResultAggregator._check_index(i0, i1, i2, TypeIndex)

        return ResultAggregator._pivot(i0, i1, i2, self.consumption)

    def agg_prod(self, i0: Index, i1: Index, i2: Index) -> pd.DataFrame:
        ResultAggregator._check_index(i0, i1, i2, TimeIndex)
        ResultAggregator._check_index(i0, i1, i2, NodeIndex)
        ResultAggregator._check_index(i0, i1, i2, TypeIndex)

        return ResultAggregator._pivot(i0, i1, i2, self.production)

    def agg_border(self, i0: Index, i1: Index, i2: Index) -> pd.DataFrame:
        ResultAggregator._check_index(i0, i1, i2, TimeIndex)
        # TODO ResultAggregator._check_index(i0, i1, i2, SrcIndex)
        # TODO ResultAggregator._check_index(i0, i1, i2, DestIndex)

        return ResultAggregator._pivot(i0, i1, i2, self.production)
