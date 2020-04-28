#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

from typing import List, Union

import numpy as np


__all__ = ['Consumption', 'Border', 'Production', 'InputNode', 'Study']


class DTO:
    """
    Implement basic method for DTO objects
    """
    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.__dict__ == other.__dict__

    def __str__(self):
        return "{}({})".format(type(self).__name__, ", ".join(["{}={}".format(k, str(self.__dict__[k])) for k in sorted(self.__dict__)]))

    def __repr__(self):
        return self.__str__()


class Consumption(DTO):
    """
    Consumption element.
    """

    def __init__(self, quantity: Union[List[float], np.ndarray, float], cost: int = 0, type: str = ''):
        """
        Create consumption.

        :param quantity: quantity to match
        :param cost: cost of unavailability
        :param type: type of consumption (unique for each node)
        """
        self.cost = cost
        self.quantity = np.array(quantity)
        self.type = type


class Production(DTO):
    """
    Production element
    """
    def __init__(self, quantity: Union[List[float], np.ndarray, float], cost: int = 0, type: str = 'in'):
        """
        Create production

        :param quantity: capacity production
        :param cost: cost of use
        :param type: type of production (unique for each node)
        """
        self.type = type
        self.cost = cost
        self.quantity = np.array(quantity)


class Border(DTO):
    """
    Border element
    """
    def __init__(self, dest: str, quantity: Union[List[float], np.ndarray, float], cost: int = 0):
        """
        Create border.

        :param dest: node name destination (to export)
        :param quantity: transfer capacity
        :param cost: cost of use
        """
        self.dest = dest
        self.quantity = np.array(quantity)
        self.cost = cost


class InputNode(DTO):
    """
    Node element
    """
    def __init__(self, consumptions: List[Consumption], productions: List[Production], borders: List[Border]):
        """
        Create node element.

        :param consumptions: list of consumptions inside node
        :param productions: list of productions inside node
        :param borders: list of borders inside node
        """
        self.consumptions = consumptions
        self.productions = productions
        self.borders = borders


class Study(DTO):
    """
    Main object to facilitate to build a study
    """

    def __init__(self, node_names: List[str], horizon: int, nb_scn: int = 1):
        """
        Instance study.

        :param node_names: list of node names inside network.
        :param horizon: simulation time horizon (i.e. number of time step in simulation)
        :param nb_scn: number of scenarios in study. Default is 1.
        """
        if len(node_names) > len(set(node_names)):
            raise ValueError('some nodes are not unique')

        self._nodes = {name: InputNode(consumptions=[], productions=[], borders=[]) for name in node_names}
        self.horizon = horizon
        self.nb_scn = nb_scn


    @property
    def nodes(self):
        return self._nodes

    def add_on_node(self, node: str, data=Union[Production, Consumption, Border]):
        """
        Attach a production or consumption into a node.

        :param node: node name to attach
        :param data: consumption or production to attach
        :return:
        """
        if node not in self._nodes.keys():
            raise ValueError('Node "{}" is not in available nodes'.format(node))

        if isinstance(data, Production):
            self._add_production(node, data)

        elif isinstance(data, Consumption):
            self._add_consumption(node, data)

        return self

    def add_border(self, src: str, dest: str, cost: int, quantity: Union[List[float], np.ndarray, float]):
        """
        Add a border inside network.

        :param src: source node name
        :param dest: destination node name
        :param cost: cost of use
        :param quantity: transfer capacity
        :return:
        """
        if cost < 0:
            raise ValueError('border cost must be positive')
        if dest not in self._nodes.keys():
            raise ValueError('border destination must be a valid node')
        if dest in [b.dest for b in self._nodes[src].borders]:
            raise ValueError('border destination must be unique on a node')

        quantity = self._validate_quantity(quantity)
        self._nodes[src].borders.append(Border(dest=dest, quantity=quantity, cost=cost))

        return self

    def _add_production(self, node: str, prod: Production):
        if prod.cost < 0:
            raise ValueError('production cost must be positive')
        if prod.type in [p.type for p in self._nodes[node].productions]:
            raise ValueError('production type must be unique on a node')

        prod.quantity = self._validate_quantity(prod.quantity)
        self._nodes[node].productions.append(prod)

    def _add_consumption(self, node: str, cons: Consumption):
        if cons.cost < 0:
            raise ValueError('consumption cost must be positive')
        if cons.type in [c.type for c in self._nodes[node].consumptions]:
            raise ValueError('consumption type must be unique on a node')

        cons.quantity = self._validate_quantity(cons.quantity)
        self._nodes[node].consumptions.append(cons)

    def _validate_quantity(self, quantity: Union[List[float], np.ndarray, float]) -> np.ndarray:
        quantity = np.array(quantity)

        # If quantity are negative raise error:
        if np.any(quantity < 0):
            raise ValueError('Quantity must be positive')

        # If scenario and horizon are not provided, expend on both side
        if quantity.size == 1:
            return np.ones((self.nb_scn, self.horizon)) * quantity

        # If scenario are not provided copy timeseries for each scenario
        if quantity.shape == (self.horizon,):
            return np.tile(quantity, (self.nb_scn, 1))

        # If horizon are not provide extend each scenario to full horizon
        if quantity.shape == (self.nb_scn, 1):
            return np.tile(quantity, self.horizon)

        # If perfect size
        if quantity.shape == (self.nb_scn, self.horizon):
            return quantity

        # If any size pattern matches, raise error on quantity size given
        horizon_given = quantity.shape[0] if len(quantity.shape) == 1 else quantity.shape[1]
        sc_given = 1 if len(quantity.shape) == 1 else quantity.shape[0]
        raise ValueError('Quantity must be: a number, an array like (horizon, ) or (nb_scn, 1) or (nb_scn, horizon). '
                         'In your case horizon specified is %d and actual is %d' %
                         (self.horizon, horizon_given))
