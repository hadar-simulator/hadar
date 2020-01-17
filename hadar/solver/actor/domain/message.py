import uuid
from typing import List


class Message:
    """
    Implement basic method for messages send to actor
    """
    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.viewitems())))

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.__dict__ == other.__dict__

    def __str__(self):
        return "{}({})".format(type(self).__name__, ", ".join(["{}={}".format(k, str(self.__dict__[k])) for k in sorted(self.__dict__)]))

    def __repr__(self):
        return self.__str__()


class Exchange(Message):
    """Exchange message to tokenize shared production"""
    def __init__(self, quantity=0, id: uuid = 0, production_type: str = '', path_node: List[str] = []):
        self.quantity = quantity
        self.id = id
        self.production_type = production_type
        self.path_node = path_node


class Proposal(Message):
    def __init__(self, production_type: str, cost: int, quantity: int, path_node: List[str]):
        self.production_type = production_type
        self.cost = cost
        self.quantity = quantity
        self.path_node = path_node


class ProposalOffer(Proposal):
    def __init__(self, production_type: str, cost: int, quantity: int, path_node: List[str], return_path_node: List[str]):
        Proposal.__init__(self, production_type, cost, quantity, path_node)
        self.return_path_node = return_path_node


class ConsumerCanceledExchange(Message):
    def __init__(self, exchanges: List[Exchange], path_node: List[str]=[]):
        self.exchanges = exchanges
        self.path_node = path_node


class Snapshot(Message):
    def __init__(self):
        pass


class Start(Message):
    def __init__(self):
        pass

class Next(Message):
    def __init__(self):
        pass