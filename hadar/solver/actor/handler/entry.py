from copy import deepcopy
from typing import Any, Tuple

from hadar.solver.actor.handler.handler import State
from hadar.solver.actor.handler.handler import *


class StartHandler(Handler):
    """
    When Start message receive:
    --> propose free production
    """

    def __init__(self, params: HandlerParameter):
        """
        Initiate handler.

        :param params: handler parameters to use
        """
        Handler.__init__(self, params=params)
        self.handler = ProposeFreeProductionHandler(params=params, next=ReturnHandler())

    def execute(self, state: State, message=None) -> Tuple[State, Any]:
        """
        Execute handler.

        :param state: current actor state
        :param message: Start message
        :return: next actor state
        """
        return self.handler.execute(deepcopy(state), deepcopy(message))


class CanceledCustomerExchangeHandler(Handler):
    """
    When CancelCustomerExchangeHandler
    --> cancel exportation
    -----> if it's node producer : propose free production
    """
    def __init__(self, params: HandlerParameter):
        """
        Initiate handler.

        :param params: handler parameters to use
        """
        Handler.__init__(self, params=params)
        self.handler = CancelExportationHandler(params=params,
                    next=BackwardMessageHandler(type='tell',
                            after_backward=ReturnHandler(),
                            on_resume=ProposeFreeProductionHandler(next=ReturnHandler()),
                    ))

    def execute(self, state: State, message=None) -> Tuple[State, Any]:
        """
        Execute handler.

        :param state: current actor state
        :param message: CancelCustomerExchange message
        :return: next actor state
        """
        return self.handler.execute(deepcopy(state), deepcopy(message))


class ProposalOfferHandler(Handler):
    """
    When receive proposal offer:
    --> check border capacity
    ----> if node is transfer, wait response
    ------> save final exchanges
    ----> if node is producer, check production capacity
    ------> save final exchanges
    """
    def __init__(self, params: HandlerParameter):
        """
        Initiate handler.

        :param params: handler parameters to use
        """
        Handler.__init__(self, params=params)
        self.handler = CheckOfferBorderCapacityHandler(params=params,
                    next=BackwardMessageHandler(type='ask',
                        after_backward=SaveExchangeHandler(exchange_type='transfer', next=ReturnHandler()),
                        on_resume=AcceptExchangeHandler(
                            next=SaveExchangeHandler(exchange_type='export', next=ReturnHandler()))
                    ))

    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        """
        Execute handler.

        :param state: current actor state
        :param message: ProposalOffer message
        :return: next actor state, list of exchanges
        """
        return self.handler.execute(deepcopy(state), deepcopy(message))


class ProposalHandler(Handler):
    """
    When receive proposal:
    -> compare proposal with current state
    ---> if useless
    -----> forward proposal
    ---> if useful
    -----> make an offer, wait response
    -------> save exchanges accepted by producer
    ---------> compute new adequacy
    -----------> propose free production
    -------------> cancel useless importation
    """
    def __init__(self, params: HandlerParameter):
        """
        Initiate handler.

        :param params: handler parameters to use
        """
        Handler.__init__(self, params=params)
        self.handler = CompareNewProduction(params=params,
                            for_prod_useless=ForwardMessageHandler(next=ReturnHandler()),
                            for_prod_useful=MakerOfferHandler(
                                next=SaveExchangeHandler(exchange_type='import',
                                    next=AdequacyHandler(
                                        next=ProposeFreeProductionHandler(
                                            next=CancelUselessImportationHandler(next=ReturnHandler())
                                        )
                                    )
                                )
                            ))

    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        """
        Execute handler.

        :param state: current actor state
        :param message: ProposalOffer message
        :return: next actor state
        """
        return self.handler.execute(deepcopy(state), deepcopy(message))
