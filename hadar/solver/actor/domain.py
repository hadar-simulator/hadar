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


class NodeQuantity(DTO):
    def __init__(self, consumptions: List[Consumption]=[], productions: List[Production]=[], borders: [Border]=[], min_exchange=1):
        self.min_exchange = min_exchange
        self.consumptions = consumptions
        self.productions = productions
        self.borders = borders


class Study(DTO):
    def __init__(self, nodes: Mapping[str, NodeQuantity]):
        self.nodes = nodes




class NodeState(DTO):
    def __init__(self, productions_used: List[Production], productions_free: List[Production], cost: int, rac: int):
        self.productions_used = productions_used
        self.productions_free = productions_free
        self.cost = cost
        self.rac = rac


