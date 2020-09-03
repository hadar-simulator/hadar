#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import numpy as np

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Union, List

from hadar.optimizer.utils import JSON

T = TypeVar('T')


class NumericalValue(JSON, ABC, Generic[T]):
    def __init__(self, value: T, horizon: int, nb_scn: int):
        self.value = value
        self.horizon = horizon
        self.nb_scn = nb_scn

    @abstractmethod
    def __getitem__(self, item) -> float:
        pass

    @abstractmethod
    def __lt__(self, other) -> bool:
        pass

    @abstractmethod
    def flatten(self) -> np.ndarray:
        pass


class ScalarNumericalValue(NumericalValue[float]):
    def __getitem__(self, item) -> float:
        i, j = item
        if i >= self.nb_scn:
            raise IndexError('There are %d scenario you ask the %dth' % (self.nb_scn, i))
        if j >= self.horizon:
            raise IndexError('There are %d time step you ask the %dth' % (self.horizon, j))
        return self.value

    def __lt__(self, other):
        return self.value < other

    def flatten(self) -> np.ndarray:
        return np.ones(self.horizon * self.nb_scn) * self.value

    @staticmethod
    def from_json(dict):
        return ScalarNumericalValue(**dict)


class NumpyNumericalValue(NumericalValue[np.ndarray], ABC):
    def __lt__(self, other) -> bool:
        return np.all(self.value < other)


class MatrixNumericalValue(NumpyNumericalValue):
    def __getitem__(self, item) -> float:
        i, j = item
        return self.value[i, j]

    def flatten(self) -> np.ndarray:
        return self.value.flatten()

    @staticmethod
    def from_json(dict):
        dict['value'] = np.ndarray(dict['value'])
        MatrixNumericalValue(**dict)


class RowNumericValue(NumpyNumericalValue):
    def __getitem__(self, item) -> float:
        i, j = item
        if i >= self.nb_scn:
            raise IndexError('There are %d scenario you ask the %dth' % (self.nb_scn, i))
        return self.value[j]

    def flatten(self) -> np.ndarray:
        return np.tile(self.value, self.nb_scn)

    @staticmethod
    def from_json(dict):
        dict['value'] = np.ndarray(dict['value'])
        MatrixNumericalValue(**dict)


class ColumnNumericValue(NumpyNumericalValue):
    def __getitem__(self, item) -> float:
        i, j = item
        if j >= self.horizon:
            raise IndexError('There are %d time step you ask the %dth' % (self.horizon, j))
        return self.value[i, 0]

    def flatten(self) -> np.ndarray:
        return np.repeat(self.value.flatten(), self.horizon)

    @staticmethod
    def from_json(dict):
        dict['value'] = np.ndarray(dict['value'])
        MatrixNumericalValue(**dict)


class NumericalValueFactory:

    def __init__(self, horizon: int, nb_scn: int):
        self.horizon = horizon
        self.nb_scn = nb_scn

    def create(self, value: Union[float, List[float], str, np.ndarray, NumericalValue]) -> NumericalValue:
        if isinstance(value, NumericalValue):
            return value

        if isinstance(value, int):
            return ScalarNumericalValue(value=value, horizon=self.horizon, nb_scn=self.nb_scn)

        if isinstance(value, List):
            value = np.array(value)

        if isinstance(value, np.ndarray):
            # If scenario are not provided copy timeseries for each scenario
            if value.shape == (self.horizon,):
                return RowNumericValue(value=value, horizon=self.horizon, nb_scn=self.nb_scn)

            # If horizon are not provide extend each scenario to full horizon
            if value.shape == (self.nb_scn, 1):
                return ColumnNumericValue(value=value, horizon=self.horizon, nb_scn=self.nb_scn)

            # If perfect size
            if value.shape == (self.nb_scn, self.horizon):
                return MatrixNumericalValue(value=value, horizon=self.horizon, nb_scn=self.nb_scn)