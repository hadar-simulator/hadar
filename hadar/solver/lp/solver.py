import logging

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
        self.logger = logging.getLogger(__name__ + '.' + __class__.__name__)

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
        pass


class AdequacyBuilder:
    """
    Build adequacy flow constraint.
    """
    def __init__(self, solver: Solver):
        """
        Initiate
        :param solver: ortools solver instance to use
        """
        self.constraints = {}
        self.borders = []
        self.solver = solver
        self.logger = logging.getLogger(__name__ + '.' + __class__.__name__)

    def add_node(self, name, node: LPNode):
        """
        Add flow constraint for a specific node.

        :param name: node name. Used to differentiate each equation
        :param node: node to map constraint
        :return:
        """
        load = sum([c.quantity for c in node.consumptions])*1.0
        self.constraints[name] = self.solver.Constraint(load, load)

        self._add_consumptions(name, node.consumptions)
        self._add_productions(name, node.productions)
        self._add_borders(name, node.borders)

    def _add_consumptions(self, name: str, consumptions: List[LPConsumption]):
        """
        Add consumption flow. That mean loss of consumption is set a production to match
        equation in case there are not enough production.

        :param name: node's name
        :param consumptions: consumptions with loss as variable
        :return:
        """
        for cons in consumptions:
            self.constraints[name].SetCoefficient(cons.variable, 1)
            self.logger.debug('Add lol %s for %s into adequacy constraint', cons.type, name)

    def _add_productions(self, name: str, productions: List[LPProduction]):
        """
        Add production flow. That mean production use is like a production.

        :param name: node's name
        :param productions: productoins with production used as variable
        :return:
        """
        for prod in productions:
            self.constraints[name].SetCoefficient(prod.variable, 1)
            self.logger.debug('Add prod %s for %s into adequacy constraint', prod.type, name)

    def _add_borders(self, name: str, borders: List[LPBorder]):
        """
        Add borders. That mean the border export is like a consumption.
        After all node added. The same export, become also an import for destination node.
        Therefore border has to be set like production for destination node.

        :param name: node's name
        :param borders: border with export quantity as variable
        :return:
        """
        for bord in borders:
            self.borders.append(bord)
            self.constraints[name].SetCoefficient(bord.variable, -1)
            self.logger.debug('Add border %s for %s into adequacy constraint', bord.dest, name)

    def build(self):
        """
        Call when all node are added. Apply all import flow for each node.

        :return:
        """
        # Apply import border in adequacy
        for bord in self.borders:
            self.constraints[bord.dest].SetCoefficient(bord.variable, 1)


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
    variables = [{}] * study.horizon

    for t in range(0, study.horizon):
        for name, node in study.nodes.items():
            variables[t][name] = in_mapper.get_var(name=name, t=t)

            adequacy.add_node(name=name, node=variables[t][name])
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
    adequacy = AdequacyBuilder(solver=solver)

    in_mapper = InputMapper(solver=solver, study=study)
    out_mapper = OutputMapper(solver=solver, study=study)

    return _solve(study, solver, objective, adequacy, in_mapper, out_mapper)
