import uuid
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import List, Tuple, Any

import pandas as pd
import numpy as np

from hadar.solver.actor.common import State
from hadar.solver.actor.domain.message import *


class HandlerParameter:
    """Global parameters used by all handlers"""
    def __init__(self, ask=None, tell=None, uuid_generate: uuid = uuid.uuid4, min_exchange: int = 1):
        self.ask = ask
        self.tell = tell
        self.uuid_generate = uuid_generate


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
    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        pass


class ReturnHandler(Handler):
    """Stub handler chain. Return state value"""
    def __init__(self):
        Handler.__init__(self)

    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        """
        Return state and message without any change.

        :param state: current state
        :param message: message receive
        :return: same state, same message
        """
        return state, message


class CancelUselessImportationHandler(Handler):
    """
    Cancel exchanges find in not free productions
    """
    def __init__(self, next: Handler, params: HandlerParameter = None):
        """
        Create handler.

        :param next: handler to execute at this end of process
        :param params: handler parameters (use only if handler is first of the chain)
        """
        Handler.__init__(self, params)
        self.next = next
        self.set_params(params)

    def set_params(self, params: HandlerParameter):
        self.params = params
        self.next.set_params(params)

    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        """
        Execute process.

        :param state: current state
        :param message: message receive from dispatcher. (Not used by handler)
        :return: new state, response message. (Not response from handler)
        """
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
        """
        Create handler.

        :param next: handler to execute at this end of process
        :param params: handler parameters (use only if handler is first of the chain)
        """
        Handler.__init__(self, params)
        self.next = next
        self.set_params(params)

    def set_params(self, params: HandlerParameter):
        self.params = params
        self.next.set_params(params)

    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        """
        Execute process.

        :param state: current state
        :param message: message received from dispatcher. Not used by this handler
        :return: new state, response message (Not response from this handler)
        """
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
    """Cancel exchange."""
    def __init__(self, next: Handler, params: HandlerParameter = None):
        """
        Create handler.

        :param next: handler to execute after delete exchange.
        :param params: handler parameters (use only if handler is first of the chain)
        """
        Handler.__init__(self, params)
        self.next = next
        self.next.set_params(params)

    def set_params(self, params: HandlerParameter):
        self.params = params
        self.next.set_params(params)

    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        """
        Execute process.

        :param state: current state
        :param message: ConsumerCancelExchange message
        :return: new state, response message (Not response from handler)
        """
        # delete exchange in ledger
        state.exchanges.delete_all(message.exchanges)

        return self.next.execute(deepcopy(state), deepcopy(message))


class BackwardMessageHandler(Handler):
    """Forward message to border"""
    def __init__(self, after_backward: Handler, on_resume: Handler, type: str, params: HandlerParameter = None):
        """
        Create Handler
        :param after_backward: handler to execute after backward
        :param on_resume: handler to execute if not backward
        :param type: give what kind of connection 'ask' or 'tell'
        """
        Handler.__init__(self, params)
        self.type = type
        self.after_backward = after_backward
        self.on_resume = on_resume
        self.set_params(params)

    def set_params(self, params: HandlerParameter):
        self.params = params
        self.after_backward.set_params(params)
        self.on_resume.set_params(params)

    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        if len(message.path_node) > 1:
            message.path_node = message.path_node[1:]
            if self.type == 'ask':
                res = self.params.ask(to=message.path_node[0], mes=message)
                return self.after_backward.execute(deepcopy(state), deepcopy(res))

            elif self.type == 'tell':
                self.params.tell(to=message.path_node[0], mes=message)
                return self.after_backward.execute(deepcopy(state), None)

        return self.on_resume.execute(deepcopy(state), deepcopy(message))


class AcceptExchangeHandler(Handler):
    """Create available exchanges according to proposal"""
    def __init__(self, next: Handler, min_exchange: int = 1, params: HandlerParameter = None):
        """
        Create Handler.

        :param next: handler to call after process
        :param min_exchange: production are tokenized when exchanged. Set the tokenize size
        :param params: current handler parameters
        """
        Handler.__init__(self, params)
        self.next = next
        self.min_exchange = min_exchange
        self.set_params(params)

    def set_params(self, params: HandlerParameter):
        self.params = params
        self.next.set_params(params)

    def execute(self, state: State, proposal: Any = None) -> Tuple[State, Any]:
        """
        Compute available exchanges according to production already sent.

        :param state: current state
        :param proposal: ProposalOffer message
        :return: (state, [available exchanges])
        """
        # Check production remain capacity
        quantity_available = state.productions.find_production(proposal.production_id).quantity
        quantity_used = state.exchanges.sum_production(proposal.production_id)

        # Send available exchange
        quantity_exchange = min(proposal.quantity, quantity_available - quantity_used)
        ex = self._generate_exchanges(quantity=quantity_exchange,
                                      production_id=proposal.production_id,
                                      path_node=proposal.return_path_node)

        return self.next.execute(deepcopy(state), deepcopy(ex))

    def _generate_exchanges(self, production_id: int, quantity: int, path_node: List[str]):
        """
        Generate list to exchanges to fill available quantity with minimum exchange capacity.

        :param production_id: id production to embedded
        :param quantity:  quantity to use to generate exchange list
        :param path_node: path node to embedded
        :return: list of exchanges. sum of capacities equals or less quantity asked
        """
        length = int(quantity / self.min_exchange)
        exchanges = [Exchange(quantity=self.min_exchange,
                              id=self.params.uuid_generate(),
                              production_id=production_id,
                              path_node=path_node)
                     for i in range(0, length)]

        remain = quantity - length*self.min_exchange
        if remain:
            exchanges += [Exchange(quantity=remain, id=self.params.uuid_generate(), production_id=production_id, path_node=path_node)]
        return exchanges


class SaveExchangeHandler(Handler):
    """Save exchange to ledger"""
    def __init__(self, next: Handler, params: HandlerParameter = None):
        Handler.__init__(self, params)
        self.next = next
        self.set_params(params)

    def set_params(self, params: HandlerParameter):
        self.params = params
        self.next.set_params(params)

    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        """
        Save exchanges in ledger.

        :param state: current state
        :param message: exchanges
        :return: new sate, same exchanges
        """

        for e in deepcopy(message):
            if e.quantity > 0:
                e.path_node = SaveExchangeHandler.trim_path(state, deepcopy(e.path_node))
                state.exchanges.add(e)
        return self.next.execute(deepcopy(state), deepcopy(message))
    
    @staticmethod
    def trim_path(state: State, path: List[str]):
        """
        trim uphill nodes in path.

        :param state: current state
        :param path: whole path from exchange producer
        :return: trimed path with only next nodes
        """
        while len(path) > 0 and path[0] != state.name:
            del path[0]
        del path[0]
        return path


class CheckOfferBorderCapacityHandler(Handler):
    """Check border capacity to respond to offer"""
    def __init__(self, next: Handler, params: HandlerParameter = None):
        """
        Create handler
        :param next: handler to execute after check border capacity
        :param params: parameters to use
        """
        Handler.__init__(self, params)
        self.next = next
        self.set_params(params)

    def set_params(self, params: HandlerParameter):
        self.params = params
        self.next.set_params(params)

    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        """
        Check border capacity, update message with new quantity.

        :param state: current state
        :param message: ProposalOffer
        :return: (new state, response message
        """
        border = state.borders.find_border_in_path(message.return_path_node)
        free_border_capacity = border.quantity - state.exchanges.sum_border(border.name)
        if not free_border_capacity:
            return deepcopy(state), []

        message.quantity = min(free_border_capacity, message.quantity)
        return self.next.execute(deepcopy(state), deepcopy(message))
