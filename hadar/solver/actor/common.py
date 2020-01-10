import uuid
from typing import List

import pandas as pd
from abc import ABC, abstractmethod

from solver.actor.actor import Exchange


class LedgerExchange:
    """
    Manage exchange ledger for a dispatcher.
    """
    def __init__(self):
        self.ledger = pd.DataFrame(columns=['prod_id', 'border', 'quantity', 'path_node'])
        self.ledger = self.ledger.astype({'prod_id': 'int64', 'border': 'object', 'quantity': 'int64', 'path_node': 'object'})

    def add_all(self, ex: List[Exchange]):
        """
        Add many exchanges to ledger

        :param ex: list of exchange to add
        """
        for e in ex:
            self.add(e)

    def add(self, ex: Exchange):
        """
        Add exchange to ledger

        :param ex: exchange object to add
        :return:
        """
        if ex.id in self.ledger.index:
            raise ValueError('Exchange already stored in ledger')
        border = ex.path_node[0]
        self.ledger.loc[ex.id] = [ex.production_id, border, ex.quantity, ex.path_node]

    def delete(self, ex: Exchange):
        """
        Delete exchange from ledger.

        :param ex: exchange object to delete
        :return:
        """
        self.ledger.drop(ex.id, inplace=True)

    def delete_all(self, exs: List[Exchange]):
        """
        Delete many exchanges from ledger.

        :param exs: exchanges list to delete
        :return:
        """
        ids = [ex.id for ex in exs]
        self.ledger.drop(ids, inplace=True)

    def sum_production(self, production_id):
        """
        Sum production quantity used.

        :param production_id: production id
        :return: quantity produce by this production
        """
        return self.ledger[self.ledger['prod_id'] == production_id]['quantity'].sum()

    def sum_border(self, name: str):
        """
        Sum all quantity send to a border.

        :param name: border's name
        :return: quantity send to this border
        """
        return self.ledger[self.ledger['border'] == name]['quantity'].sum()


class LedgerProduction:
    """Manage production used by dispatcher"""

    def __init__(self, uuid_generate=uuid.uuid4):
        self.uuid_generate = uuid_generate
        self.ledger = pd.DataFrame(columns=('cost', 'quantity', 'type', 'used', 'exchange'))
        self.ledger = self.ledger.astype({'cost': 'int64', 'quantity': 'int64', 'type': 'object', 'used': 'bool', 'exchange': 'object'})

    def add_production(self, cost: int, quantity: int, type: str = ''):
        self.ledger.loc[self.uuid_generate()] = [cost, quantity, type, False, None]

    def add_exchange(self, cost: int, ex: Exchange):
        self.ledger.loc[ex.production_id] = [cost, ex.quantity, 'import', False, ex]

    def delete(self, id: uuid):
        self.ledger.drop(id, inplace=True)

    def delete_all(self, ids):
        self.ledger.drop(ids, inplace=True)

    def filter_exchanges(self) -> pd.DataFrame:
        return self.ledger[self.ledger['exchange'].notnull()]

    def filter_productions(self) -> pd.DataFrame:
        return self.ledger[self.ledger['exchange'].isnull()]

    def find_production(self, id: uuid) -> pd.Series:
        return self.ledger.loc[id]


class State:



class Handler(ABC):
    pass