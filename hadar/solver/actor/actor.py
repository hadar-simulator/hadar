import time
import numpy as np
import pandas as pd

from pykka import ThreadingActor, ActorRegistry

from hadar.solver.actor.common import State
from hadar.solver.actor.domain.input import *
from hadar.solver.actor.domain.message import *
from hadar.solver.actor.ledger import LedgerConsumption, LedgerProduction, LedgerBorder


def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


@singleton
class Waiter:
    def __init__(self, wait_ms=0):
        self.updated = True
        self.wait_ms = wait_ms

    def wait(self):
        while self.updated:
            self.updated = False
            time.sleep(self.wait_ms / 1000)

    def update(self):
        self.updated = True


class Event:
    def __init__(self, type: str, message, res=None):
        self.type = type
        self.message = message
        self.res = res


class Dispatcher(ThreadingActor):

    def __init__(self, name,
                 min_exchange: int=1,
                 uuid_generate=uuid.uuid4,
                 consumptions: List[InputConsumption] = [],
                 productions: List[InputProduction] = [],
                 borders: List[InputBorder] = []
                 ):
        super().__init__()

        self.name = name
        self.consumptions = consumptions
        self.productions = productions
        self.borders = borders
        self.uuid_generate = uuid_generate

        self.t = 0
        self.state = self.build_state(self.t)

        self.waiter = Waiter()
        self.events = []

        self.actor_ref.actor_urn = name
        ActorRegistry.register(self.actor_ref)

    def build_state(self, t: int):
        """
        Build new state according to timestamp.

        :param t: timestamp (i.e. quantity array index) to use
        :return: state with all ledgers setup with correct available quantities
        """
        # Build Consumers
        consumer_ledger = LedgerConsumption()
        for cons in self.consumptions:
            consumer_ledger.add(type=cons.type, cost=cons.cost, quantity=cons.quantity[t])

        # Build Producers
        producer_ledger = LedgerProduction(uuid_generate=self.uuid_generate)
        for prod in self.productions:
            producer_ledger.add_production(cost=prod.cost, quantity=prod.quantity[t], type=prod.type)

        # Build Border
        border_ledger = LedgerBorder()
        for b in self.borders:
            border_ledger.add(dest=b.dest, cost=b.cost, quantity=b.quantity[t])

        return State(consumptions=consumer_ledger, borders=border_ledger,
                     productions=producer_ledger, rac=0, cost=0)


    def on_receive(self, message):
        """
        Mail box of actor.

        :param message: next message to process
        :return:
        """
        self.waiter.update()
        self.events.append(Event(type='recv', message=message))

        if isinstance(message, Start):
            self.broker.init()
        elif isinstance(message, Snapshot):
            return self
        elif isinstance(message, Next):
            return self.name, self.next()
        elif isinstance(message, ProposalOffer):
            ex = self.broker.receive_proposal_offer(proposal=message)
            self.events.append(Event(type='recv res', message=ex))
            return ex
        elif isinstance(message, Proposal):
            self.broker.receive_proposal(proposal=message)
        elif isinstance(message, ConsumerCanceledExchange):
            self.broker.receive_cancel_exchange(cancel=message)

    def on_stop(self):
        ActorRegistry.unregister(self.actor_ref)

    def tell_to(self, to: str, mes):
        self.events.append(Event(type='tell', message=mes))
        ActorRegistry.get_by_urn(to).tell(mes)

    def ask_to(self, to: str, mes):
        self.events.append(Event(type='ask', message=mes))
        res = ActorRegistry.get_by_urn(to).ask(mes)
        self.events.append(Event(type='ask res', message=res))
        return res

    def next(self):
        c, p, b = self.broker.compute_total()
        # plot(self)
        return c, p, b
