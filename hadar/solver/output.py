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
    """
    Consumption element
    """
    def __init__(self, quantity: Union[np.ndarray, list], cost: int = 0, type: str = ''):
        """
        Create instance.

        :param quantity: quantity matched by node
        :param cost: cost of unavailability
        :param type: consumption type (unique in a node)
        """
        self.cost = cost
        self.quantity = np.array(quantity)
        self.type = type


class OutputProduction(DTO):
    """
    Production element
    """
    def __init__(self, quantity: Union[np.ndarray, list], cost: int = 0, type: str = 'in'):
        """
        Create instance.

        :param quantity: capacity used by node
        :param cost: cost of use
        :param type: production type (unique in a node)
        """
        self.type = type
        self.cost = cost
        self.quantity = np.array(quantity)


class OutputBorder(DTO):
    """
    Border element
    """
    def __init__(self, dest: str, quantity: Union[np.ndarray, list], cost: int = 0):
        """
        Create instance.

        :param dest: destination node name
        :param quantity: capacity used
        :param cost: cost of use
        """
        self.dest = dest
        self.quantity = np.array(quantity)
        self.cost = cost


class OutputNode(DTO):
    """
    Node element
    """
    def __init__(self,
                 consumptions: List[OutputConsumption],
                 productions: List[OutputProduction],
                 borders: List[OutputBorder]):
        """
        Create Node.

        :param consumptions: consumptions list
        :param productions: productions list
        :param borders:  border list
        """
        self.consumptions = consumptions
        self.productions = productions
        self.borders = borders

    @staticmethod
    def build_like_input(input: InputNode):
        """
        Use an input node to create an output node. Keep list elements fill quantity by zeros.

        :param input: InputNode to copy
        :return: OutputNode like InputNode with all quantity at zero
        """
        output = OutputNode(consumptions=[], productions=[], borders=[])

        output.consumptions = [OutputConsumption(type=i.type, cost=i.cost, quantity=np.zeros_like(i.quantity))
                               for i in input.consumptions]
        output.productions = [OutputProduction(type=i.type, cost=i.cost, quantity=np.zeros_like(i.quantity))
                              for i in input.productions]
        output.borders = [OutputBorder(dest=i.dest, cost=i.cost, quantity=np.zeros_like(i.quantity))
                          for i in input.borders]
        return output


class Result(DTO):
    """
    Result of study
    """
    def __init__(self, nodes: Dict[str, OutputNode]):
        """
        Create result
        :param nodes: list of nodes present in network
        """
        self._nodes = nodes

    @property
    def nodes(self):
        return self._nodes
