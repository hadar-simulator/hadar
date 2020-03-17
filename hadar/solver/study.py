from hadar.solver.input import Study
from hadar.solver.output import Result
from hadar.solver.lp.solver import solve_lp
from hadar.solver.remote.solver import solve_remote


def solve(study: Study, kind: str = 'lp', **kwargs) -> Result:
    """
    Solve adequacy study.

    :param study: study to resolve
    :param kind: type of solver to use. 'remote' or 'lp'
    :return: study's result
    """
    if kind == 'lp':
        return solve_lp(study)
    if kind == 'remote':
        return solve_remote(study, **kwargs)
    raise ValueError('kind {} not supported. Support only [actor]')
