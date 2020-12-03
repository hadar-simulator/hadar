#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import numpy as np
import pandas as pd

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Union, List

from hadar.optimizer.utils import JSON

T = TypeVar("T")


class NumericalValue(JSON, ABC, Generic[T]):
    """
    Interface to handle numerical value in study
    """

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

    def __le__(self, other) -> bool:
        return not self.__gt__(other)

    @abstractmethod
    def __gt__(self, other) -> bool:
        pass

    def __ge__(self, other) -> bool:
        return not self.__lt__(other)

    @abstractmethod
    def flatten(self) -> np.ndarray:
        """
        flat data into 1D matrix.
        :return: [v[0, 0], v[0, 1], v[0, 2], ..., v[1, i], v[2, i], ..., v[j, i])
        """
        pass


class ScalarNumericalValue(NumericalValue[float]):
    """
    Implement one scalar numerical value i.e. float or int
    """

    def __getitem__(self, item) -> float:
        i, j = item
        if i >= self.nb_scn:
            raise IndexError(
                "There are %d scenario you ask the %dth" % (self.nb_scn, i)
            )
        if j >= self.horizon:
            raise IndexError(
                "There are %d time step you ask the %dth" % (self.horizon, j)
            )
        return self.value

    def __lt__(self, other):
        return self.value < other

    def __gt__(self, other):
        return self.value > other

    def flatten(self) -> np.ndarray:
        return np.ones(self.horizon * self.nb_scn) * self.value

    @staticmethod
    def from_json(dict):
        pass  # not used. Deserialization is done by study elements themself


class NumpyNumericalValue(NumericalValue[np.ndarray], ABC):
    """
    Half-implementation with numpy array as numerical value. Implement only compare methods.
    """

    def __lt__(self, other) -> bool:
        return np.all(self.value < other)

    def __gt__(self, other) -> bool:
        return np.all(self.value > other)


class MatrixNumericalValue(NumpyNumericalValue):
    """
    Implementation with complex matrix with shape (nb_scn, horizon)
    """

    def __getitem__(self, item) -> float:
        i, j = item
        return self.value[i, j]

    def flatten(self) -> np.ndarray:
        return self.value.flatten()

    @staticmethod
    def from_json(dict):
        pass  # not used. Deserialization is done by study elements themself


class RowNumericValue(NumpyNumericalValue):
    """
    Implementation with one scenario wiht shape (horizon, ).
    """

    def __getitem__(self, item) -> float:
        i, j = item
        if i >= self.nb_scn:
            raise IndexError(
                "There are %d scenario you ask the %dth" % (self.nb_scn, i)
            )
        return self.value[j]

    def flatten(self) -> np.ndarray:
        return np.tile(self.value, self.nb_scn)

    @staticmethod
    def from_json(dict):
        pass  # not used. Deserialization is done by study elements themself


class ColumnNumericValue(NumpyNumericalValue):
    """
    Implementation with one time step by scenario with shape (nb_scn, 1)
    """

    def __getitem__(self, item) -> float:
        i, j = item
        if j >= self.horizon:
            raise IndexError(
                "There are %d time step you ask the %dth" % (self.horizon, j)
            )
        return self.value[i, 0]

    def flatten(self) -> np.ndarray:
        return np.repeat(self.value.flatten(), self.horizon)

    @staticmethod
    def from_json(dict):
        pass  # not used. Deserialization is done by study elements themself


class NumericalValueFactory:
    def __init__(self, horizon: int, nb_scn: int):
        self.horizon = horizon
        self.nb_scn = nb_scn

    def __eq__(self, other):
        if not isinstance(other, NumericalValueFactory):
            return False
        return other.horizon == self.horizon and other.nb_scn == self.nb_scn

    def create(
        self, value: Union[float, List[float], str, np.ndarray, NumericalValue]
    ) -> NumericalValue:
        if isinstance(value, NumericalValue):
            return value

        # If data come from json serialized dictionary, use 'value' key as input
        if isinstance(value, dict) and "value" in value:
            value = value["value"]

        # If data is just a scalar
        if type(value) in [float, int, complex]:
            return ScalarNumericalValue(
                value=value, horizon=self.horizon, nb_scn=self.nb_scn
            )

        # If data is list or pandas object convert to numpy array
        if type(value) in [List, list, pd.DataFrame, pd.Series]:
            value = np.array(value)

        if isinstance(value, np.ndarray):
            # If scenario are not provided copy timeseries for each scenario
            if value.shape == (self.horizon,):
                return RowNumericValue(
                    value=value, horizon=self.horizon, nb_scn=self.nb_scn
                )

            # If horizon are not provide extend each scenario to full horizon
            if value.shape == (self.nb_scn, 1):
                return ColumnNumericValue(
                    value=value, horizon=self.horizon, nb_scn=self.nb_scn
                )

            # If perfect size
            if value.shape == (self.nb_scn, self.horizon):
                return MatrixNumericalValue(
                    value=value, horizon=self.horizon, nb_scn=self.nb_scn
                )

            # If any size pattern matches, raise error on quantity size given
            horizon_given = value.shape[0] if len(value.shape) == 1 else value.shape[1]
            sc_given = 1 if len(value.shape) == 1 else value.shape[0]
            raise ValueError(
                "Array must be: a number, an array like (horizon, ) or (nb_scn, 1) or (nb_scn, horizon). "
                "In your case horizon specified is %d and actual is %d. "
                "And nb_scn specified %d is whereas actual is %d"
                % (self.horizon, horizon_given, self.nb_scn, sc_given)
            )

        raise ValueError("Wrong source data for numerical value")
