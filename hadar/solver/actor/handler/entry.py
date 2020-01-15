from copy import deepcopy

from solver.actor.common import State
from solver.actor.handler.handler import *


class StartHandler(Handler):

    def __init__(self, params: HandlerParameter):
        Handler.__init__(self, params=params)
        self.handler = ProposeFreeProductionHandler(params=params, next=ReturnHandler())

    def execute(self, state: State, message=None) -> Tuple[State, Any]:
        return self.handler.execute(deepcopy(state))


class CanceledCustomerExchangeHandler(Handler):
    def __init__(self, params: HandlerParameter):
        Handler.__init__(self, params=params)
        self.handler = CancelExportationHandler(params=params,
                    on_forward=BackwardMessageHandler(type='tell',
                        next=ReturnHandler()),
                    on_producer=ProposeFreeProductionHandler(
                        next=ReturnHandler()
                    ))

    def execute(self, state: State, message=None) -> Tuple[State, Any]:
        return self.handler.execute(state, message)
