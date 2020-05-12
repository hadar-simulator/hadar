#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

from abc import ABC, abstractmethod


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