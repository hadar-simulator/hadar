import uuid
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import List

import pandas as pd
import numpy as np

from hadar.solver.actor.common import State
from hadar.solver.actor.domain.message import *
from hadar.solver.actor.actor import HandlerParameter


class Handler(ABC):
    """
    Represent an atomic behaviour. Handler update state object and call other handlers.
    Message receiving behaviour is implemented by chaining handler according to Chain of Responsabilities pattern
    """
    def __init__(self):
        params = HandlerParameter()
        self.ask = params.ask
        self.tell = params.tell
        self.uuid_generate = params.uuid_generate
        self.min_exchange = params.min_exchange

    @abstractmethod
    def execute(self, state: State) -> State:
        pass


class ReturnHandler(Handler):
    """Stub handler chain. Return state value"""
    def __init__(self):
        Handler.__init__(self)

    def execute(self, state: State) -> State:
        return state

class CancelExchangeUselessHandler(Handler):
    """
    Get exchange in free production and send cancel messages.
    """
    def __init__(self, next: Handler):
        Handler.__init__(self)
        self.next = next

    def execute(self, state: State) -> State:
        useless = state.productions.filter_useless_exchanges()
        exs = useless['exchange'].values

        state.exchanges.delete_all(exs)
        state.productions.delete_all(useless.index)
        self._send_cancel_exchange(exs)

        return self.next.execute(deepcopy(state))

    def _send_cancel_exchange(self, exchanges: List[Exchange]):
        """
        Send canceled exchange order regrouped by production.

        :param exchanges: exchanges to cancel
        :return:
        """
        productions = {}
        for ex in exchanges:
            if ex.production_id not in productions.keys():
                productions[ex.production_id] = [[], []]
            productions[ex.production_id][0].append(ex)
            productions[ex.production_id][1] = ex.path_node

        for prod_id, (ex, path) in productions.items():
            cancel = ConsumerCanceledExchange(exchanges=ex, path_node=path)
            self.tell(to=path[0], mes=cancel)


class ProposeFreeProduction(Handler):
    def __init__(self, next: Handler):
        Handler.__init__(self)
        self.next = next

    def execute(self, state: State) -> State:
        pass


class StartHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        self.handler = CancelExchangeUselessHandler(
            next=ProposeFreeProduction(
                next=ReturnHandler()
            ))

    def execute(self, state: State) -> State:
        return self.handler.execute(deepcopy(state))