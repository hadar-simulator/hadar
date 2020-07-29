#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import numpy as np

from typing import Union, List, Dict, Tuple

from hadar.optimizer.input import InputNode


__all__ = ['OutputProduction', 'OutputNode', 'OutputStorage', 'OutputLink', 'OutputConsumption', 'OutputNetwork', 'Result']


class DTO:
    """
    Implement basic method for DTO objects
    """

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        for name, att in self.__dict__.items():
            if isinstance(att, (np.ndarray, np.generic)):
                if not np.array_equal(self.__dict__[name], other.__dict__[name]):
                    return False
            elif self.__dict__[name] != other.__dict__[name]:
                return False
        return True

    def __str__(self):
        return "{}({})".format(type(self).__name__,
                               ", ".join(["{}={}".format(k, str(self.__dict__[k])) for k in sorted(self.__dict__)]))

    def __repr__(self):
        return self.__str__()


class OutputConsumption(DTO):
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
        self.cost = cost
        self.quantity = np.array(quantity)
        self.name = name


class OutputProduction(DTO):
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
        self.cost = cost
        self.quantity = np.array(quantity)


class OutputStorage(DTO):
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


class OutputLink(DTO):
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
        self.cost = cost


class OutputConverter(DTO):
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


class OutputNode(DTO):
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


class OutputNetwork(DTO):
    """
    Network element
    """

    def __init__(self, nodes: Dict[str, OutputNode]):
        """
        Create network
        :param nodes: nodes belongs to network
        """
        self.nodes = nodes


class Result(DTO):
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
