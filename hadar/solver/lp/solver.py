from ortools.linear_solver.pywraplp import Solver

from hadar.solver.lp.domain import *
from hadar.solver.input import InputNode, Study
from hadar.solver.lp.mapper import InputMapper, OutputMapper
from hadar.solver.output import OutputNode, Result


class ObjectiveBuilder:
    def __init__(self, solver: Solver):
        self.objective = solver.Objective()
        self.objective.SetMinimization()

    def add_productions(self, prods: List[LPProduction]):
        for prod in prods:
            self.objective.SetCoefficient(prod.quantity, prod.cost)

    def add_borders(self, borders: List[LPBorder]):
        for border in borders:
            self.objective.SetCoefficient(border.quantity, border.cost)

    def build(self):
        pass


class AdequacyBuilder:
    def __init__(self, solver: Solver):
        self.constraints = {}
        self.borders = []
        self.solver = solver

    def add_node(self, name, node: LPNode):
        load = sum([c.quantity for c in node.consumptions])*1.0
        ct = self.solver.Constraint(load, load)
        for prod in node.productions:
            ct.SetCoefficient(prod.quantity, 1)
        for bord in node.borders:
            self.borders.append(bord)
            ct.SetCoefficient(bord.quantity, -1)
        self.constraints[name] = ct

    def build(self):
        # Apply import border in adequacy
        for bord in self.borders:
            self.constraints[bord.dest].SetCoefficient(bord.quantity, 1)


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

    objective.build()
    adequacy_const.build()

    solver.EnableOutput()
    solver.Solve()

    out_mapper = OutputMapper(solver=solver, study=study)
    for t in range(0, study.horizon):
        for name, node in study.nodes.items():
            out_mapper.set_var(name=name, t=t, vars=variables[t][name])

    print('\n--- Minimum objective function value = %d' % solver.Objective().Value())
    print(solver.ExportModelAsLpFormat(False).replace('\\', '').replace(',_', ','), sep='\n')
    return out_mapper.get_result()

