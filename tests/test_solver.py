import unittest

import time
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('pykka').setLevel(logging.INFO)

from pykka import ActorRef

from dispatcher.domain import *
from solver import solve


class TestSolver(unittest.TestCase):

    def test_two_nodes_on_side(self):

        nodes = {}
        nodes['a'] = NodeQuantity(min_exchange=1,
                                  consumptions=[Consumption(cost=10 ** 6, quantity=10, type='load')],
                                  productions=[Production(cost=10, quantity=20, type='nuclear')],
                                  borders=[Border(dest='b', capacity=10, cost=2)])

        nodes['b'] = NodeQuantity(min_exchange=1,
                                  consumptions=[Consumption(cost=10 ** 6, quantity=5, type='load')],
                                  productions=[Production(cost=20, quantity=15, type='nuclear')],
                                  borders=[Border(dest='c', capacity=1, cost=2)])

        nodes['c'] = NodeQuantity(min_exchange=1,
                                  consumptions=[Consumption(cost=10 ** 6, quantity=20, type='load')],
                                  productions=[Production(cost=10, quantity=10, type='nuclear')])

        nodes_expected = {}
        nodes_expected['a'] = NodeQuantity(min_exchange=1,
                                           consumptions=[Consumption(cost=10 ** 6, quantity=10, type='load')],
                                           productions=[Production(cost=10, quantity=20, type='nuclear')],
                                           borders=[])

        nodes_expected['b'] = NodeQuantity(min_exchange=1,
                                           consumptions=[Consumption(cost=10 ** 6, quantity=5, type='load')],
                                           productions=[Production(cost=20, quantity=5, type='nuclear')],
                                           borders=[])

        nodes_expected['c'] = NodeQuantity(min_exchange=1,
                                           consumptions=[Consumption(cost=10 ** 6, quantity=20, type='load')],
                                           productions=[Production(cost=10, quantity=10, type='nuclear')])

        res = solve(Study(nodes=nodes))

        self.assert_study(nodes_expected, res.nodes)

    def assert_study(self, expected, results):
        for name, node in expected.items():
            if name not in results.keys():
                self.fail('Node {} expected but not')
            res = results[name]

            # Consumptions
            for cons_expected, cons_res in zip(node.consumptions, res.consumptions):
                self.assertEqual(cons_expected.type, cons_res.type,
                                 "Consumption for node {} has different type".format(name))
                self.assertEqual(cons_expected.quantity, cons_res.quantity,
                                 'Consumption {} for node {} has different quantity'.format(cons_expected.type, name))
                self.assertEqual(cons_expected.cost, cons_res.cost,
                                 'Consumption {} for node {} has different cost'.format(cons_expected.type, name))

            # Productions
            for prod_expected, prod_res in zip(node.productions, res.productions):
                self.assertEqual(prod_expected.type, prod_res.type,
                                 "Production for node {} has different type".format(name))
                self.assertEqual(prod_expected.quantity, prod_res.quantity,
                                 'Production {} for node {} has different quantity'.format(prod_expected.type, name))
                self.assertEqual(prod_expected.cost, prod_res.cost,
                                 'Production {} for node {} has different cost'.format(prod_expected.type, name))

            # Borders
            for border_expected, border_res in zip(node.borders, res.borders):
                self.assertEqual(border_expected.dest, border_res.dest,
                                 "Border for node {} has different type".format(name))
                self.assertEqual(border_expected.quantity, border_res.quantity,
                                 'Border {} for node {} has different quantity'.format(border_expected.type, name))
                self.assertEqual(border_expected.cost, border_res.cost,
                                 'Border {} for node {} has different cost'.format(border_expected.type, name))


    def plot(self, actor: ActorRef):
        d = actor.ask(Snapshot())

        print('=============================================================================================')
        print("Node ", d.name, 'rac=', d.broker.state.rac, 'cost=', d.broker.state.cost)
        print('\nEvents')
        print('\ttype\tmes')
        for event in d.events:
            print('\t{type: <8}{mes}'.format(type=event.type, mes=event.message))

        print("\nProduction used")
        print('\ttype        id\t\t\t\t\t\t\t\t\tcost\tquantity\t\texchange_id\t\t\t\t\t\t\texchange_path')
        for p in d.broker.state.productions_used:
            print('\t{type: <12}{id: <36}{cost: <8}{quantity: <16}'.format(type=p.type, id=p.id.hex, cost=p.cost,
                                                                           quantity=p.quantity), end='')
            if p.exchange is None:
                print('None')
            else:
                print('{id: <36}{path}'.format(id=p.exchange.id.hex, path=p.exchange.path_node))

        print("\nProduction free")
        print('\ttype    id\t\t\t\t\t\t\t\t\tcost\tquantity')
        for p in d.broker.state.productions_free:
            print('\t{type: <8}{id: <36}{cost: <8}{quantity: <8}'.format(type=p.type, id=p.id.hex, cost=p.cost,
                                                                         quantity=p.quantity))

        print("\nLedger")
        print('\tproduction_id\t\t\t\t\t\texchange_id\t\t\t\t\t\t\tquantity\tpath')
        for production, exchanges in d.broker.ledger_exchanges.ledger.items():
            for id, ex in exchanges.items():
                print('\t{production: <36}{id: <36}{quantity: <12}{path}'.format(id=ex.id.hex,
                                                                                 production=ex.production_id.hex,
                                                                                 quantity=ex.quantity,
                                                                                 path=ex.path_node))
