from copy import deepcopy

from solver.actor.common import State
from solver.actor.handler.handler import *


class StartHandler(Handler):

    def __init__(self, params: HandlerParameter):
        Handler.__init__(self, params=params)
        self.handler = ProposeFreeProductionHandler(params=params, next=ReturnHandler())

    def execute(self, state: State, message=None) -> Tuple[State, Any]:
        return self.handler.execute(deepcopy(state), deepcopy(message))


class CanceledCustomerExchangeHandler(Handler):
    def __init__(self, params: HandlerParameter):
        Handler.__init__(self, params=params)
        self.handler = CancelExportationHandler(params=params,
                    next=BackwardMessageHandler(type='tell',
                            after_backward=ReturnHandler(),
                            on_resume=ProposeFreeProductionHandler(next=ReturnHandler()),
                    ))

    def execute(self, state: State, message=None) -> Tuple[State, Any]:
        return self.handler.execute(deepcopy(state), deepcopy(message))


class ProposalOfferHandler(Handler):
    def __init__(self, params: HandlerParameter):
        Handler.__init__(self, params=params)
        self.handler = CheckOfferBorderCapacityHandler(params=params,
                    next=BackwardMessageHandler(type='ask',
                        after_backward=SaveExchangeHandler(exchange_type='transfer', next=ReturnHandler()),
                        on_resume=AcceptExchangeHandler(
                            next=SaveExchangeHandler(exchange_type='export', next=ReturnHandler()))
                    ))

    def execute(self, state: State, message: Any = None) -> Tuple[State, Any]:
        return self.handler.execute(deepcopy(state), deepcopy(message))


class ProposalHandler(Handler):
    def __init__(self, params: HandlerParameter):
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
