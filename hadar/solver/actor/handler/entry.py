from copy import deepcopy

from solver.actor.common import State
from solver.actor.handler.handler import ProposeFreeProductionHandler, ReturnHandler, \
    HandlerParameter, Handler


class StartHandler(Handler):

    def __init__(self, params: HandlerParameter):
        Handler.__init__(self, params=params)
        self.handler = ProposeFreeProductionHandler(next=ReturnHandler())

    def execute(self, state: State, message=None) -> State:
        return self.handler.execute(deepcopy(state))


class CanceledCustomerExchangeHandler(Handler):
    def __init__(self, params: HandlerParameter):
        Handler.__init__(self, params=params)
        self.handler =

    def execute(self, state: State, message=None) -> State:
        pass

