import uuid
from typing import List, Dict, Union

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


class Consumption(DTO):

    def __init__(self, quantity: Union[np.ndarray, list], cost: int = 0, type: str = ''):
        self.cost = cost
        self.quantity = np.array(quantity)
        self.type = type


class Production(DTO):

    def __init__(self, quantity: Union[np.ndarray, list], cost: int = 0, type: str = 'in'):
        self.type = type
        self.cost = cost
        self.quantity = np.array(quantity)


class Border(DTO):
    def __init__(self, dest: str, quantity: Union[np.ndarray, list], cost: int = 0):
        self.dest = dest
        self.quantity = np.array(quantity)
        self.cost = cost


class InputNode(DTO):
    def __init__(self, consumptions: List[Consumption], productions: List[Production], borders: List[Border]):
        self.consumptions = consumptions
        self.productions = productions
        self.borders = borders


class Study(DTO):
    """
    Main object to parameterize network study
    """

    def __init__(self, node_names=List[str]):
        """

        :param node_names:
        """
        if len(node_names) > len(set(node_names)):
            raise ValueError('some nodes are not unique')

        self._nodes = {name: InputNode(consumptions=[], productions=[], borders=[]) for name in node_names}



    @property
    def nodes(self):
        return self._nodes

    def add(self, node: str, data=Union[Production, Consumption, Border]):
        """

        :param node:
        :param data:
        :return:
        """
        if node not in self._nodes.keys():
            raise ValueError('Node "{}" is not in available nodes'.format(node))
        pass

        if isinstance(data, Production):
            self._add_production(node, data)

        elif isinstance(data, Consumption):
            self._add_consumption(node, data)

        elif isinstance(data, Border):
            self._add_border(node, data)

        return self

    def _add_production(self, node: str, prod: Production):
        if prod.cost < 0:
            raise ValueError('production cost must be positive')
        if prod.quantity < 0:
            raise ValueError('production quantity must be positive')
        if prod.type in [p.type for p in self._nodes[node].productions]:
            raise ValueError('production type must be unique on a node')
        self._nodes[node].productions.append(prod)

    def _add_consumption(self, node: str, cons: Consumption):
        if cons.cost < 0:
            raise ValueError('consumption cost must be positive')
        if cons.quantity < 0:
            raise ValueError('consumption quantity must be positive')
        if cons.type in [c.type for c in self._nodes[node].consumptions]:
            raise ValueError('consumption type must be unique on a node')
        self._nodes[node].consumptions.append(cons)

    def _add_border(self, node: str, border: Border):
        if border.cost < 0:
            raise ValueError('border cost must be positive')
        if border.quantity < 0:
            raise ValueError('border quantity must be positive')
        if border.dest not in self._nodes.keys():
            raise ValueError('border destination must be a valid node')
        if border.dest in [b.dest for b in self._nodes[node].borders]:
            raise ValueError('border destination must be unique on a node')
        self._nodes[node].borders.append(border)
