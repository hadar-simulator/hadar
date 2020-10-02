#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
from abc import ABC, abstractmethod
import numpy as np


class DTO:
    """
    Implement basic method for DTO objects
    """

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.__dict__ == other.__dict__

    def __str__(self):
        return "{}({})".format(
            type(self).__name__,
            ", ".join(
                [
                    "{}={}".format(k, str(self.__dict__[k]))
                    for k in sorted(self.__dict__)
                ]
            ),
        )

    def __repr__(self):
        return self.__str__()


class JSON(DTO, ABC):
    """
    Object to be serializer by json
    """

    @staticmethod
    def convert(value):
        if isinstance(value, JSON):
            return value.to_json()
        elif isinstance(value, dict):
            return {k: JSON.convert(v) for k, v in value.items()}
        elif isinstance(value, list) or isinstance(value, tuple):
            return [JSON.convert(v) for v in value]
        elif isinstance(value, np.int64):
            return int(value)
        elif isinstance(value, np.float64):
            return float(value)
        elif isinstance(value, np.ndarray):
            return value.tolist()
        return value

    def to_json(self):
        return {k: JSON.convert(v) for k, v in self.__dict__.items()}

    @staticmethod
    @abstractmethod
    def from_json(dict, factory=None):
        pass
