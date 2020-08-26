#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
from copy import deepcopy
from typing import Union, List, Dict, Tuple

import numpy as np

from hadar.optimizer.input import InputNode, JSON

__all__ = ['OutputProduction', 'OutputNode', 'OutputStorage', 'OutputLink', 'OutputConsumption', 'OutputNetwork',
           'OutputConverter', 'Result']


class OutputConsumption(JSON):
    """
    Consumption element
    """
    def __init__(self, quantity: Union[np.ndarray, list], cost: Union[np.ndarray, list], name: str = ''):
        """
        Create instance.

        :param quantity: quantity matched by node
        :param cost: cost of unavailability
        :param name: consumption name (unique in a node)
        """
        self.cost = np.array(cost)
        self.quantity = np.array(quantity)
        self.name = name


    @staticmethod
    def from_json(dict):
        return OutputConsumption(**dict)


class OutputProduction(JSON):
    """
    Production element
    """
    def __init__(self, quantity: Union[np.ndarray, list], cost: Union[np.ndarray, list], name: str = 'in'):
        """
        Create instance.

        :param quantity: capacity used by node
        :param cost: cost of use
        :param name: production name (unique in a node)
        """
        self.name = name
        self.cost = np.array(cost)
        self.quantity = np.array(quantity)

    @staticmethod
    def from_json(dict):
        return OutputProduction(**dict)


class OutputStorage(JSON):
    """
    Storage element
    """
    def __init__(self, name: str, capacity: Union[np.ndarray, list],
                 flow_in: Union[np.ndarray, list], flow_out: Union[np.ndarray, list]):
        """
        Create instance.

        :param name: storage name
        :param capacity: final capacity
        :param flow_in: final input flow
        :param flow_out: final output flow
        """
        self.name = name
        self.capacity = np.array(capacity)
        self.flow_in = np.array(flow_in)
        self.flow_out = np.array(flow_out)

    @staticmethod
    def from_json(dict):
        return OutputStorage(**dict)


class OutputLink(JSON):
    """
    Link element
    """
    def __init__(self, dest: str, quantity: Union[np.ndarray, list], cost: Union[np.ndarray, list]):
        """
        Create instance.

        :param dest: destination node name
        :param quantity: capacity used
        :param cost: cost of use
        """
        self.dest = dest
        self.quantity = np.array(quantity)
        self.cost = np.array(cost)

    @staticmethod
    def from_json(dict):
        return OutputLink(**dict)


class OutputConverter(JSON):
    """
    Converter element
    """
    def __init__(self, name: str, flow_src: Dict[Tuple[str, str], Union[np.ndarray, List]], flow_dest: Union[np.ndarray, List]):
        """
        Create instance.

        :param name: converter name
        :param flow_src: flow from sources
        :param flow_dest: flow to destination
        """
        self.name = name
        self.flow_src = {src: np.array(qt) for src, qt in flow_src.items()}
        self.flow_dest = np.array(flow_dest)

    def to_json(self) -> dict:
        dict = deepcopy(self.__dict__)
        # flow_src has a tuple of two string as key. These forbidden by JSON.
        # Therefore when serialized we join these two strings with '::' to create on string as key
        # Ex: ('elec', 'a') --> 'elec::a'
        dict['flow_src'] = {'::'.join(k): v.tolist() for k, v in self.flow_src.items()}
        dict['flow_dest'] = self.flow_dest.tolist()
        return dict

    @staticmethod
    def from_json(dict: dict):
        # When deserialize, we need to split key string of src_network.
        # JSON doesn't accept tuple as key, so two string was joined for serialization
        # Ex: 'elec::a' -> ('elec', 'a')
        dict['flow_src'] = {tuple(k.split('::')): v for k, v in dict['flow_src'].items()}
        return OutputConverter(**dict)


class OutputNode(JSON):
    """
    Node element
    """
    def __init__(self,
                 consumptions: List[OutputConsumption],
                 productions: List[OutputProduction],
                 storages: List[OutputStorage],
                 links: List[OutputLink]):
        """
        Create Node.

        :param consumptions: consumptions list
        :param productions: productions list
        :param storages: storages list
        :param links:  link list
        """
        self.consumptions = consumptions
        self.productions = productions
        self.storages = storages
        self.links = links

    @staticmethod
    def build_like_input(input: InputNode, fill: np.ndarray):
        """
        Use an input node to create an output node. Keep list elements fill quantity by zeros.

        :param input: InputNode to copy
        :param fill: array to use to fill data
        :return: OutputNode like InputNode with all quantity at zero
        """
        output = OutputNode(consumptions=[], productions=[], storages=[], links=[])
        output.consumptions = [OutputConsumption(name=i.name, cost=i.cost, quantity=fill)
                               for i in input.consumptions]
        output.productions = [OutputProduction(name=i.name, cost=i.cost, quantity=fill)
                              for i in input.productions]
        output.storages = [OutputStorage(name=i.name, capacity=fill,
                                         flow_out=fill, flow_in=fill)
                           for i in input.storages]
        output.links = [OutputLink(dest=i.dest, cost=i.cost, quantity=fill)
                        for i in input.links]
        return output

    @staticmethod
    def from_json(dict):
        dict['consumptions'] = [OutputConsumption.from_json(v) for v in dict['consumptions']]
        dict['productions'] = [OutputProduction.from_json(v) for v in dict['productions']]
        dict['storages'] = [OutputStorage.from_json(v) for v in dict['storages']]
        dict['links'] = [OutputLink.from_json(v) for v in dict['links']]
        return OutputNode(**dict)


class OutputNetwork(JSON):
    """
    Network element
    """

    def __init__(self, nodes: Dict[str, OutputNode]):
        """
        Create network
        :param nodes: nodes belongs to network
        """
        self.nodes = nodes

    @staticmethod
    def from_json(dict):
        dict['nodes'] = {k: OutputNode.from_json(v) for k, v in dict['nodes'].items()}
        return OutputNetwork(**dict)


class Result(JSON):
    """
    Result of study
    """
    def __init__(self, networks: Dict[str, OutputNetwork], converters: Dict[str, OutputConverter]):
        """
        Create result
        :param networks: list of networks present in study
        """
        self.networks = networks
        self.converters = converters


    @staticmethod
    def from_json(dict):
        return Result(networks={k: OutputNetwork.from_json(v) for k, v in dict['networks'].items()},
                      converters={k: OutputConverter.from_json(v) for k, v in dict['converters'].items()})
