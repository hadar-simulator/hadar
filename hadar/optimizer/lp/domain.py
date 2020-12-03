#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import numpy as np

from abc import ABC, abstractmethod
from typing import List, Union, Dict, Tuple

from ortools.linear_solver.pywraplp import Variable

from hadar import Study
from hadar.optimizer.utils import JSON


class JSONLP(JSON, ABC):
    def to_json(self):
        def copy(v):
            if isinstance(v, Variable):
                return v.solution_value()
            elif isinstance(v, dict):
                # Json can't serialize tuple key, therefore join items with ::
                return {
                    "::".join(k) if isinstance(k, tuple) else k: copy(v)
                    for k, v in v.items()
                }
            elif isinstance(v, np.int64):
                return int(v)
            elif isinstance(v, np.float64):
                return float(v)
            else:
                return v

        return {k: copy(v) for k, v in self.__dict__.items()}

    @staticmethod
    @abstractmethod
    def from_json(dict, factory=None):
        pass


class LPConsumption(JSONLP):
    """
    Consumption element for linear programming.
    """

    def __init__(
        self,
        quantity: int,
        variable: Union[Variable, float],
        cost: float = 0,
        name: str = "",
    ):
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

    @staticmethod
    def from_json(dict, factory=None):
        return LPConsumption(**dict)


class LPProduction(JSONLP):
    """
    Production element for linear programming.
    """

    def __init__(
        self,
        quantity: int,
        variable: Union[Variable, float],
        cost: float = 0,
        name: str = "in",
    ):
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

    @staticmethod
    def from_json(dict, factory=None):
        return LPProduction(**dict)


class LPStorage(JSONLP):
    """
    Storage element
    """

    def __init__(
        self,
        name,
        capacity: int,
        var_capacity: Union[Variable, float],
        flow_in: float,
        var_flow_in: Union[Variable, float],
        flow_out: float,
        var_flow_out: Union[Variable, float],
        cost: float = 0,
        init_capacity: int = 0,
        eff: float = 0.99,
    ):
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

    @staticmethod
    def from_json(dict, factory=None):
        return LPStorage(**dict)


class LPLink(JSONLP):
    """
    Link element for linear programming
    """

    def __init__(
        self,
        src: str,
        dest: str,
        quantity: int,
        variable: Union[Variable, float],
        cost: float = 0,
    ):
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

    @staticmethod
    def from_json(dict, factory=None):
        return LPLink(**dict)


class LPConverter(JSONLP):
    """
    Converter element for linear programming
    """

    def __init__(
        self,
        name: str,
        src_ratios: Dict[Tuple[str, str], float],
        var_flow_src: Dict[Tuple[str, str], Union[Variable, float]],
        dest_network: str,
        dest_node: str,
        var_flow_dest: Union[Variable, float],
        cost: float,
        max: float,
    ):
        """
        Create converter.

        :param name: converter name

        :param src_ratios: ration conversion for each sources. data={(network, node): ratio}
        :param var_flow_src: ortools variables represents quantity from sources
        :param dest_network: destination network
        :param dest_node: destination node
        :param var_flow_dest: ortools variables represents quantity to destination
        :param cost: cost applied on quantity through converter
        :param max: max output flow
        """
        self.name = name
        self.src_ratios = src_ratios
        self.var_flow_src = var_flow_src
        self.dest_network = dest_network
        self.dest_node = dest_node
        self.var_flow_dest = var_flow_dest
        self.cost = cost
        self.max = max

    @staticmethod
    def from_json(dict, factory=None):
        # Json can't serialize tuple as key. tuple is concatained before serialized, we need to extract it now
        dict["src_ratios"] = {
            tuple(k.split("::")): v for k, v in dict["src_ratios"].items()
        }
        dict["var_flow_src"] = {
            tuple(k.split("::")): v for k, v in dict["var_flow_src"].items()
        }
        return LPConverter(**dict)


class LPNode(JSON):
    """
    Node element for linear programming
    """

    def __init__(
        self,
        consumptions: List[LPConsumption],
        productions: List[LPProduction],
        storages: List[LPStorage],
        links: List[LPLink],
    ):
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

    @staticmethod
    def from_json(dict, factory=None):
        dict["consumptions"] = [
            LPConsumption.from_json(v) for v in dict["consumptions"]
        ]
        dict["productions"] = [LPProduction.from_json(v) for v in dict["productions"]]
        dict["storages"] = [LPStorage.from_json(v) for v in dict["storages"]]
        dict["links"] = [LPLink.from_json(v) for v in dict["links"]]
        return LPNode(**dict)


class LPNetwork(JSON):
    """
    Network element for linear programming
    """

    def __init__(self, nodes: Dict[str, LPNode] = None):
        """
        Instance network.

        :param study: Study to use to generate blank network
        """
        self.nodes = nodes if nodes else dict()

    @staticmethod
    def from_json(dict, factory=None):
        dict["nodes"] = {k: LPNode.from_json(v) for k, v in dict["nodes"].items()}
        return LPNetwork(**dict)


class LPTimeStep(JSON):
    def __init__(
        self, networks: Dict[str, LPNetwork], converters: Dict[str, LPConverter]
    ):
        self.networks = networks
        self.converters = converters

    @staticmethod
    def create_like_study(study: Study):
        networks = {name: LPNetwork() for name in study.networks}
        converters = dict()
        return LPTimeStep(networks=networks, converters=converters)

    @staticmethod
    def from_json(dict, factory=None):
        return LPTimeStep(
            networks={k: LPNetwork.from_json(v) for k, v in dict["networks"].items()},
            converters={
                k: LPConverter.from_json(v) for k, v in dict["converters"].items()
            },
        )
