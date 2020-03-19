from abc import ABC, abstractmethod
from copy import deepcopy
from typing import List, Tuple

import pandas as pd
import numpy as np
from pandas import MultiIndex

from hadar.solver.input import DTO


class Plug(ABC, DTO):
    def __init__(self, inputs: List[str], outputs: List[str]):
        self.inputs = inputs
        self.outputs = outputs

    @abstractmethod
    def _linkable_to(self, other) -> bool:
        pass
    @abstractmethod
    def _join(self, other):
        pass


class FreePlug(Plug):
    def __init__(self):
        Plug.__init__(self, inputs=[], outputs=[])

    def _linkable_to(self, other: Plug) -> bool:
        return True

    def _join(self, other: Plug) -> Plug:
        # take input of next pipelines if current is restriction free
        if not isinstance(other, FreePlug):
            return deepcopy(other)
        return deepcopy(self)


class RestrictedPlug(Plug):
    def __init__(self, inputs, outputs):
        Plug.__init__(self, inputs=inputs, outputs=outputs)

    def _linkable_to(self, next) -> bool:
        if isinstance(next, FreePlug):
            return True
        return all(e in self.outputs for e in next.inputs)

    def _join(self, next: Plug) -> Plug:
        if isinstance(next, FreePlug):
            return self

        # keep output not used by next pipeline and add next outputs
        outputs = [e for e in self.outputs if e not in next.inputs] + next.outputs
        return RestrictedPlug(inputs=self.inputs, outputs=outputs)


class Compute(ABC, DTO):
    def __init__(self):
        pass

    @abstractmethod
    def process(self, timeline: pd.DataFrame) -> pd.DataFrame:
        pass


class LocalCompute(ABC, DTO, Compute):
    def __init__(self):
        pass

    @abstractmethod
    def local_process(self, timeline: pd.DataFrame, scn: int) -> pd.DataFrame:
        pass

    def process(self, timelines: pd.DataFrame) -> pd.DataFrame:
        for scn in timelines.columns.get_level_values(0).unique():
            timelines[scn] = self._local_process(timelines[scn])


class Pipeline(ABC):
    def __init__(self, mandatory_fields: List[str] = None, created_fields: List[str] = None):
        if (mandatory_fields is None) != (created_fields is None):
            raise ValueError('mandatory_fields and created_fields work together. You can\'t given only one of them')

        self.next_computes = []
        self.input_fields = [] if mandatory_fields is None else mandatory_fields
        self.output_fields = [] if created_fields is None else created_fields

    def __add__(self, other):
        if not isinstance(other, Pipeline):
            raise ValueError('Only addition with other pipeline is accepted not with %s' % type(other))

        if other.is_restricted() and not self._linkable_io(other):
            raise ValueError("Pipeline can't be added %s has output %s and %s has input %s" %
                             (self.__class__.__name__, self.output_fields, other.__class__.__name__, other.input_fields))

        self._merge_io(other)
        self.next_computes.append(other.compute)
        return self

    @abstractmethod
    def _process(self, timelines: pd.DataFrame) -> pd.DataFrame:
        pass

    def is_restricted(self):
        return (self.input_fields != []) and (self.output_fields != [])

    def compute(self, timelines: pd.DataFrame) -> pd.DataFrame:
        timelines = self._process(timelines)
        for compute in self.next_computes:
            timelines = compute(timelines.copy())

        return timelines.copy()

    def _merge_io(self, other):
        # take input of next pipelines if current is restriction free
        if not self.is_restricted() and other.is_restricted():
            self.input_fields = other.input_fields

        # remove outputs used by next pipeline and add its outputs
        if other.is_restricted():
            [self.output_fields.remove(e) for e in other.input_fields if e in self.output_fields]
            self.output_fields += other.output_fields

    def _linkable_io(self, other) -> bool:
        if not self.is_restricted():
            return True
        return all(e in self.output_fields for e in other.input_fields)

#            for scn in timelines.columns.get_level_values(0).unique():
#                timelines[scn] = self._process(timelines[scn])