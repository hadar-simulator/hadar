from hadar.solver.input import Study
from hadar.solver.actor.solver import solve as solve_actor
from hadar.solver.output import Result
from hadar.solver.lp.solver import solve_lp


def solve(study: Study, kind: str = 'lp') -> Result:
    """
    Solve adequacy study.

    :param study: study to resolve
    :param kind: type of solver to use. 'actor' or 'lp'
    :return: study's result
    """
    if kind == 'actor':
        return solve_actor(study)
    if kind == 'lp':
        return solve_lp(study)
    raise ValueError('kind {} not supported. Support only [actor]')
