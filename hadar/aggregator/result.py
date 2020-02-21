from typing import Union, TypeVar, List, Generic, Tuple

import pandas as pd
import numpy as np

from solver.output import Result, Study

T = TypeVar('T')


class Index(Generic[T]):
    def __init__(self, index: Union[List[T], T] = None):
        self.all = False
        if index is None:
            self.all = True
        elif not isinstance(index, list):
            self.index = [index]
        else:
            self.index = index


class NodeIndex(Index[str]):
    def __init__(self, index: Union[List[str], str] = None):
        Index.__init__(self, index=index)


class TimeIndex(Index[int]):
    def __init__(self, index: Union[List[int], int] = None, start: int = None, end: int = None):
        if index is None:
            if start is None and end is not None:
                raise ValueError('Please give an start index if you give an end index')
            if start is not None and end is None:
                raise ValueError('Please give an end index if you give a start index')
            index = list(range(start, end))
        Index.__init__(self, index)


class ResultAggregator:
    def __init__(self, study: Study, result: Result):
        self.result = result
        self.study = study
        self.nodes = {}
        self.timestamp = {}

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
    
    def aggregate(self, indexes: List[Index]) -> Tuple[pd.DataFrame]:
        pass