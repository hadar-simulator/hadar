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
    """Exchange token to be send"""
    def __init__(self, quantity=0, id: uuid = 0, production_type: str = '', path_node: List[str] = []):
        """
        Create instance exchange message.

        :param quantity: quality of items to exchanges. Quantity is not divisible.
        :param id: unique id of this exchanges. It's the same as production token
        :param production_type: type of production used
        :param path_node: path node inside network te retrieve producer
        """
        self.quantity = quantity
        self.id = id
        self.production_type = production_type
        self.path_node = path_node


class Proposal(Message):
    """Proposal capacity production to be spread accros network"""
    def __init__(self, production_type: str, cost: int, quantity: int, path_node: List[str]):
        """
        Create instance.

        :param production_type: production type available
        :param cost: cost of production
        :param quantity: sum of quantity available
        :param path_node: path node inside network to retrieve producer
        """
        self.production_type = production_type
        self.cost = cost
        self.quantity = quantity
        self.path_node = path_node


class ProposalOffer(Proposal):
    """Offer send by consumer as a response to a proposal from a producer"""
    def __init__(self, production_type: str, cost: int, quantity: int, path_node: List[str], return_path_node: List[str]):
        """
        Create instance.

        :param production_type: production type asked
        :param cost: cost of productions asked (added with border cost during transfer)
        :param quantity: quantity asked
        :param path_node: path node inside network to retrieve producer
        :param return_path_node: path node inside network to retrieve consumer
        """
        Proposal.__init__(self, production_type, cost, quantity, path_node)
        self.return_path_node = return_path_node


class ConsumerCanceledExchange(Message):
    """Order send by consumer to cancel exchange"""
    def __init__(self, exchanges: List[Exchange], path_node: List[str]=[]):
        """
        Create instance.

        :param exchanges: exchanges to cancel
        :param path_node: path node to follow to retrieve producer
        """
        self.exchanges = exchanges
        self.path_node = path_node


class Snapshot(Message):
    """Message send by orchestrator to backup a snapshot of an actor state"""
    def __init__(self):
        pass  # Standalone message


class Start(Message):
    """Message send by orchestrator to start exchanges between actors"""
    def __init__(self):
        pass  # Standalone message


class Next(Message):
    """Message send by orchestrator to actor to force to go to the next timestamp"""
    def __init__(self):
        pass  # Standalone message
