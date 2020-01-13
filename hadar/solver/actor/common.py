import uuid
from typing import List

import pandas as pd
from abc import ABC, abstractmethod

from hadar.solver.actor.domain.input import DTO
from hadar.solver.actor.ledger import *


class State(DTO):
    """
    Represent current adequacy configuration. Each Handler has to update and forward this state.
    """
    def __init__(self, consumptions: LedgerConsumption, borders: LedgerBorder,
                 productions: LedgerProduction, rac: int, cost: int):
        self.consumptions = consumptions
        self.borders = borders
        self.productions = productions
        self.exchanges = LedgerExchange()
        self.rac = rac
        self.cost = cost


class Handler(ABC):
    """
    Represent an atomic behaviour. Handler update state object and call other handlers.
    Message receiving behaviour is implemented by chaining handler according to Chain of Responsabilities pattern
    """

    def __init__(self, ask, to, uuid_generate=uuid.uuid4):
        self.ask = ask
        self.to = to
        self.uuid_generate = uuid_generate

    @abstractmethod
    def execute(self, state: State) -> State:
        pass