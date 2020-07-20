#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

from ortools.linear_solver.pywraplp import Solver

from hadar.optimizer.input import Study, InputNetwork
from hadar.optimizer.lp.domain import LPLink, LPConsumption, LPNode, LPProduction
from hadar.optimizer.output import OutputNode, Result, OutputNetwork


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

    def get_var(self, network: str, node: str, t: int, scn: int) -> LPNode:
        """
        Map InputNode to LPNode.

        :param network: network name
        :param node: node name
        :param t: timestamp
        :param scn: scenario index
        :return: LPNode according to node name at t in study
        """
        suffix = 'inside network=%s on node=%s at t=%d for scn=%d' % (network, node, t, scn)
        consumptions = [LPConsumption(name=c.name, cost=float(c.cost), quantity=c.quantity[scn, t],
                                      variable=self.solver.NumVar(0, float(c.quantity[scn, t]), name='lol=%s %s' % (c.name, suffix)))
                        for c in self.study.networks[network].nodes[node].consumptions]

        productions = [LPProduction(name=p.name, cost=float(p.cost), quantity=p.quantity[scn, t],
                                    variable=self.solver.NumVar(0, float(p.quantity[scn, t]), 'prod=%s %s' % (p.name, suffix)))
                       for p in self.study.networks[network].nodes[node].productions]

        links = [LPLink(dest=l.dest, cost=float(l.cost), src=node, quantity=l.quantity[scn, t],
                        variable=self.solver.NumVar(0, float(l.quantity[scn, t]), 'link=%s %s' % (l.dest, suffix)))
                 for l in self.study.networks[network].nodes[node].links]

        return LPNode(consumptions=consumptions, productions=productions, links=links)


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
        def build_nodes(network: InputNetwork):
            return {name: OutputNode.build_like_input(input) for name, input in network.nodes.items()}

        self.networks = {name: OutputNetwork(nodes=build_nodes(network)) for name, network in study.networks.items()}

    def set_var(self, network: str, node: str, t: int, scn: int, vars: LPNode):
        """
        Map linear programming node to global node (set inside intern attribute).

        :param network: network name
        :param node: node name
        :param t: timestamp index
        :param scn: scenario index
        :param vars: linear programming node with ortools variables inside
        :return: None (use get_result)
        """
        for i in range(len(vars.consumptions)):
            self.networks[network].nodes[node].consumptions[i].quantity[scn, t] = vars.consumptions[i].quantity - vars.consumptions[i].variable.solution_value()

        for i in range(len(vars.productions)):
            self.networks[network].nodes[node].productions[i].quantity[scn, t] = vars.productions[i].variable.solution_value()

        for i in range(len(vars.links)):
            self.networks[network].nodes[node].links[i].quantity[scn, t] = vars.links[i].variable.solution_value()

    def get_result(self) -> Result:
        """
        Get result.

        :return: final result after map all nodes
        """
        return Result(networks=self.networks)
