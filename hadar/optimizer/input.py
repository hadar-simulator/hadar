#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

from typing import List, Union, Dict

import numpy as np


__all__ = ['Consumption', 'Link', 'Production', 'Storage', 'InputNode', 'Study',
           'NetworkFluentAPISelector', 'NodeFluentAPISelector']


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

    def __init__(self, quantity: Union[List, np.ndarray, float], cost: Union[List, np.ndarray, float], name: str = ''):
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
    def __init__(self, quantity: Union[List, np.ndarray, float], cost: Union[List, np.ndarray, float], name: str = 'in'):
        """
        Create production

        :param quantity: capacity production
        :param cost: cost of use
        :param name: name of production (unique for each node)
        """
        self.name = name
        self.cost = cost
        self.quantity = np.array(quantity)


class Storage(DTO):
    """
    Storage element
    """
    def __init__(self, name, capacity: int, flow_in: float, flow_out: float,
                 cost_in: Union[List, np.ndarray, float], cost_out: Union[List, np.ndarray, float],
                 init_capacity: int = 0,  eff: float = 1):
        """
        Create storage.

        :param capacity: maximum storage capacity (like of many quantity to use inside storage)
        :param flow_in: max flow into storage during on time step
        :param flow_out: max flow out storage during on time step
        :param cost_in: unit cost of use for input flow
        :param cost_out: unit cost of used for output flow
        :param init_capacity: initial capacity level
        :param eff: storage efficient. (applied on input flow stored)
        """
        self.name = name
        self.capacity = capacity
        self.flow_in = flow_in
        self.flow_out = flow_out
        self.cost_in = np.array(cost_in)
        self.cost_out = np.array(cost_out)
        self.init_capacity = init_capacity
        self.eff = eff


class Link(DTO):
    """
    Link element
    """
    def __init__(self, dest: str, quantity: Union[List, np.ndarray, float], cost: Union[List, np.ndarray, float]):
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
    def __init__(self, consumptions: List[Consumption], productions: List[Production],
                 storages: List[Storage], links: List[Link]):
        """
        Create node element.

        :param consumptions: list of consumptions inside node
        :param productions: list of productions inside node
        :param storages: list of storages inside node
        :param links: list of links inside node
        """
        self.consumptions = consumptions
        self.productions = productions
        self.storages = storages
        self.links = links


class InputNetwork(DTO):
    """
    Network element
    """
    def __init__(self, nodes: Dict[str, InputNode] = None):
        """
        Create network element

        :param nodes: nodes list inside network
        """
        self.nodes = nodes if nodes else {}


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

        self.networks = dict()
        self.horizon = horizon
        self.nb_scn = nb_scn

    def network(self, name='default'):
        """
        Entry point to create study with the fluent api.

        :return:
        """
        self.add_network(name)
        return NetworkFluentAPISelector(selector={'network': name}, study=self)

    def add_link(self, network: str, src: str, dest: str, cost: int, quantity: Union[List[float], np.ndarray, float]):
        """
        Add a link inside network.

        :param network: network where nodes belong
        :param src: source node name
        :param dest: destination node name
        :param cost: cost of use
        :param quantity: transfer capacity
        :return:
        """
        if src not in self.networks[network].nodes.keys():
            raise ValueError('link source must be a valid node')
        if dest not in self.networks[network].nodes.keys():
            raise ValueError('link destination must be a valid node')
        if dest in [l.dest for l in self.networks[network].nodes[src].links]:
            raise ValueError('link destination must be unique on a node')

        quantity = self._standardize_array(quantity)
        if np.any(quantity < 0):
            raise ValueError('Link quantity must be positive')

        cost = self._standardize_array(cost)
        self.networks[network].nodes[src].links.append(Link(dest=dest, quantity=quantity, cost=cost))

        return self

    def add_network(self, network: str):
        if network not in self.networks.keys():
            self.networks[network] = InputNetwork()

    def add_node(self, network: str, node: str):
        if node not in self.networks[network].nodes.keys():
            self.networks[network].nodes[node] = InputNode(consumptions=[], productions=[], links=[], storages=[])

    def _add_production(self, network: str, node: str, prod: Production):
        if prod.name in [p.name for p in self.networks[network].nodes[node].productions]:
            raise ValueError('production name must be unique on a node')

        prod.quantity = self._standardize_array(prod.quantity)
        if np.any(prod.quantity < 0):
            raise ValueError('Production quantity must be positive')

        prod.cost = self._standardize_array(prod.cost)
        self.networks[network].nodes[node].productions.append(prod)

    def _add_consumption(self, network: str, node: str, cons: Consumption):
        if cons.name in [c.name for c in self.networks[network].nodes[node].consumptions]:
            raise ValueError('consumption name must be unique on a node')

        cons.quantity = self._standardize_array(cons.quantity)
        if np.any(cons.quantity < 0):
            raise ValueError('Consumption quantity must be positive')

        cons.cost = self._standardize_array(cons.cost)
        self.networks[network].nodes[node].consumptions.append(cons)

    def _add_storage(self, network: str, node: str, store: Storage):
        if store.name in [s.name for s in self.networks[network].nodes[node].storages]:
            raise ValueError('storage name must be unique on a node')
        if store.flow_in < 0 or store.flow_out < 0:
            raise ValueError('storage flow must be positive')
        if store.capacity < 0 or store.init_capacity < 0:
            raise ValueError('storage capacities must be positive')
        if store.eff < 0:
            raise ValueError('storage efficiency must be positive')

        store.cost_in = self._standardize_array(store.cost_in)
        store.cost_out = self._standardize_array(store.cost_out)
        self.networks[network].nodes[node].storages.append(store)

    def _standardize_array(self, array: Union[List[float], np.ndarray, float]) -> np.ndarray:
        array = np.array(array)

        # If scenario and horizon are not provided, expend on both side
        if array.size == 1:
            return np.ones((self.nb_scn, self.horizon)) * array

        # If scenario are not provided copy timeseries for each scenario
        if array.shape == (self.horizon,):
            return np.tile(array, (self.nb_scn, 1))

        # If horizon are not provide extend each scenario to full horizon
        if array.shape == (self.nb_scn, 1):
            return np.tile(array, self.horizon)

        # If perfect size
        if array.shape == (self.nb_scn, self.horizon):
            return array

        # If any size pattern matches, raise error on quantity size given
        horizon_given = array.shape[0] if len(array.shape) == 1 else array.shape[1]
        sc_given = 1 if len(array.shape) == 1 else array.shape[0]
        raise ValueError('Array must be: a number, an array like (horizon, ) or (nb_scn, 1) or (nb_scn, horizon). '
                         'In your case horizon specified is %d and actual is %d. '
                         'And nb_scn specified %d is whereas actual is %d' %
                         (self.horizon, horizon_given, self.nb_scn, sc_given))


class NetworkFluentAPISelector:
    """
    Network level of Fluent API Selector.
    """
    def __init__(self, study, selector):
        self.study = study
        self.selector = selector

    def node(self, name):
        """
        Go to node level.

        :param name: node to select when changing level
        :return: NodeFluentAPISelector initialized
        """
        self.selector['node'] = name
        self.study.add_node(network=self.selector['network'], node=name)
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
        self.study.add_link(network=self.selector['network'], src=src, dest=dest, cost=cost, quantity=quantity)
        return NetworkFluentAPISelector(self.study, self.selector)

    def network(self, name='default'):
        """
        Go to network level.

        :param name: network level, 'default' as default name
        :return: NetworkAPISelector with selector set to 'default'
        """
        self.study.add_network(name)
        return NetworkFluentAPISelector(selector={'network': name}, study=self.study)

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
        self.study._add_consumption(network=self.selector['network'], node=self.selector['node'],
                                    cons=Consumption(name=name, cost=cost, quantity=quantity))
        return self

    def production(self, name: str, cost: int, quantity: Union[List, np.ndarray, float]):
        """
        Add production on node.

        :param name: production name
        :param cost: unit cost of use
        :param quantity: available capacities
        :return: NodeFluentAPISelector with new production
        """
        self.study._add_production(network=self.selector['network'], node=self.selector['node'],
                                   prod=Production(name=name, cost=cost, quantity=quantity))
        return self

    def storage(self, name, capacity: int, flow_in: float, flow_out: float,
                 cost_in: Union[List, np.ndarray, float], cost_out: Union[List, np.ndarray, float],
                 init_capacity: int = 0,  eff: int = 1):

        self.study._add_storage(network=self.selector['network'], node=self.selector['node'],
                                store=Storage(name=name, capacity=capacity, flow_in=flow_in, flow_out=flow_out,
                                              cost_in=cost_in, cost_out=cost_out, init_capacity=init_capacity, eff=eff))
        return self

    def node(self, name):
        """
        Go to different node level.

        :param name: new node level
        :return: NodeFluentAPISelector
        """
        return NetworkFluentAPISelector(self.study, self.selector).node(name)

    def link(self, src: str, dest: str, cost: int, quantity: Union[List, np.ndarray, float]):
        """
        Add a link on network.

        :param src: node source
        :param dest: node destination
        :param cost: unit cost transfer
        :param quantity: available capacity

        :return: NetworkAPISelector with new link.
        """
        return NetworkFluentAPISelector(self.study, self.selector).link(src=src, dest=dest, cost=cost, quantity=quantity)

    def network(self, name='default'):
        """
        Go to network level.

        :param name: network level, 'default' as default name
        :return: NetworkAPISelector with selector set to 'default'
        """
        self.study.add_network(name)
        return NetworkFluentAPISelector(selector={'network': name}, study=self.study)

    def build(self):
        """
        Build study.

        :return: study
        """
        return self.study
