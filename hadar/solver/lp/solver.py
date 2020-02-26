import logging

from typing import List
from ortools.linear_solver.pywraplp import Solver

import hadar
from hadar.solver.lp.domain import *
from hadar.solver.input import InputNode, Study
from hadar.solver.lp.mapper import InputMapper, OutputMapper
from hadar.solver.output import OutputNode, Result

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
        self._add_borders(node.borders)

    def _add_consumption(self, consumptions: List[LPConsumption]):
        """
        Add consumption cost. That mean we add cost of a loss of consumption.

        :param consumptions: consumption with loss variable and cost
        :return:
        """
        for cons in consumptions:
            self.objective.SetCoefficient(cons.variable, cons.cost)
            self.logger.debug('Add consumption %s into objective', cons.type)

    def _add_productions(self, prods: List[LPProduction]):
        """
        Add production cost. That mean the cost to use a production.

        :param prods: production with cost to use and used quantity variable
        :return:
        """
        for prod in prods:
            self.objective.SetCoefficient(prod.variable, prod.cost)
            self.logger.debug('Add production %s into objective', prod.type)

    def _add_borders(self, borders: List[LPBorder]):
        """
        Add border cost. That mean cost to use a border capacity.

        :param borders: borders with cost to use and used quantity variable
        :return:
        """
        for border in borders:
            self.objective.SetCoefficient(border.variable, border.cost)
            self.logger.debug('Add border %s->%s to objective', border.src, border.dest)

    def build(self):
        pass  # Currently nothing are need at the end. But we keep builder pattern syntax


class AdequacyBuilder:
    """
    Build adequacy flow constraint.
    """
    def __init__(self, solver: Solver, horizon: int):
        """
        Initiate.

        :param solver: ortools solver instance to use
        :param horizon: study horizon
        """
        self.constraints = [dict() for _ in range(horizon)]
        self.borders = [list() for _ in range(horizon)]
        self.solver = solver
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)

    def add_node(self, name: str, t: int, node: LPNode):
        """
        Add flow constraint for a specific node.

        :param name: node name. Used to differentiate each equation
        :param t: timestamp index
        :param node: node to map constraint
        :return:
        """
        load = sum([c.quantity for c in node.consumptions])*1.0
        self.constraints[t][name] = self.solver.Constraint(load, load)

        self._add_consumptions(name, t, node.consumptions)
        self._add_productions(name, t, node.productions)
        self._add_borders(name, t, node.borders)

    def _add_consumptions(self, name: str, t: int, consumptions: List[LPConsumption]):
        """
        Add consumption flow. That mean loss of consumption is set a production to match
        equation in case there are not enough production.

        :param name: node's name
        :param t: timestamp index
        :param consumptions: consumptions with loss as variable
        :return:
        """
        for cons in consumptions:
            self.constraints[t][name].SetCoefficient(cons.variable, 1)
            self.logger.debug('Add lol %s for %s into adequacy constraint', cons.type, name)

    def _add_productions(self, name: str, t: int, productions: List[LPProduction]):
        """
        Add production flow. That mean production use is like a production.

        :param name: node's name
        :param t: timestamp index
        :param productions: productions with production used as variable
        :return:
        """
        for prod in productions:
            self.constraints[t][name].SetCoefficient(prod.variable, 1)
            self.logger.debug('Add prod %s for %s into adequacy constraint', prod.type, name)

    def _add_borders(self, name: str, t: int, borders: List[LPBorder]):
        """
        Add borders. That mean the border export is like a consumption.
        After all node added. The same export, become also an import for destination node.
        Therefore border has to be set like production for destination node.

        :param name: node's name
        :param t: timestamp index
        :param borders: border with export quantity as variable
        :return:
        """
        for bord in borders:
            self.borders[t].append(bord)
            self.constraints[t][name].SetCoefficient(bord.variable, -1)
            self.logger.debug('Add border %s for %s into adequacy constraint', bord.dest, name)

    def build(self):
        """
        Call when all node are added. Apply all import flow for each node.

        :return:
        """
        # Apply import border in adequacy
        for t in range(len(self.constraints)):
            for bord in self.borders[t]:
                self.constraints[t][bord.dest].SetCoefficient(bord.variable, 1)


def _solve(study: Study,
           solver: Solver,
           objective: ObjectiveBuilder,
           adequacy: AdequacyBuilder,
           in_mapper: InputMapper,
           out_mapper: OutputMapper) -> Result:
    """
    Solve adequacy flow problem with a linear optimizer.

    :param study: study to compute
    :param solver: solver to used
    :param objective: objective builder to use
    :param adequacy: adequacy builder to use
    :return: Result object with optimal solution
    """
    variables = [dict() for _ in range(study.horizon)]

    for t in range(0, study.horizon):
        for name, node in study.nodes.items():
            variables[t][name] = in_mapper.get_var(name=name, t=t)

            adequacy.add_node(name=name, t=t, node=variables[t][name])
            objective.add_node(node=variables[t][name])

    objective.build()
    adequacy .build()

    logger.info('Problem build. Start solver')
    solver.EnableOutput()
    solver.Solve()

    logger.info('Solver finish cost=%d', solver.Objective().Value())
    logger.debug(solver.ExportModelAsLpFormat(False).replace('\\', '').replace(',_', ','))

    for t in range(0, study.horizon):
        for name, node in study.nodes.items():
            out_mapper.set_var(name=name, t=t, vars=variables[t][name])

    return out_mapper.get_result()


def solve_lp(study: Study) -> Result:
    """
    Solve adequacy flow problem with a linear optimizer.

    :param study: study to compute
    :return: Result object with optimal solution
    """
    solver = Solver('simple_lp_program', Solver.GLOP_LINEAR_PROGRAMMING)

    objective = ObjectiveBuilder(solver=solver)
    adequacy = AdequacyBuilder(solver=solver, horizon=study.horizon)

    in_mapper = InputMapper(solver=solver, study=study)
    out_mapper = OutputMapper(solver=solver, study=study)

    return _solve(study, solver, objective, adequacy, in_mapper, out_mapper)
