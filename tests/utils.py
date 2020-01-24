from hadar.solver.input import *
from hadar.solver.output import Result


def assert_study(self, expected: Result, result: Result):
    for name, node in expected.nodes.items():
        if name not in result.nodes.keys():
            self.fail('Node {} expected but not'.format(name))
        res = result.nodes[name]

        np.testing.assert_array_equal(node.cost, res.cost, "Wrong cost")
        np.testing.assert_array_equal(node.rac, res.rac, "Wrong RAC")

        # Consumptions
        for cons_expected, cons_res in zip(node.consumptions, res.consumptions):
            self.assertEqual(cons_expected.type, cons_res.type,
                             "Consumption for node {} has different type".format(name))
            np.testing.assert_array_equal(cons_expected.quantity, cons_res.quantity,
                             'Consumption {} for node {} has different quantity'.format(cons_expected.type, name))
            self.assertEqual(cons_expected.cost, cons_res.cost,
                             'Consumption {} for node {} has different cost'.format(cons_expected.type, name))

        # Productions
        for prod_expected, prod_res in zip(node.productions, res.productions):
            self.assertEqual(prod_expected.type, prod_res.type,
                             "Production for node {} has different type".format(name))
            np.testing.assert_array_equal(prod_expected.quantity, prod_res.quantity,
                             'Production {} for node {} has different quantity'.format(prod_expected.type, name))
            self.assertEqual(prod_expected.cost, prod_res.cost,
                             'Production {} for node {} has different cost'.format(prod_expected.type, name))

        # Borders
        for border_expected, border_res in zip(node.borders, res.borders):
            self.assertEqual(border_expected.dest, border_res.dest,
                             "Border for node {} has different type".format(name))
            np.testing.assert_array_equal(border_expected.quantity, border_res.quantity,
                             'Border {} for node {} has different quantity'.format(border_expected.dest, name))
            self.assertEqual(border_expected.cost, border_res.cost,
                             'Border {} for node {} has different cost'.format(border_expected.dest, name))


def plot(d):

    print('=============================================================================================')
    print("Node ", d.state.name, 'rac=', d.state.rac, 'cost=', d.state.cost)
    print('\nEvents')
    print('\ttype\tmes')
    for event in d.events:
        print('\t{type: <8}{mes}'.format(type=event.type, mes=event.message))

    print(d.state.consumptions)
    print(d.state.productions)
    print(d.state.exchanges)
