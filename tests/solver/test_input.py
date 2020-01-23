import unittest
from hadar.solver.input import *

class TestNetwork(unittest.TestCase):
    def test_create_study(self):
        study = Study(['a', 'b']) \
            .add(node='a', data=Consumption(type='load', cost=20, quantity=[10])) \
            .add(node='a', data=Production(type='nuclear', cost=20, quantity=[10])) \
            .add(node='b', data=Border(dest='a', cost=20, quantity=[10]))

        print(study)

    def test_wrong_node_list(self):
        def test():
            study = Study(node_names=['fr', 'be', 'de', 'be'])
        self.assertRaises(ValueError, test)

    def test_wrong_production_cost(self):
        def test():
            study = Study(node_names=['fr']) \
                .add(node='fr', data=Production(type='solar', cost=-1, quantity=[10]))

        self.assertRaises(ValueError, test)

    def test_wrong_production_quantity(self):
        def test():
            study = Study(node_names=['fr']) \
                .add(node='fr', data=Production(type='solar', cost=10, quantity=[-1]))

        self.assertRaises(ValueError, test)

    def test_wrong_production_type(self):
        def test():
            study = Study(node_names=['fr']) \
                .add(node='fr', data=Production(type='solar', cost=10, quantity=[10])) \
                .add(node='fr', data=Production(type='solar', cost=10, quantity=[10]))

        self.assertRaises(ValueError, test)

    def test_wrong_consumption_cost(self):
        def test():
            study = Study(node_names=['fr']) \
                .add(node='fr', data=Consumption(type='load', cost=-10, quantity=[10]))

        self.assertRaises(ValueError, test)

    def test_wrong_consumption_quantity(self):
        def test():
            study = Study(node_names=['fr']) \
                .add(node='fr', data=Consumption(type='load', cost=10, quantity=[-10]))

        self.assertRaises(ValueError, test)

    def test_wrong_consumption_type(self):
        def test():
            study = Study(node_names=['fr']) \
                .add(node='fr', data=Consumption(type='load', cost=10, quantity=[10])) \
                .add(node='fr', data=Consumption(type='load', cost=10, quantity=[10]))

        self.assertRaises(ValueError, test)

    def test_wrong_border_cost(self):
        def test():
            study = Study(node_names=['fr', 'be']) \
                .add(node='fr', data=Border(dest='be', cost=-10, quantity=[10]))

        self.assertRaises(ValueError, test)

    def test_wrong_border_quantity(self):
        def test():
            study = Study(node_names=['fr', 'be']) \
                .add(node='fr', data=Border(dest='be', cost=10, quantity=[-10]))

        self.assertRaises(ValueError, test)

    def test_wrong_border_dest_not_node(self):
        def test():
            study = Study(node_names=['fr', 'be']) \
                .add(node='fr', data=Border(dest='it', cost=10, quantity=[10]))

        self.assertRaises(ValueError, test)

    def test_wrong_border_dest_not_unique(self):
        def test():
            study = Study(node_names=['fr', 'be']) \
                .add(node='fr', data=Border(dest='be', cost=10, quantity=[10])) \
                .add(node='fr', data=Border(dest='be', cost=10, quantity=[10]))
        self.assertRaises(ValueError, test)