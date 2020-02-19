import numpy as np
from typing import Union, List

from ortools.linear_solver.pywraplp import Variable

from hadar.solver.input import DTO


class LPConsumption(DTO):
    """
    Consumption element for linear programming.
    """

    def __init__(self, quantity: int, variable: Variable, cost: float = 0, type: str = ''):
        """
        Instance consumption.

        :param quantity: quantity to match
        :param variable: ortools variables. represent a loss of load inside equation
        :param cost: unavailability cost
        :param type: consumption type name
        """
        self.cost = cost
        self.quantity = quantity
        self.type = type
        self.variable = variable


class LPProduction(DTO):
    """
    Production element for linear programming.
    """

    def __init__(self, quantity: int, variable: Variable, cost: float = 0, type: str = 'in'):
        """
        Instance production.

        :param quantity: production capacity
        :param variable: ortools variables. Represent production used inside equation
        :param cost: cost of use
        :param type: production type name
        """
        self.type = type
        self.cost = cost
        self.variable = variable
        self.quantity = quantity


class LPBorder(DTO):
    """
    Border element for linear programming
    """
    def __init__(self, src: str, dest: str, quantity: int, variable: Variable, cost: float = 0):
        """
        Instance border.

        :param src: node source name
        :param dest: node destination name
        :param quantity: border capacity
        :param variable: ortools variables. Represent border used inside equation
        :param cost: cost of use
        """
        self.src = src
        self.dest = dest
        self.quantity = quantity
        self.variable = variable
        self.cost = cost


class LPNode(DTO):
    """
    Node element for linear programming
    """
    def __init__(self, consumptions: List[LPConsumption], productions: List[LPProduction], borders: List[LPBorder]):
        """
        Instance node.

        :param consumptions: consumptions list
        :param productions: productions list
        :param borders: border list
        """
        self.consumptions = consumptions
        self.productions = productions
        self.borders = borders