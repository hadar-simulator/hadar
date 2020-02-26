from ortools.linear_solver.pywraplp import Solver

from hadar.solver.input import InputNode, Study
from hadar.solver.lp.domain import *
from hadar.solver.output import OutputNode, Result


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

    def get_var(self, name: str, t: int) -> LPNode:
        """
        Map InputNode to LPNode.

        :param name: node name
        :param t: timestamp
        :return: LPNode according to node name at t in study
        """
        consumptions = [LPConsumption(type=c.type, cost=float(c.cost), quantity=c.quantity[t],
                                      variable=self.solver.NumVar(0, float(c.quantity[t]), name='lol {} on {} at {}'.format(c.type, name, t)))
                        for c in self.study.nodes[name].consumptions]

        productions = [LPProduction(type=p.type, cost=float(p.cost), quantity=p.quantity[t],
                                    variable=self.solver.NumVar(0, float(p.quantity[t]), 'prod {} on {} at {}'.format(p.type, name, t)))
                       for p in self.study.nodes[name].productions]

        borders = [LPBorder(dest=b.dest, cost=float(b.cost), src=name, quantity=b.quantity[t],
                            variable=self.solver.NumVar(0, float(b.quantity[t]), 'border on {} to {} at {}'.format(name, b.dest, t)))
                   for b in self.study.nodes[name].borders]

        return LPNode(consumptions=consumptions, productions=productions, borders=borders)


class OutputMapper:
    """
    Output mapper from specific linear programming domain to global domain.
    """
    def __init__(self, solver: Solver, study: Study):
        """
        Instantiate mapper.

        :param solver: ortools solver to use to fetch variable value
        :param study: input study to reproduce structure
        """
        self.nodes = {name: OutputNode.build_like_input(input) for name, input in study.nodes.items()}

    def set_var(self, name: str, t: int, vars: LPNode):
        """
        Map linear programming node to global node (set inside intern attribute).

        :param name: node name
        :param t: timestamp index
        :param vars: linear programming node with ortools variables inside
        :return: None (use get_result)
        """
        for i in range(len(vars.consumptions)):
            self.nodes[name].consumptions[i].quantity[t] = vars.consumptions[i].quantity - vars.consumptions[i].variable.solution_value()

        for i in range(len(vars.productions)):
            self.nodes[name].productions[i].quantity[t] = vars.productions[i].variable.solution_value()

        for i in range(len(vars.borders)):
            self.nodes[name].borders[i].quantity[t] = vars.borders[i].variable.solution_value()

    def get_result(self) -> Result:
        """
        Get result.

        :return: final result after map all nodes
        """
        return Result(nodes=self.nodes)
