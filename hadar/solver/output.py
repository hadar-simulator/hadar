import numpy as np

from typing import Union, List, Dict

from hadar.solver.input import *


class DTO:
    """
    Implement basic method for DTO objects
    """

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        for name, att in self.__dict__.items():
            if isinstance(att, (np.ndarray, np.generic)):
                if not np.array_equal(self.__dict__[name], other.__dict__[name]):
                    return False
            elif self.__dict__[name] != other.__dict__[name]:
                return False
        return True

    def __str__(self):
        return "{}({})".format(type(self).__name__,
                               ", ".join(["{}={}".format(k, str(self.__dict__[k])) for k in sorted(self.__dict__)]))

    def __repr__(self):
        return self.__str__()


class OutputConsumption(DTO):

    def __init__(self, quantity: Union[np.ndarray, list], cost: int = 0, type: str = ''):
        self.cost = cost
        self.quantity = np.array(quantity)
        self.type = type


class OutputProduction(DTO):

    def __init__(self, quantity: Union[np.ndarray, list], cost: int = 0, type: str = 'in'):
        self.type = type
        self.cost = cost
        self.quantity = np.array(quantity)


class OutputBorder(DTO):
    def __init__(self, dest: str, quantity: Union[np.ndarray, list], cost: int = 0):
        self.dest = dest
        self.quantity = np.array(quantity)
        self.cost = cost


class OutputNode(DTO):
    def __init__(self,
                 consumptions: List[OutputConsumption],
                 productions: List[OutputProduction],
                 borders: List[OutputBorder],
                 rac: Union[np.ndarray, List[int]],
                 cost: Union[np.ndarray, List[int]]):
        self.consumptions = consumptions
        self.productions = productions
        self.borders = borders
        self.rac = np.array(rac)
        self.cost = np.array(cost)

    @staticmethod
    def build_like_input(input: InputNode):
        output = OutputNode(consumptions=[], productions=[], borders=[], rac=[0], cost=[0])

        output.consumptions = [OutputConsumption(type=i.type, cost=i.cost, quantity=np.zeros_like(i.quantity))
                               for i in input.consumptions]
        output.productions = [OutputProduction(type=i.type, cost=i.cost, quantity=np.zeros_like(i.quantity))
                              for i in input.productions]
        output.borders = [OutputBorder(dest=i.dest, cost=i.cost, quantity=np.zeros_like(i.quantity))
                          for i in input.borders]

        size = input.consumptions[0].quantity.size if len(input.consumptions) > 0 else 0
        output.rac = np.zeros_like(size).reshape(1,)
        output.cost = np.zeros_like(size).reshape(1,)
        return output


class Result(DTO):
    def __init__(self, nodes: Dict[str, OutputNode]):
        self._nodes = nodes

    @property
    def nodes(self):
        return self._nodes
