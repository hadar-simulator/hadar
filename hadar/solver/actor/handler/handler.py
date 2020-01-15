import uuid
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import List

import pandas as pd
import numpy as np

from hadar.solver.actor.common import State
from hadar.solver.actor.domain.message import *


class HandlerParameter:
    def __init__(self, ask=None, tell=None, uuid_generate: uuid = uuid.uuid4, min_exchange: int = 1):
        self.ask = ask
        self.tell = tell
        self.uuid_generate = uuid_generate
        self.min_exchange = min_exchange


class Handler(ABC):
    """
    Represent an atomic behaviour. Handler update state object and call other handlers.
    Message receiving behaviour is implemented by chaining handler according to Chain of Responsabilities pattern
    """
    def __init__(self, params: HandlerParameter = None):
        self.params = params

    def set_params(self, params: HandlerParameter):
        self.params = params

    @abstractmethod
    def execute(self, state: State, message=None) -> State:
        pass


class ReturnHandler(Handler):
    """Stub handler chain. Return state value"""
    def __init__(self):
        Handler.__init__(self)

    def execute(self, state: State, message=None) -> State:
        return state


class CancelUselessImportationHandler(Handler):
    """
    Get exchange in free production and send cancel messages.
    """
    def __init__(self, next: Handler, params: HandlerParameter = None):
        Handler.__init__(self, params)
        self.next = next
        self.next.set_params(self.params)

    def execute(self, state: State, nothing=None) -> State:
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
            self.params.tell(to=path[0], mes=cancel)


class ProposeFreeProductionHandler(Handler):
    """
    Send as proposal free production.
    Check already sent production quantity and border capacities.
    """
    def __init__(self, next: Handler, params: HandlerParameter = None):
        Handler.__init__(self, params)
        self.next = next
        self.next.set_params(self.params)

    def execute(self, state: State, nothing=None) -> State:
        for p_id, (p_cost, p_quantity, _, _, _ ) in state.productions.filter_free_productions().iterrows():
            prod_sent = state.exchanges.sum_production(production_id=p_id)
            qt = p_quantity - prod_sent

            for b_id, (b_cost, b_quantity) in state.borders.ledger.iterrows():
                export = state.exchanges.sum_border(name=b_id)
                qt = min(qt, b_quantity - export)
                prop = Proposal(production_id=p_id,
                                cost=p_cost + b_cost,
                                quantity=qt,
                                path_node=[state.name])
                self.params.tell(to=b_id, mes=prop)

        return self.next.execute(deepcopy(state))


class CancelExportationHandler(Handler):
    """Cancel exchange. If middle node forward cancel"""
    def __init__(self, on_producer: Handler, on_forward: Handler, params: HandlerParameter = None):
        Handler.__init__(self, params)
        self.on_producer = on_producer
        self.on_producer.set_params(self.params)
        self.on_forward = on_forward
        self.on_forward.set_params(self.params)

    def execute(self, state: State, message=None) -> State:
        # delete exchange in ledger
        state.exchanges.delete_all(message.exchanges)

        # Forward if path node has next
        if len(message.path_node) > 1:
            cancel = deepcopy(message)
            cancel.path_node = cancel.path_node[1:]
            self.params.tell(to=cancel.path_node[0], mes=cancel)
            return self.on_forward.execute(deepcopy(state), message)

        return self.on_producer.execute(deepcopy(state), message)