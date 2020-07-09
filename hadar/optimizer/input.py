#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

from typing import List, Union, Dict

import numpy as np


__all__ = ['Consumption', 'Link', 'Production', 'InputNode', 'Study', 'NetworkFluentAPISelector', 'NodeFluentAPISelector']


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

    def __init__(self, quantity: Union[List, np.ndarray, float], cost: int = 0, name: str = ''):
        """
        Create consumption.

        :param quantity: quantity to match
        :param cost: cost of unavailability
        :param name: name of consumption (unique for each node)
        """
        self.cost = cost
        self.quantity = np.array(quantity)
        self.name = name


class Production(DTO):
    """
    Production element
    """
    def __init__(self, quantity: Union[List, np.ndarray, float], cost: int = 0, name: str = 'in'):
        """
        Create production

        :param quantity: capacity production
        :param cost: cost of use
        :param name: name of production (unique for each node)
        """
        self.name = name
        self.cost = cost
        self.quantity = np.array(quantity)


class Link(DTO):
    """
    Link element
    """
    def __init__(self, dest: str, quantity: Union[List, np.ndarray, float], cost: int = 0):
        """
        Create link.

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
    def __init__(self, consumptions: List[Consumption], productions: List[Production], links: List[Link]):
        """
        Create node element.

        :param consumptions: list of consumptions inside node
        :param productions: list of productions inside node
        :param links: list of links inside node
        """
        self.consumptions = consumptions
        self.productions = productions
        self.links = links


class Study(DTO):
    """
    Main object to facilitate to build a study
    """

    def __init__(self, horizon: int, nb_scn: int = 1):
        """
        Instance study.

        :param horizon: simulation time horizon (i.e. number of time step in simulation)
        :param nb_scn: number of scenarios in study. Default is 1.
        """

        self.nodes = dict()
        self.horizon = horizon
        self.nb_scn = nb_scn

    def network(self):
        """
        Entry point to create study with the fluent api.

        :return:
        """
        return NetworkFluentAPISelector(study=self)

    def add_link(self, src: str, dest: str, cost: int, quantity: Union[List[float], np.ndarray, float]):
        """
        Add a link inside network.

        :param src: source node name
        :param dest: destination node name
        :param cost: cost of use
        :param quantity: transfer capacity
        :return:
        """
        if cost < 0:
            raise ValueError('link cost must be positive')
        if src not in self.nodes.keys():
            raise ValueError('link source must be a valid node')
        if dest not in self.nodes.keys():
            raise ValueError('link destination must be a valid node')
        if dest in [l.dest for l in self.nodes[src].links]:
            raise ValueError('link destination must be unique on a node')

        quantity = self._validate_quantity(quantity)
        self.nodes[src].links.append(Link(dest=dest, quantity=quantity, cost=cost))

        return self

    def add_node(self, node):
        if node not in self.nodes.keys():
            self.nodes[node] = InputNode(consumptions=[], productions=[], links=[])

    def _add_production(self, node: str, prod: Production):
        if prod.cost < 0:
            raise ValueError('production cost must be positive')
        if prod.name in [p.name for p in self.nodes[node].productions]:
            raise ValueError('production name must be unique on a node')

        prod.quantity = self._validate_quantity(prod.quantity)
        self.nodes[node].productions.append(prod)

    def _add_consumption(self, node: str, cons: Consumption):
        if cons.cost < 0:
            raise ValueError('consumption cost must be positive')
        if cons.name in [c.name for c in self.nodes[node].consumptions]:
            raise ValueError('consumption name must be unique on a node')

        cons.quantity = self._validate_quantity(cons.quantity)
        self.nodes[node].consumptions.append(cons)

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
                         'In your case horizon specified is %d and actual is %d. '
                         'And nb_scn specified %d is whereas actual is %d' %
                         (self.horizon, horizon_given, self.nb_scn, sc_given))


class NetworkFluentAPISelector:
    """
    Network level of Fluent API Selector.
    """
    def __init__(self, study):
        self.study = study
        self.selector = dict()

    def node(self, name):
        """
        Go to node level.

        :param name: node to select when changing level
        :return: NodeFluentAPISelector initialized
        """
        self.selector['node'] = name
        self.study.add_node(name)
        return NodeFluentAPISelector(self.study, self.selector)

    def link(self, src: str, dest: str, cost: int, quantity: Union[List, np.ndarray, float]):
        """
        Add a link on network.

        :param src: node source
        :param dest: node destination
        :param cost: unit cost transfer
        :param quantity: available capacity

        :return: NetworkAPISelector with new link.
        """
        self.study.add_link(src=src, dest=dest, cost=cost, quantity=quantity)
        return NetworkFluentAPISelector(self.study)

    def build(self):
        """
        Build study.

        :return: return study
        """
        return self.study


class NodeFluentAPISelector:
    """
    Node level of Fluent API Selector
    """
    def __init__(self, study, selector):
        self.study = study
        self.selector = selector

    def consumption(self, name: str, cost: int, quantity: Union[List, np.ndarray, float]):
        """
        Add consumption on node.

        :param name: consumption name
        :param cost: cost of unsuitability
        :param quantity: consumption to sustain
        :return: NodeFluentAPISelector with new consumption
        """
        self.study._add_consumption(node=self.selector['node'], cons=Consumption(name=name, cost=cost, quantity=quantity))
        return self

    def production(self, name: str, cost: int, quantity: Union[List, np.ndarray, float]):
        """
        Add production on node.

        :param name: production name
        :param cost: unit cost of use
        :param quantity: available capacities
        :return: NodeFluentAPISelector with new production
        """
        self.study._add_production(node=self.selector['node'], prod=Production(name=name, cost=cost, quantity=quantity))
        return self

    def node(self, name):
        """
        Go to different node level.

        :param name: new node level
        :return: NodeFluentAPISelector
        """
        return NetworkFluentAPISelector(self.study).node(name)

    def link(self, src: str, dest: str, cost: int, quantity: Union[List, np.ndarray, float]):
        """
        Add a link on network.

        :param src: node source
        :param dest: node destination
        :param cost: unit cost transfer
        :param quantity: available capacity

        :return: NetworkAPISelector with new link.
        """
        return NetworkFluentAPISelector(self.study).link(src=src, dest=dest, cost=cost, quantity=quantity)

    def build(self):
        """
        Build study.

        :return: study
        """
        return self.study
