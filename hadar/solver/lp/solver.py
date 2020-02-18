import logging

from ortools.linear_solver.pywraplp import Solver

import hadar
from hadar.solver.lp.domain import *
from hadar.solver.input import InputNode, Study
from hadar.solver.lp.mapper import InputMapper, OutputMapper
from hadar.solver.output import OutputNode, Result

logger = logging.getLogger(__name__)

class ObjectiveBuilder:
    def __init__(self, solver: Solver):
        self.objective = solver.Objective()
        self.objective.SetMinimization()
        self.logger = logging.getLogger(__name__ + '.' + __class__.__name__)

    def add_consumption(self, consumptions: List[LPConsumption]):
        for cons in consumptions:
            self.objective.SetCoefficient(cons.variable, cons.cost)
            self.logger.debug('Add consumption %s into objective', cons.type)

    def add_productions(self, prods: List[LPProduction]):
        for prod in prods:
            self.objective.SetCoefficient(prod.variable, prod.cost)
            self.logger.debug('Add production %s into objective', prod.type)

    def add_borders(self, borders: List[LPBorder]):
        for border in borders:
            self.objective.SetCoefficient(border.variable, border.cost)
            self.logger.debug('Add border %s->%s to objective', border.src, border.dest)

    def build(self):
        pass


class AdequacyBuilder:
    def __init__(self, solver: Solver):
        self.constraints = {}
        self.borders = []
        self.solver = solver
        self.logger = logging.getLogger(__name__ + '.' + __class__.__name__)

    def add_node(self, name, node: LPNode):
        load = sum([c.quantity for c in node.consumptions])*1.0
        ct = self.solver.Constraint(load, load)
        for cons in node.consumptions:
            ct.SetCoefficient(cons.variable, 1)
            self.logger.debug('Add lol %s for %s into adequacy constraint', cons.type, name)

        for prod in node.productions:
            ct.SetCoefficient(prod.variable, 1)
            self.logger.debug('Add prod %s for %s into adequacy constraint', prod.type, name)

        for bord in node.borders:
            self.borders.append(bord)
            ct.SetCoefficient(bord.variable, -1)
            self.logger.debug('Add border %s for %s into adequacy constraint', bord.dest, name)
        self.constraints[name] = ct

    def build(self):
        # Apply import border in adequacy
        for bord in self.borders:
            self.constraints[bord.dest].SetCoefficient(bord.variable, 1)


def solve_lp(study: Study) -> Result:
    solver = Solver('simple_lp_program', Solver.GLOP_LINEAR_PROGRAMMING)

    objective = ObjectiveBuilder(solver=solver)
    adequacy_const = AdequacyBuilder(solver=solver)
    variables = [{}] * study.horizon

    in_mapper = InputMapper(solver=solver, study=study)
    for t in range(0, study.horizon):
        for name, node in study.nodes.items():
            variables[t][name] = in_mapper.get_var(name=name, t=t)

            adequacy_const.add_node(name=name, node=variables[t][name])
            objective.add_productions(variables[t][name].productions)
            objective.add_borders(variables[t][name].borders)
            objective.add_consumption(variables[t][name].consumptions)

    objective.build()
    adequacy_const.build()

    logger.info('Problem build. Start solver')
    solver.EnableOutput()
    solver.Solve()

    logger.info('Solver finish cost=%d', solver.Objective().Value())
    logger.debug(solver.ExportModelAsLpFormat(False).replace('\\', '').replace(',_', ','))

    out_mapper = OutputMapper(solver=solver, study=study)
    for t in range(0, study.horizon):
        for name, node in study.nodes.items():
            out_mapper.set_var(name=name, t=t, vars=variables[t][name])

    return out_mapper.get_result()

