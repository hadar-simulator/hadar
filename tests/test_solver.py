import unittest

import time

from pykka import ActorRef

from domain import Consumption, Production, Border, Start, Snapshot
from node import DispatcherRegistry, Dispatcher


class TestSolver(unittest.TestCase):

    def test_two_nodes_on_side(self):
        a = Dispatcher.start(name='a',
                             min_exchange=100,
                             consumptions=[Consumption(cost=10**6, quantity=1000)],
                             productions=[Production(cost=10, quantity=2000, type='nuclear')],
                             borders=[Border(dest='b', capacity=1000, cost=2)])

        b = Dispatcher.start(name='b',
                             min_exchange=100,
                             consumptions=[Consumption(cost=10**6, quantity=500)],
                             productions=[Production(cost=10, quantity=250, type='nuclear')],
                             borders=[Border(dest='c', capacity=1000, cost=2)])

        c = Dispatcher.start(name='c',
                             min_exchange=100,
                             consumptions=[Consumption(cost=10**6, quantity=750)],
                             productions=[Production(cost=10, quantity=500, type='nuclear')])

        a.tell(Start())
        b.tell(Start())
        c.tell(Start())

        time.sleep(1)

        self.plot(a)
        self.plot(b)
        self.plot(c)

        a.stop()
        b.stop()
        c.stop()

    def plot(self, actor: ActorRef):
        d = actor.ask(Snapshot())
        print("\n\nNode ", d.name, 'rac=', d.state.rac, 'cost=', d.state.cost)
        print("Production used")
        print('\ttype        id\t\t\t\t\t\t\t\t\tcost\tquantity\t\texchange_id\t\t\t\t\t\t\texchange_path')
        for p in d.state.productions_used:
            print('\t{type: <12}{id: <36}{cost: <8}{quantity: <16}'.format(type=p.type, id=p.id.hex, cost=p.cost, quantity=p.quantity), end='')
            if p.exchange is None:
                print('None')
            else:
                print('{id: <36}{path}'.format(id=p.exchange.id.hex, path=p.exchange.path_node))

        print("Production free")
        print('\ttype    id\t\t\t\t\t\t\t\t\tcost\tquantity')
        for p in d.state.productions_free:
            print('\t{type: <8}{id: <36}{cost: <8}{quantity: <8}'.format(type=p.type, id=p.id.hex, cost=p.cost, quantity=p.quantity))

        print("Ledger")
        print('\tproduction_id\t\t\t\t\t\texchange_id\t\t\t\t\t\t\tquantity\tpath')
        for production, exchanges in d.ledger_exchanges.ledger.items():
            for id, ex in exchanges.items():
                print('\t{production: <36}{id: <36}{quantity: <12}{path}'.format(id=ex.id.hex, production=ex.production_id.hex, quantity=ex.quantity, path=ex.path_node))
