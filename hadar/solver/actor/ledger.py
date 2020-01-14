import uuid
from typing import List

import pandas as pd

from hadar.solver.actor.domain.message import Exchange


class Ledger:
    """Meta Ledger to implement eq, hash, str, repr method"""
    def __init__(self, headers: List[List[str]]):
        self.ledger = pd.DataFrame(columns=[name for name, dtype in headers])
        self.ledger = self.ledger.astype({name: dtype for name, dtype in headers})

    def __hash__(self):
        return hash(self.ledger)

    def __eq__(self, other):
        print('Original', self.ledger)
        print('Other', other.ledger)
        return isinstance(other, type(self)) and self.ledger.equals(other.ledger)

    def __str__(self):
        return str(self.ledger)

    def __repr__(self):
        return self.__str__()


class LedgerExchange(Ledger):
    """
    Manage exchange ledger for a dispatcher.
    """
    def __init__(self):
        Ledger.__init__(self, [['prod_id', 'int64'], ['border', 'object'], ['quantity', 'int64'], ['path_node', 'object']])

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


class LedgerProduction(Ledger):
    """Manage production used by dispatcher"""

    def __init__(self, uuid_generate=uuid.uuid4):
        self.uuid_generate = uuid_generate
        Ledger.__init__(self, [['cost', 'int64'], ['quantity', 'int64'], ['type', 'object'],
                               ['used', 'bool'], ['exchange', 'object']])

    def __eq__(self, other):
        if not hasattr(other, 'ledger'):
            return False
        return self.ledger.equals(other.ledger)

    def add_production(self, cost: int, quantity: int, type: str = '', used: bool = False):
        """
        Add production from internal.

        :param cost: production cost
        :param quantity: production quantity
        :param type: production type
        :param used: set used or not
        :return:
        """
        self.ledger.loc[self.uuid_generate()] = [cost, quantity, type, used, None]

    def add_exchange(self, cost: int, ex: Exchange, used: bool = False):
        """
        Add production from external.

        :param cost: cost of external production
        :param used: set used or not
        :param ex: exchange object where production comes
        :return:
        """
        self.ledger.loc[ex.id] = [cost, ex.quantity, 'import', used, ex]

    def delete(self, id: uuid):
        """
        Delete production by its id.

        :param id: production id
        :return:
        """
        self.ledger.drop(id, inplace=True)

    def delete_all(self, ids):
        """
        Delete many production by their ids.

        :param ids: productions id
        :return:
        """
        self.ledger.drop(ids, inplace=True)

    def filter_exchanges(self) -> pd.DataFrame:
        """
        Get only external production.

        :return: dataframe with external production
        """
        return self.ledger[self.ledger['exchange'].notnull()]

    def filter_useless_exchanges(self) -> pd.DataFrame:
        return self.ledger[self.ledger['exchange'].notnull() & ~self.ledger['used']]

    def filter_productions(self) -> pd.DataFrame:
        """
        Get only internal production.

        :return: dataframe with internal production
        """
        return self.ledger[self.ledger['exchange'].isnull()]

    def find_production(self, id: uuid) -> pd.Series:
        """
        Get production by id
        :param id: production id
        :return: Series with asked production
        """
        return self.ledger.loc[id]

    def find_production_by_type(self, type: str) -> pd.Series:
        """
        Get production by type
        :param type: production type
        :return: Series with asked production
        """
        return self.ledger[self.ledger['type'] == type].iloc[0]


class LedgerConsumption(Ledger):
    """Manage consumption used by dispatcher"""

    def __init__(self):
        Ledger.__init__(self, [['cost', 'int64'], ['quantity', 'int64']])

    def add(self, type: str, cost: int, quantity: int):
        self.ledger.loc[type] = [cost, quantity]

    def delete(self, type: str):
        self.ledger.drop(type, inplace=True)

    def find_consumption(self, type: str) -> pd.Series:
        return self.ledger.loc[type]


class LedgerBorder(Ledger):
    """Manage borders used by dispatcher"""

    def __init__(self):
        Ledger.__init__(self, [['cost', 'int64'], ['quantity', 'int64']])

    def __eq__(self, other):
        if not hasattr(other, 'ledger'):
            return False
        return self.ledger.equals(other.ledger)

    def add(self, dest: str, cost: int, quantity: int):
        self.ledger.loc[dest] = [cost, quantity]

    def delete(self, dest: str):
        self.ledger.drop(dest, inplace=True)

    def find_border(self, dest: str):
        return self.ledger.loc[dest]
