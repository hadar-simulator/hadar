import logging
import time

from pykka import ActorRegistry

from hadar.solver.actor.actor import Dispatcher, Result, Waiter
from hadar.solver.input import *
from hadar.solver.actor.domain.message import Start, Next


logger = logging.getLogger(__name__)


def _create_dispatcher(name: str, node: InputNode, waiter: Waiter) -> Dispatcher:
    return Dispatcher.start(name=name, waiter=waiter, input=node)


def solve(study: Study) -> Result:
    """
    Solve adequacy by behaviour simulation with actor pattern.

    :param study: study to resolve
    :return: result
    """
    waiter = Waiter(wait_ms=100)

    dispatchers = [_create_dispatcher(name, node, waiter) for name, node in study.nodes.items()]
    for d in dispatchers:
        d.tell(Start())

    logger.info('Agents stated')
    waiter.wait()

    nodes = {}
    for d in dispatchers:
        name, node = d.ask(Next())
        nodes[name] = node
    logger.info('Agents stopped')

    #for d in dispatchers:
    #    plot(d.ask(Snapshot()))

    ActorRegistry.stop_all()
    return Result(nodes=nodes)