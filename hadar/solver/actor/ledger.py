import uuid
from copy import deepcopy
from typing import List, Tuple

import pandas as pd
import numpy as np
from hadar.solver.actor.domain.message import Exchange


class Ledger:
    """Meta Ledger to implement eq, hash, str, repr method"""
    def __init__(self, headers: List[List[str]]):
        self.ledger = pd.DataFrame(columns=[name for name, dtype in headers])  #NOSONAR
        self.ledger = self.ledger.astype({name: dtype for name, dtype in headers})

    def __hash__(self):
        return hash(self.ledger)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.ledger.equals(other.ledger)

    def __str__(self):
        return str(self.ledger)

    def __repr__(self):
        return self.__str__()


class LedgerExchange(Ledger):
    """
    Manage exchange ledger for a dispatcher.
    """
    TYPES = ['import', 'export', 'transfer']

    def __init__(self):
        Ledger.__init__(self, [['prod_type', 'object'], ['border', 'object'],
                               ['quantity', 'int64'], ['path_node', 'object'], ['type', 'object']])

    def add_all(self, ex: List[Exchange], type: str):
        """
        Add many exchanges to ledger

        :param ex: list of exchange to add
        :param type: exchange type [import/export/transfer]
        """
        for e in ex:
            self.add(e, type)

    def add(self, ex: Exchange, type: str):
        """
        Add exchange to ledger

        :param ex: exchange object to add
        :param type: exchange type [import/export/transfer]
        :return:
        """
        if type not in LedgerExchange.TYPES:
            raise ValueError("exchange type should be [import/export/transfer], you give {}".format(type))
        if ex.id in self.ledger.index:
            raise ValueError('Exchange already stored in ledger')
        border = ex.path_node[0]
        self.ledger.loc[ex.id] = [ex.production_type,  border, ex.quantity, ex.path_node, type]

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

    def get_exchanges(self, ids: List[int]) -> List[Exchange]:
        """
        Get exchanges by id
        :param ids: exchange ids
        :return: slice of ledger with asked exchanges
        """
        return [Exchange(id=id, quantity=qt, production_type=prod_type, path_node=path)
                for id, (prod_type, border, qt, path, _) in self.ledger.loc[ids].iterrows()]

    def sum_production(self, production_type):
        """
        Sum production quantity used.

        :param production_type: production type
        :return: quantity produce by this production
        """
        return self.ledger[(self.ledger['prod_type'] == production_type) & (self.ledger['type'] == 'export')]['quantity'].sum()

    def sum_border(self, name: str):
        """
        Sum all quantity send to a border.

        :param name: border's name
        :return: quantity send to this border
        """
        return self.ledger[self.ledger['border'] == name]['quantity'].sum()

    def filter_production_available(self, productions: pd.DataFrame) -> pd.DataFrame:
        """
        Filter production DataFrame with currently production in exchange

        :param productions: production DataFrame like production ledger
        :return: production DataFrame without production present in ledger exchange
        """
        prod_not_available = productions.index.intersection(self.ledger.index)
        return productions.drop(prod_not_available)

class LedgerProduction(Ledger):
    """Manage production used by dispatcher"""

    def __init__(self, uuid_generate=uuid.uuid4):
        self.uuid_generate = uuid_generate
        Ledger.__init__(self, [['cost', 'int64'], ['quantity', 'int64'], ['type', 'object'],
                               ['used', 'bool'], ['path_node', 'object']])

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
        append = pd.DataFrame(data={
            'cost': np.ones(quantity, dtype=int) * cost,
            'quantity': np.ones(quantity, dtype=int),
            'type': [type] * quantity,
            'used': [used] * quantity,
            'path_node': [None] * quantity},
            index=[self.uuid_generate() for _ in range(quantity)])

        self.ledger = pd.concat([self.ledger, append])


    def add_exchanges(self, cost: int, ex: List[Exchange], used: bool = False):
        """
        Add production from external.

        :param cost: cost of external production
        :param used: set used or not
        :param ex: exchange object where production comes
        :return:
        """
        quantity = len(ex)
        append = pd.DataFrame(data={
            'cost': np.ones(quantity, dtype=int) * cost,
            'quantity': [e.quantity for e in ex],
            'type': ['import'] * quantity,
            'used': [used] * quantity,
            'path_node': [e.path_node for e in ex]},
            index=[e.id for e in ex])

        self.ledger = pd.concat([self.ledger, append])

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
        return self.ledger[self.ledger['path_node'].notnull()]

    def filter_useless_exchanges(self) -> pd.DataFrame:
        """
        Get production from exchange tagged as not used.

        :return: DataFrame with only exchange not used
        """
        return self.ledger[self.ledger['path_node'].notnull() & ~self.ledger['used']]

    def group_free_productions(self) -> pd.DataFrame:
        """
        Regroup free productions by type.
        :return: dataframe with each production type sum up on one row (quantities are sum up)
        """
        df = self.ledger[self.ledger['path_node'].isnull() & ~self.ledger['used']]
        return pd.pivot_table(df, values=['cost', 'quantity'], index=['type'], aggfunc={'cost': np.mean, 'quantity': np.sum})

    def get_free_productions_by_type(self, type: str) -> pd.DataFrame:
        """
        Get a slice of ledger with internal productions with same type.

        :param type: type of production asked
        :return: slice of global ledger
        """
        slice = self.ledger[(self.ledger['path_node'].isnull()) & (~self.ledger['used']) & (self.ledger['type'] == type)]
        return deepcopy(slice)

    def get_production_quantity(self, type: str, used: bool) -> int:
        """
        Get total quantity production if used or not.

        :param type: type of production
        :param used: get used or free quantity
        :return:
        """
        return self.ledger[(self.ledger['type'] == type) & (self.ledger['used'] == used)]['quantity'].sum()


    def apply_adequacy(self, quantity: int):
        """
        Split current production state between used and free production according quantity consumption needed.

        :param quantity: consumption quantity
        :return: new cost, power used
        """
        used, free = LedgerProduction.split_by_quantity(self.ledger, quantity)
        used['used'] = True
        free['used'] = False
        self.ledger = pd.concat([used, free])

        cost = (used['cost'] * used['quantity']).sum()
        power = used['quantity'].sum()
        return cost, power


    @classmethod
    def split_by_quantity(cls, prod: pd.DataFrame, quantity: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split DataFrame between production used and productions free according quantity production asked.

        :return: DataFrame productions used, DataFrame productions free
        """
        prod = prod.sort_values(by=['cost', 'quantity'], ascending=[True, False])
        index_split = prod['quantity'].cumsum() <= quantity
        return prod[index_split], prod[~index_split]



class LedgerConsumption(Ledger):
    """Manage consumption used by dispatcher"""

    def __init__(self):
        Ledger.__init__(self, [['cost', 'int64'], ['quantity', 'int64']])

    def add(self, type: str, cost: int, quantity: int):
        self.ledger.loc[type] = [cost, quantity]
        self.ledger.sort_values(by='cost', ascending=False, inplace=True)


    def delete(self, type: str):
        self.ledger.drop(type, inplace=True)

    def find_consumption(self, type: str) -> pd.Series:
        return self.ledger.loc[type]

    def sum_quantity(self):
        return self.ledger['quantity'].sum()

    def compute_cost(self, quantity: int) -> int:
        if self.ledger.size == 0:
            return 0
        cum = self.ledger['quantity'].cumsum()
        rac = cum - quantity
        rac[rac < 0] = 0
        unit = rac.diff()
        unit.iloc[0] = rac.iloc[0]

        return (self.ledger['cost']*unit).sum()


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

    def find_border_in_path(self, path: List[str]):
        return self.ledger[self.ledger.index.isin(path)].iloc[0]
