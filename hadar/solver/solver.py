#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

from abc import ABC, abstractmethod

from hadar.solver.input import Study
from hadar.solver.output import Result
from hadar.solver.lp.solver import solve_lp
from hadar.solver.remote.solver import solve_remote


__all__ = ['LPSolver', 'RemoteSolver']


class Solver(ABC):
    """Solver interface to implement"""
    @abstractmethod
    def solve(self, study: Study) -> Result:
        pass


class LPSolver(Solver):
    """
    Basic Solver works with linear programming.
    """
    def solve(self, study: Study) -> Result:
        """
        Solve adequacy study.

        :param study: study to resolve
        :return: study's result
        """
        return solve_lp(study)


class RemoteSolver(Solver):
    """
    Use a remote solver to compute on cloud.
    """
    def __init__(self, url: str, token: str = ''):
        """
        Server solver parameter.

        :param url: server url
        :param token: server token if needed. default ''
        """
        self.url = url
        self.token = token

    def solve(self, study: Study) -> Result:
        """
        Solve adequacy study.

        :param study: study to resolve
        :return: study's result
        """
        return solve_remote(study, url=self.url, token=self.token)

