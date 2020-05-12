#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import numpy as np
from typing import List, Union

from ortools.linear_solver.pywraplp import Variable

from hadar.optimizer.input import DTO


class SerializableVariable(DTO):
    def __init__(self, var: Variable):
        self.val = var.solution_value()

    def solution_value(self):
        return self.val


class LPConsumption(DTO):
    """
    Consumption element for linear programming.
    """

    def __init__(self, quantity: int, variable: Union[Variable, SerializableVariable], cost: float = 0, name: str = ''):
        """
        Instance consumption.

        :param quantity: quantity to match
        :param variable: ortools variables. represent a loss of load inside equation
        :param cost: unavailability cost
        :param name: consumption name
        """
        self.cost = cost
        self.quantity = quantity
        self.name = name
        self.variable = variable

    def __reduce__(self):
        """
        Help pickle to serialize object, specially variable object
        :return: (constructor, values...)
        """
        return self.__class__, (self.quantity, SerializableVariable(self.variable), self.cost, self.name)

class LPProduction(DTO):
    """
    Production element for linear programming.
    """

    def __init__(self, quantity: int, variable: Union[Variable, SerializableVariable], cost: float = 0, name: str = 'in'):
        """
        Instance production.

        :param quantity: production capacity
        :param variable: ortools variables. Represent production used inside equation
        :param cost: cost of use
        :param name: production name
        """
        self.name = name
        self.cost = cost
        self.variable = variable
        self.quantity = quantity

    def __reduce__(self):
        """
        Help pickle to serialize object, specially variable object
        :return: (constructor, values...)
        """
        return self.__class__, (self.quantity, SerializableVariable(self.variable), self.cost, self.name)


class LPLink(DTO):
    """
    Link element for linear programming
    """
    def __init__(self, src: str, dest: str, quantity: int, variable: Union[Variable, SerializableVariable], cost: float = 0):
        """
        Instance Link.

        :param src: node source name
        :param dest: node destination name
        :param quantity: link capacity
        :param variable: ortools variables. Represent border used inside equation
        :param cost: cost of use
        """
        self.src = src
        self.dest = dest
        self.quantity = quantity
        self.variable = variable
        self.cost = cost

    def __reduce__(self):
        """
        Help pickle to serialize object, specially variable object
        :return: (constructor, values...)
        """
        return self.__class__, (self.src, self.dest, self.quantity, SerializableVariable(self.variable), self.cost)


class LPNode(DTO):
    """
    Node element for linear programming
    """
    def __init__(self, consumptions: List[LPConsumption], productions: List[LPProduction], links: List[LPLink]):
        """
        Instance node.

        :param consumptions: consumptions list
        :param productions: productions list
        :param links: links list
        """
        self.consumptions = consumptions
        self.productions = productions
        self.links = links