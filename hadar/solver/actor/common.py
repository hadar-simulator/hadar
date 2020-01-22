from hadar.solver.actor.domain.input import DTO
from hadar.solver.actor.ledger import *


class State(DTO):
    """
    Represent current adequacy configuration. Each Handler has to update and forward this state.
    """
    def __init__(self, name: str, consumptions: LedgerConsumption, borders: LedgerBorder,
                 productions: LedgerProduction, rac: int, cost: int):
        self.name = name
        self.consumptions = consumptions
        self.borders = borders
        self.productions = productions
        self.exchanges = LedgerExchange()
        self.rac = rac
        self.cost = cost
