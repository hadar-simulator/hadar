from ortools.linear_solver.pywraplp import Solver

from hadar.solver.input import InputNode, Study
from hadar.solver.lp.domain import *
from hadar.solver.output import OutputNode, Result


class InputMapper:

    def __init__(self, solver: Solver, study: Study):
        self.solver = solver
        self.study = study

    def get_var(self, name: str, t: int) -> LPNode:
        consumptions = [LPConsumption(type=c.type, cost=float(c.cost), quantity=c.quantity[t])
                        for c in self.study.nodes[name].consumptions]
        productions = [LPProduction(type=p.type, cost=float(p.cost),
                                    quantity=self.solver.NumVar(0, float(p.quantity[t]), 'prod {} on {}'.format(p.type, name)))
                       for p in self.study.nodes[name].productions]
        borders = [LPBorder(dest=b.dest, cost=float(b.cost), src=name,
                            quantity=self.solver.NumVar(0, float(b.quantity[t]), 'border on {} to {}'.format(name, b.dest)))
                   for b in self.study.nodes[name].borders]

        return LPNode(consumptions=consumptions, productions=productions, borders=borders)

class OutputMapper:

    def __init__(self, solver: Solver, study: Study):
        self.nodes = {name: OutputNode.build_like_input(input) for name, input in study.nodes.items()}

    def set_var(self, name: str, t: int, vars: LPNode):
        for i in range(len(vars.consumptions)):
            self.nodes[name].consumptions[i].quantity[t] = vars.consumptions[i].quantity

        for i in range(len(vars.productions)):
            self.nodes[name].productions[i].quantity[t] = vars.productions[i].quantity.solution_value()

        for i in range(len(vars.borders)):
            self.nodes[name].borders[i].quantity[t] = vars.borders[i].quantity.solution_value()

    def get_result(self) -> Result:
        return Result(nodes=self.nodes)
