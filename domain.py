import json
import uuid
from typing import *


class DTO:

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.viewitems())))

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.__dict__ == other.__dict__

    def __str__(self):
        return "{}({})".format(type(self).__name__, ", ".join(["{}={}".format(k, str(self.__dict__[k])) for k in sorted(self.__dict__)]))

    def __repr__(self):
        return self.__str__()


class Consumption(DTO):

    def __init__(self, cost: int, quantity: int):
        self.cost = cost
        self.quantity = quantity


class Production(DTO):

    def __init__(self, cost: int, quantity: int, type: str='in', id: uuid=0):
        self.type = type
        self.cost = cost
        self.quantity = quantity
        self.id = id


class Proposal(DTO):
    def __init__(self, id: uuid , cost: int, quantity: int, path_node: List[str]):
        self.id = id
        self.cost = cost
        self.quantity = quantity
        self.path_node = path_node


class ProposalFinal(DTO):
    def __init__(self, quantity):
        self.quantity = quantity


class ProposalOffer(Proposal):
    pass


class NodeState(DTO):
    def __init__(self, productions_used: List[Production], productions_free: List[Production], cost: int, rac: int):
        self.productions_used = productions_used
        self.productions_free = productions_free
        self.cost = cost
        self.rac = rac


class Border:
    def __init__(self, dest: str, capacity: int, cost: int):
        self.dest = dest
        self.capacity = capacity
        self.cost = cost


class Start:
    def __init__(self):
        pass

    def __str__(self):
        return "Start !"

    def __repr__(self):
        return self.__str__()
