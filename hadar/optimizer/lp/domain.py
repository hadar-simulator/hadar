#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import numpy as np
from typing import List, Union, Dict

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


class LPStorage(DTO):
    """
    Storage element
    """
    def __init__(self, name, capacity: int, var_capacity: Union[Variable, SerializableVariable],
                 flow_in: float, var_flow_in: Union[Variable, SerializableVariable],
                 flow_out: float, var_flow_out: Union[Variable, SerializableVariable],
                 cost: float = 0, init_capacity: int = 0,  eff: float = .99):
        """
        Create storage.

        :param capacity: maximum storage capacity (like of many quantity to use inside storage)
        :param var_capacity: solver variable for capacity
        :param flow_in: max flow into storage during on time step
        :param var_flow_in: solver variable for var_flow_in
        :param flow_out: max flow out storage during on time step
        :param var_flow_out: solver variable for var_flow_out
        :param cost: unit cost of storage at each time-step. default 0
        :param init_capacity: initial capacity level
        :param eff: storage efficient. (applied on input flow stored)
        """
        self.name = name
        self.capacity = capacity
        self.var_capacity = var_capacity
        self.flow_in = flow_in
        self.var_flow_in = var_flow_in
        self.flow_out = flow_out
        self.var_flow_out = var_flow_out
        self.cost = cost
        self.init_capacity = init_capacity
        self.eff = eff

    def __reduce__(self):
        """
        Help pickle to serialize object, specially variable object
        :return: (constructor, values...)
        """
        return self.__class__, (self.name, self.capacity, SerializableVariable(self.var_capacity),
                                self.flow_in, SerializableVariable(self.var_flow_in),
                                self.flow_out, SerializableVariable(self.var_flow_out),
                                self.cost, self.init_capacity, self.eff)


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
    def __init__(self, consumptions: List[LPConsumption], productions: List[LPProduction],
                 storages: List[LPStorage], links: List[LPLink]):
        """
        Instance node.

        :param consumptions: consumptions list
        :param productions: productions list
        :param links: links list
        """
        self.consumptions = consumptions
        self.productions = productions
        self.storages = storages
        self.links = links


class LPNetwork(DTO):
    """
    Network element for linear programming
    """

    def __init__(self, nodes: Dict[str, LPNode]):
        """
        Instance network.

        :param nodes: nodes belong to network name as key, LPNode as value
        """
        self.nodes = nodes
