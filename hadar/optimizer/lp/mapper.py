#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import numpy as np
from ortools.linear_solver.pywraplp import Solver

from hadar.optimizer.input import Study, InputNetwork
from hadar.optimizer.lp.domain import LPLink, LPConsumption, LPNode, LPProduction, LPStorage, LPConverter
from hadar.optimizer.output import OutputNode, Result, OutputNetwork, OutputConverter


class InputMapper:
    """
    Input mapper from global domain to linear programming specific domain
    """

    def __init__(self, solver: Solver, study: Study):
        """
        Instantiate mapper.

        :param solver: ortools solver to used to create variables
        :param study: study data
        """
        self.solver = solver
        self.study = study

    def get_node_var(self, network: str, node: str, t: int, scn: int) -> LPNode:
        """
        Map InputNode to LPNode.

        :param network: network name
        :param node: node name
        :param t: time step
        :param scn: scenario index
        :return: LPNode according to node name at t in study
        """
        suffix = 'inside network=%s on node=%s at t=%d for scn=%d' % (network, node, t, scn)
        in_node = self.study.networks[network].nodes[node]

        consumptions = [LPConsumption(name=c.name, cost=c.cost[scn, t], quantity=c.quantity[scn, t],
                                      variable=self.solver.NumVar(0, float(c.quantity[scn, t]), name='lol=%s %s' % (c.name, suffix)))
                        for c in in_node.consumptions]

        productions = [LPProduction(name=p.name, cost=p.cost[scn, t], quantity=p.quantity[scn, t],
                                    variable=self.solver.NumVar(0, float(p.quantity[scn, t]), 'prod=%s %s' % (p.name, suffix)))
                       for p in in_node.productions]

        storages = [LPStorage(name=s.name, capacity=s.capacity, flow_in=s.flow_in, flow_out=s.flow_out, eff=s.eff,
                              init_capacity=s.init_capacity, cost=s.cost,
                              var_capacity=self.solver.NumVar(0, float(s.capacity), 'storage_capacity=%s %s' % (s.name, suffix)),
                              var_flow_in=self.solver.NumVar(0, float(s.flow_in), 'storage_flow_in=%s %s' % (s.name, suffix)),
                              var_flow_out=self.solver.NumVar(0, float(s.flow_out), 'storage_flow_out=%s %s' % (s.name, suffix)))
                    for s in in_node.storages]

        links = [LPLink(dest=l.dest, cost=l.cost[scn, t], src=node, quantity=l.quantity[scn, t],
                        variable=self.solver.NumVar(0, float(l.quantity[scn, t]), 'link=%s %s' % (l.dest, suffix)))
                 for l in in_node.links]

        return LPNode(consumptions=consumptions, productions=productions, links=links, storages=storages)

    def get_conv_var(self, name: str, t: int, scn: int) -> LPConverter:
        """
        Map Converter to LPConverter.

        :param name: converter name
        :param t: time step
        :param scn: scenario index
        :return: LPConverter
        """
        suffix = 'at t=%d for scn=%d' % (t, scn)
        v = self.study.converters[name]

        return LPConverter(name=v.name, src_ratios=v.src_ratios, dest_network=v.dest_network, dest_node=v.dest_node,
                           cost=v.cost, max=v.max,
                           var_flow_src={src: self.solver.NumVar(0, float(v.max / r), 'flow_src %s %s %s' % (v.name, ':'.join(src), suffix))
                                         for src, r in v.src_ratios.items()},
                           var_flow_dest=self.solver.NumVar(0, float(v.max), 'flow_dest %s %s' % (v.name, suffix)))


class OutputMapper:
    """
    Output mapper from specific linear programming domain to global domain.
    """
    def __init__(self, study: Study):
        """
        Instantiate mapper.

        :param solver: ortools solver to use to fetch variable value
        :param study: input study to reproduce structure
        """
        zeros = np.zeros((study.nb_scn, study.horizon))
        def build_nodes(network: InputNetwork):
            return {name: OutputNode.build_like_input(input, fill=zeros) for name, input in network.nodes.items()}

        self.networks = {name: OutputNetwork(nodes=build_nodes(network)) for name, network in study.networks.items()}
        self.converters = {name: OutputConverter(name=name, flow_src={src: zeros for src in conv.src_ratios}, flow_dest=zeros)
                           for name, conv in study.converters.items()}

    def set_node_var(self, network: str, node: str, t: int, scn: int, vars: LPNode):
        """
        Map linear programming node to global node (set inside intern attribute).

        :param network: network name
        :param node: node name
        :param t: timestamp index
        :param scn: scenario index
        :param vars: linear programming node with ortools variables inside
        :return: None (use get_result)
        """
        out_node = self.networks[network].nodes[node]
        for i in range(len(vars.consumptions)):
            out_node.consumptions[i].quantity[scn, t] = vars.consumptions[i].quantity - vars.consumptions[i].variable.solution_value()

        for i in range(len(vars.productions)):
            out_node.productions[i].quantity[scn, t] = vars.productions[i].variable.solution_value()

        for i in range(len(vars.storages)):
            out_node.storages[i].capacity[scn, t] = vars.storages[i].var_capacity.solution_value()
            out_node.storages[i].flow_in[scn, t] = vars.storages[i].var_flow_in.solution_value()
            out_node.storages[i].flow_out[scn, t] = vars.storages[i].var_flow_out.solution_value()

        for i in range(len(vars.links)):
            self.networks[network].nodes[node].links[i].quantity[scn, t] = vars.links[i].variable.solution_value()

    def set_converter_var(self, name: str, t: int, scn: int, vars: LPConverter):
        for src, var in vars.var_flow_src.items():
            self.converters[name].flow_src[src][scn, t] = var.solution_value()
        self.converters[name].flow_dest[scn, t] = vars.var_flow_dest.solution_value()

    def get_result(self) -> Result:
        """
        Get result.

        :return: final result after map all nodes
        """
        return Result(networks=self.networks, converters=self.converters)
