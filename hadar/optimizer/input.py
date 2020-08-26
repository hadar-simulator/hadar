#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import List, Union, Dict, Tuple

import numpy as np

__all__ = ['Consumption', 'Link', 'Production', 'Storage', 'Converter', 'InputNetwork', 'InputNode', 'Study',
           'NetworkFluentAPISelector', 'NodeFluentAPISelector']

import hadar


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


class JSON(DTO, ABC):

    def to_json(self):
        def convert(value):
            if isinstance(value, JSON):
                return value.to_json()
            elif isinstance(value, dict):
                return {k: convert(v) for k, v in value.items()}
            elif isinstance(value, list) or isinstance(value, tuple):
                return [convert(v) for v in value]
            elif isinstance(value, np.ndarray):
                return value.tolist()
            return value

        return {k: convert(v) for k, v in self.__dict__.items()}

    @staticmethod
    @abstractmethod
    def from_json(dict):
        pass


class Consumption(JSON):
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
        self.cost = np.array(cost)
        self.quantity = np.array(quantity)
        self.name = name

    @staticmethod
    def from_json(dict):
        return Consumption(**dict)


class Production(JSON):
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
        self.cost = np.array(cost)
        self.quantity = np.array(quantity)

    @staticmethod
    def from_json(dict):
        return Production(**dict)


class Storage(JSON):
    """
    Storage element
    """
    def __init__(self, name, capacity: int, flow_in: float, flow_out: float, cost: float = 0,
                 init_capacity: int = 0,  eff: float = 0.99):
        """
        Create storage.

        :param capacity: maximum storage capacity (like of many quantity to use inside storage)
        :param flow_in: max flow into storage during on time step
        :param flow_out: max flow out storage during on time step
        :param cost: unit cost of storage at each time-step. default 0
        :param init_capacity: initial capacity level. default 0
        :param eff: storage efficient (applied on input flow stored). default 0.99
        """
        self.name = name
        self.capacity = capacity
        self.flow_in = flow_in
        self.flow_out = flow_out
        self.cost = cost
        self.init_capacity = init_capacity
        self.eff = eff

    @staticmethod
    def from_json(dict):
        return Storage(**dict)


class Link(JSON):
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
        self.cost = np.array(cost)

    @staticmethod
    def from_json(dict):
        return Link(**dict)


class Converter(JSON):
    """
    Converter element
    """
    def __init__(self, name: str, src_ratios: Dict[Tuple[str, str], float], dest_network: str, dest_node: str,
                 cost: float, max: float,):
        """
        Create converter.

        :param name: converter name

        :param src_ratios: ration conversion for each sources. data={(network, node): ratio}
        :param dest_network: destination network
        :param dest_node: dsetination node
        :param cost: cost applied on quantity through converter
        :param max: max output flow
        """
        self.name = name
        self.src_ratios = src_ratios
        self.dest_network = dest_network
        self.dest_node = dest_node
        self.cost = cost
        self.max = max

    def to_json(self) -> dict:
        dict = deepcopy(self.__dict__)
        # src_ratios has a tuple of two string as key. These forbidden by JSON.
        # Therefore when serialized we join these two strings with '::' to create on string as key
        # Ex: ('elec', 'a') --> 'elec::a'
        dict['src_ratios'] = {'::'.join(k): v for k, v in self.src_ratios.items()}
        return dict

    @staticmethod
    def from_json(dict: dict):
        # When deserialize, we need to split key string of src_network.
        # JSON doesn't accept tuple as key, so two string was joined for serialization
        # Ex: 'elec::a' -> ('elec', 'a')
        dict['src_ratios'] = {tuple(k.split('::')): v for k, v in dict['src_ratios'].items()}
        return Converter(**dict)


class InputNode(JSON):
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

    @staticmethod
    def from_json(dict):
        dict['consumptions'] = [Consumption.from_json(v) for v in dict['consumptions']]
        dict['productions'] = [Production.from_json(v) for v in dict['productions']]
        dict['storages'] = [Storage.from_json(v) for v in dict['storages']]
        dict['links'] = [Link.from_json(v) for v in dict['links']]
        return InputNode(**dict)


class InputNetwork(JSON):
    """
    Network element
    """
    def __init__(self, nodes: Dict[str, InputNode] = None):
        """
        Create network element

        :param nodes: nodes list inside network
        """
        self.nodes = nodes if nodes else {}

    @staticmethod
    def from_json(dict):
        dict['nodes'] = {k: InputNode.from_json(v) for k, v in dict['nodes'].items()}
        return InputNetwork(**dict)


class Study(JSON):
    """
    Main object to facilitate to build a study
    """

    def __init__(self, horizon: int, nb_scn: int = 1, version: str = None):
        """
        Instance study.

        :param horizon: simulation time horizon (i.e. number of time step in simulation)
        :param nb_scn: number of scenarios in study. Default is 1.
        """
        self.version = version or hadar.__version__
        self.networks = dict()
        self.converters = dict()
        self.horizon = horizon
        self.nb_scn = nb_scn

    @staticmethod
    def from_json(dict):
        dict = deepcopy(dict)
        study = Study(horizon=dict['horizon'], nb_scn=dict['nb_scn'], version=dict['version'])
        study.networks = {k: InputNetwork.from_json(v) for k, v in dict['networks'].items()}
        study.converters = {k: Converter.from_json(v) for k, v in dict['converters'].items()}
        return study

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
        if store.eff < 0 or store.eff > 1:
            raise ValueError('storage efficiency must be in ]0, 1[')

        self.networks[network].nodes[node].storages.append(store)

    def _add_converter(self, name: str):
        if name not in [v for v in self.converters]:
            self.converters[name] = Converter(name=name, src_ratios={}, dest_network='',
                                              dest_node='', cost=0, max=0)

    def _add_converter_src(self, name: str, network: str, node: str, ratio: float):
        if (network, node) in self.converters[name].src_ratios:
            raise ValueError('converter input already has node %s on network %s' % (node, network))

        self.converters[name].src_ratios[(network, node)] = ratio

    def _set_converter_dest(self, name: str, network: str, node: str, cost: float, max: float):
        if self.converters[name].dest_network and self.converters[name].dest_node:
            raise ValueError('converter has already output set')
        if network not in self.networks or node not in self.networks[network].nodes.keys():
            raise ValueError('Node %s is not present in network %s' % (node, network))

        self.converters[name].dest_network = network
        self.converters[name].dest_node = node
        self.converters[name].cost = cost
        self.converters[name].max = max

    def _standardize_array(self, array: Union[List[float], np.ndarray, float]) -> np.ndarray:
        array = np.array(array, dtype=float)

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

    def converter(self, name: str, to_network: str, to_node: str, max: float, cost: float = 0):
        """
        Add a converter element.

        :param name: converter name
        :param to_network: converter output network
        :param to_node: converter output node on network
        :param max: maximum quantity from converter
        :param cost: cost for each quantity produce by converter
        :return:
        """
        self.study._add_converter(name=name)
        self.study._set_converter_dest(name=name, network=to_network, node=to_node, cost=cost, max=max)
        return NetworkFluentAPISelector(selector={}, study=self.study)

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

    def storage(self, name, capacity: int, flow_in: float, flow_out: float, cost: float = 0,
                 init_capacity: int = 0,  eff: int = 0.99):
        """
        Create storage.

        :param capacity: maximum storage capacity (like of many quantity to use inside storage)
        :param flow_in: max flow into storage during on time step
        :param flow_out: max flow out storage during on time step
        :param cost: unit cost of storage at each time-step. default 0
        :param init_capacity: initial capacity level. default 0
        :param eff: storage efficient (applied on input flow stored). default 0.99
        """
        self.study._add_storage(network=self.selector['network'], node=self.selector['node'],
                                store=Storage(name=name, capacity=capacity, flow_in=flow_in, flow_out=flow_out,
                                              cost=cost, init_capacity=init_capacity, eff=eff))
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
        return NetworkFluentAPISelector(selector={}, study=self.study).network(name)

    def converter(self, name: str, to_network: str, to_node: str, max: float, cost: float = 0):
        """
        Add a converter element.

        :param name: converter name
        :param to_network: converter output network
        :param to_node: converter output node on network
        :param max: maximum quantity from converter
        :param cost: cost for each quantity produce by converter
        :return:
        """
        return NetworkFluentAPISelector(selector={}, study=self.study)\
            .converter(name=name, to_network=to_network, to_node=to_node, max=max, cost=cost)

    def to_converter(self, name: str, ratio: float = 1):
        """
        Add an ouptput to converter.

        :param name: converter name
        :param ratio: ratio for output
        :return:
        """
        self.study._add_converter(name=name)
        self.study._add_converter_src(name=name, network=self.selector['network'], node=self.selector['node'], ratio=ratio)
        return self

    def build(self):
        """
        Build study.

        :return: study
        """
        return self.study
