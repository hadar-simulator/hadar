import uuid

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Tuple, List

from hadar.solver.actor.domain.message import *
from hadar.solver.actor.ledger import *
from hadar.solver.input import DTO


class State(DTO):
    """
    Represent current adequacy configuration. Each Handler has to update and forward this state.
    """
    def __init__(self, name: str, consumptions: LedgerConsumption, borders: LedgerBorder,
                 productions: LedgerProduction, rac: int, cost: int):
        """
        Create instance.

        :param name: node's name
        :param consumptions: consumptions list to match
        :param borders: borders capacity list
        :param productions: productions capacity list
        :param rac: remain capacity
        :param cost: global adequacy cost
        """
        self.name = name
        self.consumptions = consumptions
        self.borders = borders
        self.productions = productions
        self.exchanges = LedgerExchange()
        self.rac = rac
        self.cost = cost


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
        exs = state.exchanges.get_exchanges(useless.index.values)

        state.exchanges.delete_all(exs)
        state.productions.delete_all(useless.index)
        self._send_cancel_exchange(exs)

        return self.next.execute(deepcopy(state))

    def _send_cancel_exchange(self, exchanges: List[Exchange]):
        """
        Send canceled exchange order regrouped by producer.

        :param exchanges: exchanges to cancel
        :return:
        """
        productions = {}
        for ex in exchanges:
            path = tuple(ex.path_node)
            if path not in productions.keys():
                productions[path] = []
            productions[path].append(ex)

        for path, exchanges in productions.items():
            cancel = ConsumerCanceledExchange(exchanges=exchanges, path_node=list(path))
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
        self.forward = ForwardMessageHandler(next=ReturnHandler())
        self.set_params(params)

    def set_params(self, params: HandlerParameter):
        self.params = params
        self.next.set_params(params)
        self.forward.set_params(params)

    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        """
        Execute process.

        :param state: current state
        :param message: message received from dispatcher. Not used by this handler
        :return: new state, response message (Not response from this handler)
        """
        for p_type, (p_cost, p_quantity) in state.productions.group_free_productions().iterrows():
            prod_sent = state.exchanges.sum_production(production_type=p_type)
            qt = p_quantity - prod_sent
            prop = Proposal(production_type=p_type, cost=p_cost, quantity=qt, path_node=[])

            self.forward.execute(deepcopy(state), deepcopy(prop))

        return self.next.execute(deepcopy(state))


class ForwardMessageHandler(Handler):
    """Forward message to borders according to remain capacity"""
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
        Forward message to borders.

        :param state: current state
        :param message: message with quantity and path_node properties
        :return: same state, messages (not for this handler)
        """
        for b_id, (b_cost, b_quantity) in state.borders.ledger.iterrows():
            export = state.exchanges.sum_border(name=b_id)
            copy = deepcopy(message)
            copy.quantity = min(message.quantity, b_quantity - export)
            copy.cost += b_cost
            copy.path_node = [state.name] + message.path_node
            self.params.tell(to=b_id, mes=copy)

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
    def __init__(self, next: Handler, params: HandlerParameter = None):
        """
        Create Handler.

        :param next: handler to call after process
        :param min_exchange: production are tokenized when exchanged. Set the tokenize size
        :param params: current handler parameters
        """
        Handler.__init__(self, params)
        self.next = next
        self.set_params(params)

    def set_params(self, params: HandlerParameter):
        self.params = params
        self.next.set_params(params)

    def execute(self, state: State, offer: Any = None) -> Tuple[State, Any]:
        """
        Compute available exchanges according to production already sent.

        :param state: current state
        :param offer: ProposalOffer message
        :return: (state, [available exchanges])
        """
        prod_total = state.productions.get_free_productions_by_type(type=offer.production_type)
        prod_available = state.exchanges.filter_production_available(productions=prod_total)
        prod_needed, _ = LedgerProduction.split_by_quantity(prod_available, offer.quantity)
        ex = [Exchange(quantity=p_qt, id=p_id, production_type=p_type, path_node=offer.return_path_node)
              for p_id, (_, p_qt, p_type, _, _) in prod_needed.iterrows()]

        return self.next.execute(deepcopy(state), deepcopy(ex))


class SaveExchangeHandler(Handler):
    """Save exchange to ledger"""
    def __init__(self, next: Handler, exchange_type: str, params: HandlerParameter = None):
        """
        Create Handler

        :param next: handler to execute after save exchanges
        :param params: handler global paramaters
        :param exchange_type: which kind of exchanges is saved [import/export/transfer]
        """
        Handler.__init__(self, params)
        self.next = next
        self.set_params(params)
        self.type = exchange_type

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
                e.path_node = SaveExchangeHandler.trim_path(state.name, deepcopy(e.path_node))
                state.exchanges.add(e, self.type)
        return self.next.execute(deepcopy(state), deepcopy(message))
    
    @staticmethod
    def trim_path(name: str, path: List[str]):
        """
        trim uphill nodes in path.

        :param state: current state
        :param path: whole path from exchange producer
        :return: trimed path with only next nodes
        """
        try:
            i = path.index(name) + 1
        except ValueError:
            i = 0
        return path[i:]


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
        :return: (new state, response message)
        """
        border = state.borders.find_border_in_path(message.return_path_node)
        free_border_capacity = border.quantity - state.exchanges.sum_border(border.name)
        if not free_border_capacity:
            return deepcopy(state), []

        message.quantity = min(free_border_capacity, message.quantity)
        return self.next.execute(deepcopy(state), deepcopy(message))


class CompareNewProduction(Handler):
    """Compare cost with a new production"""
    def __init__(self, for_prod_useless: Handler, for_prod_useful: Handler, params: HandlerParameter = None):
        """
        Create Handler
        :param for_prod_useless: handler to execute if some of new production is useless
        :param for_prod_useful: handler to execute if some of new production is useful
        :param params: global parameters
        """
        Handler.__init__(self, params)
        self.for_prod_useless = for_prod_useless
        self.for_prod_useful = for_prod_useful
        self.adequacy = AdequacyHandler(next=ReturnHandler())
        self.set_params(params)

    def set_params(self, params: HandlerParameter):
        self.params = params
        self.for_prod_useful.set_params(params)
        self.for_prod_useless.set_params(params)
        self.adequacy.set_params(params)

    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        """
        Compute state with new production, compare new cost.

        :param state: current state
        :param message: message received by dispatcher with quantity and cost attribute
        :return: state, message
        """
        test = deepcopy(state)
        test.productions.add_production(cost=message.cost, quantity=message.quantity, type='test')
        test, _ = self.adequacy.execute(test)
        if state.cost > test.cost:
            used_qt = test.productions.get_production_quantity(type='test', used=True)
            remain_qt = message.quantity - used_qt

            if remain_qt > 0:
                remain = deepcopy(message)
                remain.quantity = remain_qt
                self.for_prod_useless.execute(state=deepcopy(state), message=deepcopy(remain))

            message.quantity = used_qt

            return self.for_prod_useful.execute(deepcopy(state), deepcopy(message))
        else:
            return self.for_prod_useless.execute(deepcopy(state), deepcopy(message))


class MakerOfferHandler(Handler):
    """Respond to a proposal or forward proposal"""
    def __init__(self, next: Handler, params: HandlerParameter = None):
        """
        Create handler
        :param next: handler to execute when exchange from offer respond are received
        :param params: parameters to use
        """
        Handler.__init__(self, params)
        self.next = next
        self.set_params(params)

    def set_params(self, params: HandlerParameter):
        self.params = params
        self.next.set_params(params)

    def execute(self, state: State, proposal: Any = None) -> Tuple[State, Any]:
        """
        Respond to proposal. Save new productions
        :param state: current state
        :param proposal: proposal to respond
        :return:
        """
        offer = ProposalOffer(production_type=proposal.production_type, cost=proposal.cost,
                              quantity=proposal.quantity,
                              path_node=proposal.path_node,
                              return_path_node=proposal.path_node[-2::-1] + [state.name])

        exchanges = self.params.ask(to=proposal.path_node[0], mes=offer)
        exchanges = [self.change_path(ex, proposal.path_node) for ex in exchanges]
        state.productions.add_exchanges(cost=proposal.cost, ex=exchanges)

        return self.next.execute(deepcopy(state), deepcopy(exchanges))

    def change_path(self, ex: Exchange, path_node: List[str]) -> Exchange:
        ex.path_node = path_node
        return ex


class AdequacyHandler(Handler):
    """Compute power mix to used for reach local adequacy"""
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
        Compute adequacy.

        :param state: current state
        :param message: message receive by dispatcher (not used by handler)
        :return: new state with new production stack & rac & cost, message send by dispatcher (not given by this handler)
        """
        load = state.consumptions.sum_quantity()
        cost, prod = state.productions.apply_adequacy(quantity=load)

        cost += state.consumptions.compute_cost(quantity=prod)

        state.cost = cost
        state.rac = prod - load

        return self.next.execute(state, message)
