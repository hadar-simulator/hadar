from abc import ABC, abstractmethod

from hadar.solver.input import Study
from hadar.solver.output import Result
from hadar.solver.lp.solver import solve_lp
from hadar.solver.remote.solver import solve_remote


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

