from ortools.linear_solver.pywraplp import Solver

from hadar.solver.input import DTO


class MockNumVar(DTO):
    def __init__(self, min: float, max: float, name: str):
        self.min = min
        self.max = max
        self.name = name

    def solution_value(self):
        return self.max


class MockConstraint(DTO):
    def __init__(self, min: float, max: float, coeffs=None):
        self.min = min
        self.max = max
        self.coeffs = coeffs if coeffs else {}

    def SetCoefficient(self, var: MockNumVar, cost: int):
        self.coeffs[var] = cost


class MockObjective(DTO):
    def __init__(self, min=False, coeffs=None):
        self.min = min
        self.coeffs = coeffs if coeffs else {}

    def SetMinimization(self):
        self.min = True

    def SetCoefficient(self, var: MockNumVar, cost: int):
        self.coeffs[var] = cost

    def Value(self):
        return 0


class MockSolver:
    def __init__(self):
        pass

    def NumVar(self, min: float, max: float, name: str = ''):
        return MockNumVar(min, max, name)

    def Objective(self) -> MockObjective:
        return MockObjective()

    def Constraint(self, min: int, max: int):
        return MockConstraint(min, max)

    def Solve(self):
        pass

    def EnableOutput(self):
        pass

    def ExportModelAsLpFormat(self, toggle: bool):
        return ''
