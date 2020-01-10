import uuid

import numpy as np

class DTO:
    """
    Implement basic method for DTO objects
    """
    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.viewitems())))

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.__dict__ == other.__dict__

    def __str__(self):
        return "{}({})".format(type(self).__name__, ", ".join(["{}={}".format(k, str(self.__dict__[k])) for k in sorted(self.__dict__)]))

    def __repr__(self):
        return self.__str__()


class InputConsumption(DTO):

    def __init__(self, quantity: np.ndarray, cost: int = 0, type: str = ''):
        self.cost = cost
        self.quantity = quantity
        self.type = type


class InputProduction(DTO):

    def __init__(self, quantity: np.ndarray, cost: int = 0, type: str = 'in'):
        self.type = type
        self.cost = cost
        self.quantity = quantity


class InputBorder(DTO):
    def __init__(self, dest: str, quantity: np.ndarray, cost: int = 0):
        self.dest = dest
        self.quantity = quantity
        self.cost = cost
