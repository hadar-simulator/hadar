import numpy as np
from typing import Union, List

from ortools.linear_solver.pywraplp import Variable

from hadar.solver.input import DTO


class LPConsumption(DTO):

    def __init__(self, quantity: int, variable: Variable, cost: float = 0, type: str = ''):
        self.cost = cost
        self.quantity = quantity
        self.type = type
        self.variable = variable


class LPProduction(DTO):

    def __init__(self, quantity: int, variable: Variable, cost: float = 0, type: str = 'in'):
        self.type = type
        self.cost = cost
        self.variable = variable
        self.quantity = quantity


class LPBorder(DTO):
    def __init__(self, src: str, dest: str, quantity: int, variable: Variable, cost: float = 0):
        self.src = src
        self.dest = dest
        self.quantity = quantity
        self.variable = variable
        self.cost = cost


class LPNode(DTO):
    def __init__(self, consumptions: List[LPConsumption], productions: List[LPProduction], borders: List[LPBorder]):
        self.consumptions = consumptions
        self.productions = productions
        self.borders = borders