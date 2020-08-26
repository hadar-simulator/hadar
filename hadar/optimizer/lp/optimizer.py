#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import logging
import multiprocessing
import pickle
from typing import List

from ortools.linear_solver.pywraplp import Solver, Constraint

from hadar.optimizer.input import Study
from hadar.optimizer.lp.domain import LPNode, LPProduction, LPConsumption, LPLink, LPStorage, LPTimeStep, LPConverter
from hadar.optimizer.lp.mapper import InputMapper, OutputMapper
from hadar.optimizer.output import Result

logger = logging.getLogger(__name__)


class ObjectiveBuilder:
    """
    Build objective cost function.
    """

    def __init__(self, solver: Solver):
        """
        Initiate new objective to minimize inside ortools solver.

        :param solver: ortools solver instance to use
        """
        self.objective = solver.Objective()
        self.objective.SetMinimization()
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)

    def add_node(self, node: LPNode):
        """
        Add cost in objective for each node element.

        :param node: node to add
        :return:
        """
        self._add_consumption(node.consumptions)
        self._add_productions(node.productions)
        self._add_storages(node.storages)
        self._add_links(node.links)

    def _add_consumption(self, consumptions: List[LPConsumption]):
        """
        Add consumption cost. That mean we add cost of a loss of consumption.

        :param consumptions: consumption with loss variable and cost
        :return:
        """
        for cons in consumptions:
            self.objective.SetCoefficient(cons.variable, cons.cost)
            self.logger.debug('Add consumption %s into objective', cons.name)

    def _add_productions(self, prods: List[LPProduction]):
        """
        Add production cost. That mean the cost to use a production.

        :param prods: production with cost to use and used quantity variable
        :return:
        """
        for prod in prods:
            self.objective.SetCoefficient(prod.variable, prod.cost)
            self.logger.debug('Add production %s into objective', prod.name)

    def _add_storages(self, stors: List[LPStorage]):
        """
        Add storage cost. Cost of store for each time-step
        :param stors: list of storages
        :return:
        """
        for stor in stors:
            self.objective.SetCoefficient(stor.var_capacity, stor.cost)
            self.logger.debug('Add storage %s into objective', stor.name)

    def _add_links(self, links: List[LPLink]):
        """
        Add link cost. That mean cost to use a link capacity.

        :param links: links with cost to use and used quantity variable
        :return:
        """
        for link in links:
            self.objective.SetCoefficient(link.variable, link.cost)
            self.logger.debug('Add link %s->%s to objective', link.src, link.dest)

    def add_converter(self, conv: LPConverter):
        """
        Add converter. Apply cost on output of converter.

        :param conv: converter to cost
        :return:
        """
        self.objective.SetCoefficient(conv.var_flow_dest, conv.cost)
        self.logger.debug('Add converter %s to objective' % conv.name)

    def build(self):
        pass  # Currently nothing are need at the end. But we keep builder pattern syntax


class AdequacyBuilder:
    """
    Build adequacy flow constraint.
    """
    def __init__(self, solver: Solver):
        """
        Initiate.

        :param solver: ortools solver instance to use
        :param horizon: study horizon
        """
        self.constraints = dict()
        self.importations = dict()
        self.solver = solver
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)

    def add_node(self, name_network: str, name_node: str, node: LPNode, t: int):
        """
        Add flow constraint for a specific node.

        :param name_network: network name. Used to differentiate each equation
        :param name_node: node name. Used to differentiate each equation
        :param node: node to map constraint
        :return:
        """
        # Set forced consumption
        load = sum([c.quantity for c in node.consumptions]) * 1.0
        self.constraints[(t, name_network, name_node)] = self.solver.Constraint(load, load)

        self._add_consumptions(name_network, name_node, t, node.consumptions)
        self._add_productions(name_network, name_node, t, node.productions)
        self._add_storages(name_network, name_node, t, node.storages)
        self._add_links(name_network, name_node, t, node.links)

    def _add_consumptions(self, name_network: str, name_node: str, t: int, consumptions: List[LPConsumption]):
        """
        Add consumption flow. That mean loss of consumption is set a production to match
        equation in case there are not enough production.

        :param name_network: network's name
        :param name_node: node's name
        :param t: timestamp
        :param consumptions: consumptions with loss as variable
        :return:
        """
        for cons in consumptions:
            self.constraints[(t, name_network, name_node)].SetCoefficient(cons.variable, 1)
            self.logger.debug('Add lol %s for %s inside %s into adequacy constraint', cons.name, name_node, name_network)

    def _add_productions(self, name_network: str, name_node: str, t: int, productions: List[LPProduction]):
        """
        Add production flow. That mean production use is like a production.

        :param name_network: network's name
        :param name_node: node's name
        :param t: timestamp
        :param productions: productions with production used as variable
        :return:
        """
        for prod in productions:
            self.constraints[(t, name_network, name_node)].SetCoefficient(prod.variable, 1)
            self.logger.debug('Add prod %s for %s inside %s into adequacy constraint', prod.name, name_node, name_network)

    def _add_storages(self, name_network: str, name_node: str, t: int, storages: List[LPStorage]):
        """
        Add storage flow. Flow in is like a consumption. Flow out is like a production.

        :param name_network: network's name
        :param name_node: node's name
        :param t: timestamp
        :param productions: storage with flow used as variable
        :return:
        """
        for stor in storages:
            self.constraints[(t, name_network, name_node)].SetCoefficient(stor.var_flow_in, -1)
            self.constraints[(t, name_network, name_node)].SetCoefficient(stor.var_flow_out, 1)
            self.logger.debug('Add storage %s for %s inside %s into adequacy constraint', stor.name, name_node, name_network)

    def _add_links(self, name_network: str, name_node: str, t: int, links: List[LPLink]):
        """
        Add links. That mean the link export is like a consumption.
        After all node added. The same export, become also an import for destination node.
        Therefore link has to be set like production for destination node.

        :param name_network: network's name
        :param name_node: node's name
        :param t: timestamp
        :param links: link with export quantity as variable
        :return:
        """
        for link in links:
            self.constraints[(t, name_network, link.src)].SetCoefficient(link.variable, -1)  # Export from src
            self.importations[(t, name_network, link.src, link.dest)] = link.variable  # Import to dest
            self.logger.debug('Add link %s for %s inside %s into adequacy constraint', link.dest, name_node, name_network)

    def add_converter(self, conv: LPConverter, t: int):
        """
        Add converter element in equation. Sources are like consumptions, destination like production

        :param conv: converter element to add
        :param t: time index to use
        :return:
        """
        self.constraints[(t, conv.dest_network, conv.dest_node)].SetCoefficient(conv.var_flow_dest, 1)
        for (network, node), var in conv.var_flow_src.items():
            self.constraints[(t, network, node)].SetCoefficient(var, -1)
        self.logger.debug('Add converter %s' % conv.name)

    def build(self):
        """
        Call when all node are added. Apply all import flow for each node.

        :return:
        """
        # Apply import link in adequacy
        for (t, net, src, dest), var in self.importations.items():
            self.constraints[(t, net, dest)].SetCoefficient(var, 1)


class StorageBuilder:
    """
    Build storage constraints
    """

    def __init__(self, solver: Solver):
        self.capacities = dict()
        self.solver = solver
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)

    def add_node(self, name_network: str, name_node: str, node: LPNode, t: int) -> Constraint:
        for stor in node.storages:
            self.capacities[(t, name_network, name_node, stor.name)] = stor.var_capacity
            if t == 0:
                const = self.solver.Constraint(stor.init_capacity, stor.init_capacity)
                const.SetCoefficient(stor.var_flow_in, -stor.eff)
                const.SetCoefficient(stor.var_flow_out, 1)
                const.SetCoefficient(stor.var_capacity, 1)
                return const
            else:
                const = self.solver.Constraint(0, 0)
                const.SetCoefficient(stor.var_flow_in, -stor.eff)
                const.SetCoefficient(stor.var_flow_out, 1)
                const.SetCoefficient(self.capacities[(t-1, name_network, name_node, stor.name)], -1)
                const.SetCoefficient(stor.var_capacity, 1)
                return const

    def build(self):
        pass  # Currently nothing are need at the end. But we keep builder pattern syntax


class ConverterMixBuilder:
    """
    Build equation to determine ratio mix between sources converter.
    """
    def __init__(self, solver: Solver):
        self.solver = solver
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)

    def add_converter(self, conv: LPConverter):
        return [ConverterMixBuilder._build_constraint(self.solver, r, conv.var_flow_dest, conv.var_flow_src[src])
                for src, r in conv.src_ratios.items()]

    @staticmethod
    def _build_constraint(solver, r, var_dest, var_src):
        const = solver.Constraint(0, 0)
        const.SetCoefficient(var_src, r)
        const.SetCoefficient(var_dest, -1)
        return const

    def build(self):
        pass  # Currently nothing are need at the end. But we keep builder pattern syntax


def _solve_batch(params) -> bytes:
    """
    Solve study scenario batch. Called by multiprocessing.
    :param params: (study, scenarios) for main runtime OR (study, scenario, mock solver, mock objective
    , mock adequacy, mock input mapper) only for test purpose.
    :return: [t: {name: LPNode, ...},  ...]
    """
    if len(params) == 2:  # Runtime
        study, i_scn = params

        solver = Solver('simple_lp_program', Solver.GLOP_LINEAR_PROGRAMMING)

        objective = ObjectiveBuilder(solver=solver)
        adequacy = AdequacyBuilder(solver=solver)
        storage = StorageBuilder(solver=solver)
        mix = ConverterMixBuilder(solver=solver)

        in_mapper = InputMapper(solver=solver, study=study)
    else:  # Test purpose only
        study, i_scn, solver, objective, adequacy, storage, mix, in_mapper = params

    variables = [LPTimeStep.create_like_study(study) for _ in range(study.horizon)]

    # Build equation
    for t in range(0, study.horizon):

        # Build node constraints
        for name_network, network in study.networks.items():
            for name_node, node in network.nodes.items():
                node = in_mapper.get_node_var(network=name_network, node=name_node, t=t, scn=i_scn)
                variables[t].networks[name_network].nodes[name_node] = node
                adequacy.add_node(name_network=name_network, name_node=name_node, node=node, t=t)
                storage.add_node(name_network=name_network, name_node=name_node, node=node, t=t)
                objective.add_node(node=node)

        # Build converter constraints
        for name in study.converters:
            conv = in_mapper.get_conv_var(name=name, t=t, scn=i_scn)
            variables[t].converters[name] = conv
            adequacy.add_converter(conv=conv, t=t)
            mix.add_converter(conv=conv)
            objective.add_converter(conv=conv)

    objective.build()
    adequacy .build()
    storage.build()
    mix.build()

    logger.info('Problem build. Start solver')
    solver.EnableOutput()
    solver.Solve()

    logger.info('Solver finish cost=%d', solver.Objective().Value())
    logger.debug(solver.ExportModelAsLpFormat(False).replace('\\', '').replace(',_', ','))

    # When multiprocessing handle response and serialize it with pickle,
    # it's occur that ortools variables seem already erased.
    # To fix this situation, serialization is handle inside 'job scope'
    return pickle.dumps(variables)


def solve_lp(study: Study, out_mapper=None) -> Result:
    """
    Solve adequacy flow problem with a linear optimizer.

    :param study: study to compute
    :param out_mapper: use only for test purpose to inject mock. Keep None as default.
    :return: Result object with optimal solution
    """
    out_mapper = out_mapper or OutputMapper(study)

    pool = multiprocessing.Pool()
    byte = pool.map(_solve_batch, ((study, i_scn) for i_scn in range(study.nb_scn)))
    variables = [pickle.loads(b) for b in byte]

    for scn in range(0, study.nb_scn):
        for t in range(0, study.horizon):
            # Set node elements
            for name_network, network in study.networks.items():
                for name_node in network.nodes.keys():
                    out_mapper.set_node_var(network=name_network, node=name_node, t=t, scn=scn,
                                            vars=variables[scn][t].networks[name_network].nodes[name_node])
            # Set converters
            for name_conv in study.converters:
                out_mapper.set_converter_var(name=name_conv, t=t, scn=scn, vars=variables[scn][t].converters[name_conv])

    return out_mapper.get_result()
