import unittest
from hadar.solver.input import *

class TestNetwork(unittest.TestCase):
    def test_create_study(self):
        c = Consumption(type='load', cost=20, quantity=[10])
        p = Production(type='nuclear', cost=20, quantity=[10])
        b = Border(dest='a', cost=20, quantity=[10])

        study = Study(['a', 'b']) \
            .add_on_node(node='a', data=c) \
            .add_on_node(node='a', data=p) \
            .add_border(src='b', dest='a', cost=20, quantity=[10])

        self.assertEqual(c, study.nodes['a'].consumptions[0])
        self.assertEqual(p, study.nodes['a'].productions[0])
        self.assertEqual(b, study.nodes['b'].borders[0])
        self.assertEqual(1, study.horizon)

    def test_wrong_node_list(self):
        def test():
            study = Study(node_names=['fr', 'be', 'de', 'be'])
        self.assertRaises(ValueError, test)

    def test_wrong_production_cost(self):
        def test():
            study = Study(node_names=['fr']) \
                .add_on_node(node='fr', data=Production(type='solar', cost=-1, quantity=[10]))

        self.assertRaises(ValueError, test)

    def test_wrong_production_quantity(self):
        def test():
            study = Study(node_names=['fr']) \
                .add_on_node(node='fr', data=Production(type='solar', cost=10, quantity=[-1]))

        self.assertRaises(ValueError, test)

    def test_wrong_production_type(self):
        def test():
            study = Study(node_names=['fr']) \
                .add_on_node(node='fr', data=Production(type='solar', cost=10, quantity=[10])) \
                .add_on_node(node='fr', data=Production(type='solar', cost=10, quantity=[10]))

        self.assertRaises(ValueError, test)

    def test_wrong_consumption_cost(self):
        def test():
            study = Study(node_names=['fr']) \
                .add_on_node(node='fr', data=Consumption(type='load', cost=-10, quantity=[10]))

        self.assertRaises(ValueError, test)

    def test_wrong_consumption_quantity(self):
        def test():
            study = Study(node_names=['fr']) \
                .add_on_node(node='fr', data=Consumption(type='load', cost=10, quantity=[-10]))

        self.assertRaises(ValueError, test)

    def test_wrong_consumption_type(self):
        def test():
            study = Study(node_names=['fr']) \
                .add_on_node(node='fr', data=Consumption(type='load', cost=10, quantity=[10])) \
                .add_on_node(node='fr', data=Consumption(type='load', cost=10, quantity=[10]))

        self.assertRaises(ValueError, test)

    def test_wrong_border_cost(self):
        def test():
            study = Study(node_names=['fr', 'be']) \
                .add_border(src='fr', dest='be', cost=-10, quantity=[10])

        self.assertRaises(ValueError, test)

    def test_wrong_border_quantity(self):
        def test():
            study = Study(node_names=['fr', 'be']) \
                .add_border(src='fr', dest='be', cost=10, quantity=[-10])

        self.assertRaises(ValueError, test)

    def test_wrong_border_dest_not_node(self):
        def test():
            study = Study(node_names=['fr', 'be']) \
                .add_border(src='fr', dest='it', cost=10, quantity=[10])

        self.assertRaises(ValueError, test)

    def test_wrong_border_dest_not_unique(self):
        def test():
            study = Study(node_names=['fr', 'be']) \
                .add_border(src='fr', dest='be', cost=10, quantity=[10]) \
                .add_border(src='fr', dest='be', cost=10, quantity=[10])
        self.assertRaises(ValueError, test)
