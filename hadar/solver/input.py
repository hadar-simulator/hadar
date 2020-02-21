import uuid
from typing import List, Dict, Union

import numpy as np

class DTO:
    """
    Implement basic method for DTO objects
    """
    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.__dict__ == other.__dict__

    def __str__(self):
        return "{}({})".format(type(self).__name__, ", ".join(["{}={}".format(k, str(self.__dict__[k])) for k in sorted(self.__dict__)]))

    def __repr__(self):
        return self.__str__()


class Consumption(DTO):
    """
    Consumption element.
    """

    def __init__(self, quantity: Union[np.ndarray, list], cost: int = 0, type: str = ''):
        """
        Create consumption.

        :param quantity: quantity to match
        :param cost: cost of unavailability
        :param type: type of consumption (unique for each node)
        """
        self.cost = cost
        self.quantity = np.array(quantity)
        self.type = type


class Production(DTO):
    """
    Production element
    """
    def __init__(self, quantity: Union[np.ndarray, list], cost: int = 0, type: str = 'in'):
        """
        Create production

        :param quantity: capacity production
        :param cost: cost of use
        :param type: type of production (unique for each node)
        """
        self.type = type
        self.cost = cost
        self.quantity = np.array(quantity)


class Border(DTO):
    """
    Border element
    """
    def __init__(self, dest: str, quantity: Union[np.ndarray, list], cost: int = 0):
        """
        Create border.

        :param dest: node name destination (to export)
        :param quantity: transfer capacity
        :param cost: cost of use
        """
        self.dest = dest
        self.quantity = np.array(quantity)
        self.cost = cost


class InputNode(DTO):
    """
    Node element
    """
    def __init__(self, consumptions: List[Consumption], productions: List[Production], borders: List[Border]):
        """
        Create node element.

        :param consumptions: list of consumptions inside node
        :param productions: list of productions inside node
        :param borders: list of borders inside node
        """
        self.consumptions = consumptions
        self.productions = productions
        self.borders = borders


class Study(DTO):
    """
    Main object to facilitate to build a study
    """

    def __init__(self, node_names=List[str]):
        """
        Instance study.

        :param node_names: list of node names inside network.
        """
        if len(node_names) > len(set(node_names)):
            raise ValueError('some nodes are not unique')

        self._nodes = {name: InputNode(consumptions=[], productions=[], borders=[]) for name in node_names}
        self.horizon = 0


    @property
    def nodes(self):
        return self._nodes

    def add_on_node(self, node: str, data=Union[Production, Consumption, Border]):
        """
        Attach a production or consumption into a node.

        :param node: node name to attach
        :param data: consumption or production to attach
        :return:
        """
        if node not in self._nodes.keys():
            raise ValueError('Node "{}" is not in available nodes'.format(node))

        if isinstance(data, Production):
            self._add_production(node, data)

        elif isinstance(data, Consumption):
            self._add_consumption(node, data)

        return self

    def add_border(self, src: str, dest: str, cost: int, quantity: Union[np.ndarray, List[int]]):
        """
        Add a border inside network.

        :param src: source node name
        :param dest: destination node name
        :param cost: cost of use
        :param quantity: transfer capacity
        :return:
        """
        quantity = np.array(quantity)
        if cost < 0:
            raise ValueError('border cost must be positive')
        if np.all(quantity < 0):
            raise ValueError('border quantity must be positive')
        if dest not in self._nodes.keys():
            raise ValueError('border destination must be a valid node')
        if dest in [b.dest for b in self._nodes[src].borders]:
            raise ValueError('border destination must be unique on a node')
        self._nodes[src].borders.append(Border(dest=dest, quantity=quantity, cost=cost))
        self._update_horizon(quantity)

        return self

    def _add_production(self, node: str, prod: Production):
        if prod.cost < 0:
            raise ValueError('production cost must be positive')
        prod.quantity = np.array(prod.quantity)
        if np.all(prod.quantity < 0):
            raise ValueError('production quantity must be positive')
        if prod.type in [p.type for p in self._nodes[node].productions]:
            raise ValueError('production type must be unique on a node')
        self._nodes[node].productions.append(prod)
        self._update_horizon(prod.quantity)

    def _add_consumption(self, node: str, cons: Consumption):
        if cons.cost < 0:
            raise ValueError('consumption cost must be positive')
        cons.quantity = np.array(cons.quantity)
        if np.all(cons.quantity < 0):
            raise ValueError('consumption quantity must be positive')
        if cons.type in [c.type for c in self._nodes[node].consumptions]:
            raise ValueError('consumption type must be unique on a node')
        self._nodes[node].consumptions.append(cons)
        self._update_horizon(cons.quantity)

    def _update_horizon(self, quantity):
        self.horizon = max(self.horizon, quantity.size)