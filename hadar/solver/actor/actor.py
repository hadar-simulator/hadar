import logging
import time
import uuid
from typing import Callable, List

from pykka import ThreadingActor, ActorRegistry

from hadar.solver.output import *
from hadar.solver.input import *
from hadar.solver.actor.handler.entry import *
from hadar.solver.actor.handler.handler import AdequacyHandler, ReturnHandler, HandlerParameter, State
from hadar.solver.actor.ledger import *
from hadar.solver.actor.domain.message import *

class Waiter:
    """
    Waiter are updated by all actor at each message receive.
    Waiter determine when actor exchanges are finished, when anyone update it.
    """
    def __init__(self, wait_ms=0):
        """
        Create instance.

        :param wait_ms: waiting time for each loop
        """
        self.updated = True
        self.wait_ms = wait_ms

    def wait(self):
        """
        Endlessly loop. Stop only when actor don't notify waiter during a full time loop.

        :return:
        """
        while self.updated:
            self.updated = False
            time.sleep(self.wait_ms / 1000)

    def update(self):
        """
        Method used by actor to pock waiter that actors still exchange.

        :return:
        """
        self.updated = True


class Event:
    """
    Meta object to store message receive by actor.
    """
    def __init__(self, type: str, message, res=None):
        self.type = type
        self.message = message
        self.res = res


class Dispatcher(ThreadingActor):
    """
    Main actor. It optimize it local adequacy by exchange productions with its neighborhood
    """
    def __init__(self, name,
                 uuid_generate=uuid.uuid4,
                 waiter: Waiter = None,
                 input: InputNode = None):
        """
        Initiate actor.

        :param name: actor (node) name
        :param uuid_generate: uuid generate to use when tokenize production
        :param waiter: waiter instance to pock
        :param input: input node data to perform adequacy at best cost
        """
        super().__init__()

        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)

        # Save constructor params
        self.name = name
        self.consumptions = input.consumptions
        self.productions = input.productions
        self.borders = input.borders
        self.uuid_generate = uuid_generate

        # Instantiate output data
        self.out_node = OutputNode.build_like_input(input)

        # Set time horizon
        if self.consumptions:
            self.limit = self.consumptions[0].quantity.size
        elif self.productions:
            self.limit = self.productions[0].quantity.size
        elif self.borders:
            self.limit = self.borders[0].quantity.size
        self.t = 0

        # Setup waiter and and event sink
        self.waiter = waiter
        self.events = []

        # Setup handlers
        params = HandlerParameter(ask=self.ask_to, tell=self.tell_to, uuid_generate=self.uuid_generate)
        self.adequacy = AdequacyHandler(next=ReturnHandler())
        self.start = StartHandler(params=params)
        self.proposal = ProposalHandler(params=params)
        self.offer = ProposalOfferHandler(params=params)
        self.cancel_consumer_exchange = CanceledCustomerExchangeHandler(params=params)

        # Build first state
        self.state = Dispatcher.build_state(name=self.name, consumptions=self.consumptions, borders=self.borders,
                                            productions=self.productions, uuid_generate=self.uuid_generate, t=self.t)
        self.state, _ = self.adequacy.execute(self.state)

        # Registry actor
        self.actor_ref.actor_urn = name
        ActorRegistry.register(self.actor_ref)

    @staticmethod
    def build_state(name: str,
                    consumptions: List[Consumption],
                    borders: List[Border],
                    productions: List[Production],
                    uuid_generate: Callable, t: int) -> State:
        """
        Build new state according to timestamp.

        :param t: timestamp (i.e. quantity array index) to use
        :return: state with all ledgers setup with correct available quantities
        """
        # Build Consumers
        consumer_ledger = LedgerConsumption()
        for cons in consumptions:
            consumer_ledger.add(type=cons.type, cost=cons.cost, quantity=cons.quantity[t])

        # Build Producers
        producer_ledger = LedgerProduction(uuid_generate=uuid_generate)
        for prod in productions:
            producer_ledger.add_production(cost=prod.cost, quantity=prod.quantity[t], type=prod.type)

        # Build Border
        border_ledger = LedgerBorder()
        for b in borders:
            border_ledger.add(dest=b.dest, cost=b.cost, quantity=b.quantity[t])

        return State(name=name, consumptions=consumer_ledger, borders=border_ledger,
                     productions=producer_ledger, rac=0, cost=0)

    def on_receive(self, message):
        """
        Mail box of actor.

        :param message: next message to process
        :return:
        """
        self.logger.debug('%s receive message %s', self.name, message)

        res = None
        if isinstance(message, Start):
            self.state, _ = self.start.execute(self.state, message)

        elif isinstance(message, Snapshot):
            res = self

        elif isinstance(message, Next):
            res = self.name, self.next()

        elif isinstance(message, ProposalOffer):
            self.waiter.update()
            self.state, res = self.offer.execute(self.state, message)

        elif isinstance(message, Proposal):
            self.waiter.update()
            self.state, _ = self.proposal.execute(self.state, message)

        elif isinstance(message, ConsumerCanceledExchange):
            self.waiter.update()
            self.state, _ = self.cancel_consumer_exchange.execute(self.state, message)

        if res:
            self.logger.debug('%s response message %s', self.name, res)
        return res

    def on_stop(self):
        """
        Unregister actor
        :return:
        """
        ActorRegistry.unregister(self.actor_ref)

    def tell_to(self, to: str, mes):
        """
        Send message to asked actor using actor registry.

        :param to: actor name
        :param mes: message to send
        :return:
        """
        self.events.append(Event(type='tell', message=mes))
        ActorRegistry.get_by_urn(to).tell(mes)

    def ask_to(self, to: str, mes):
        """
        Send mess to asked actor using actor registry.

        :param to: actor name
        :param mes: message to send
        :return: actor response
        """
        self.events.append(Event(type='ask', message=mes))
        res = ActorRegistry.get_by_urn(to).ask(mes)
        self.events.append(Event(type='ask res', message=res))
        return res

    def next(self) -> OutputNode:
        """
        Handle next message. Update result. pass to next timestamp.

        :return: return OutputNode only if they have no more timestamp
        """
        self.out_node = self.compute_total(out_node=self.out_node, state=self.state, t=self.t)
        if self.t + 1 < self.limit:
            self.t += 1
            self.state = Dispatcher.build_state(name=self.name, consumptions=self.consumptions, borders=self.borders,
                                                productions=self.productions, uuid_generate=self.uuid_generate,
                                                t=self.t)
        else:
            return self.out_node

    @staticmethod
    def compute_total(out_node: OutputNode, state: State, t: int):
        """
        Compute dispatcher result:
        - copy initial consumption quantities
        - get production quantity used
        - sum production send to border

        :param out_node: OutputNode used by dispatcher to collect result
        :param state: current dispatcher state
        :param t: timestamp to update inside output result
        :return: new out_node with quantities updated
        """
        for i, _ in enumerate(out_node.consumptions):
            type = out_node.consumptions[i].type
            out_node.consumptions[i].quantity[t] = state.consumptions.find_consumption(type)['quantity']

        for i, _ in enumerate(out_node.productions):
            type = out_node.productions[i].type
            qt = state.productions.get_production_quantity(type=type, used=True)
            qt += state.exchanges.sum_production(production_type=type)
            out_node.productions[i].quantity[t] = qt

        for i, _ in enumerate(out_node.borders):
            dest = out_node.borders[i].dest
            out_node.borders[i].quantity[t] = state.exchanges.sum_border(name=dest)

        return out_node
