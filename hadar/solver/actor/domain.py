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

    def __init__(self, quantity: int, cost: int=0, type: str=''):
        self.cost = cost
        self.quantity = quantity
        self.type = type





class Production(DTO):

    def __init__(self, quantity: int, cost: int=0, type: str='in', id: uuid=0, exchange: Exchange = None):
        self.type = type
        self.cost = cost
        self.quantity = quantity
        self.id = id
        self.exchange = exchange


class Border(DTO):
    def __init__(self, dest: str, capacity: int, cost: int=0):
        self.dest = dest
        self.capacity = capacity
        self.cost = cost


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


class Event(DTO):
    def __init__(self, type: str, message, res=None):
        self.type = type
        self.message = message
        self.res = res


class Snapshot(DTO):
    def __init__(self):
        pass


class Start(DTO):
    def __init__(self):
        pass

class Next(DTO):
    def __init__(self):
        pass
