import unittest
import pandas as pd
import numpy as np

from hadar.solver.input import *
from hadar.solver.output import *
from hadar.solver.study import solve
from hadar.aggregator.result import *
from viewer.jupyter import plot_flow


class TestJupyter(unittest.TestCase):
    def setUp(self) -> None:
        self.study = Study(['a', 'b', 'c']) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[20, 2], type='load')) \
            .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[30, 3], type='car')) \
            .add_on_node('a', data=Production(cost=10, quantity=[30, 3], type='prod')) \
            .add_on_node('b', data=Consumption(cost=10 ** 6, quantity=[20, 2], type='load')) \
            .add_on_node('b', data=Production(cost=20, quantity=[10, 1], type='prod')) \
            .add_on_node('b', data=Production(cost=20, quantity=[20, 2], type='nuclear')) \
            .add_border(src='a', dest='b', quantity=[10, 1], cost=2) \
            .add_border(src='a', dest='c', quantity=[20, 2], cost=2)

        self.result = solve(study=self.study)

        self.agg = ResultAggregator(self.study, self.result)

    def test_flow(self):
        plot_flow(self.agg, 'a', 0)