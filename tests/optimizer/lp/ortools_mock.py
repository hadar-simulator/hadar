#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
from ortools.linear_solver.pywraplp import Solver, Variable

from hadar.optimizer.input import DTO


class MockNumVar(DTO, Variable):
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
        self.coeffs = coeffs if coeffs else dict()

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


class MockSolver(Solver):
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
