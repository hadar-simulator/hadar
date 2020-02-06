import time

from pykka import ActorRegistry

from hadar.solver.actor.actor import Dispatcher, Result, Waiter
from hadar.solver.input import *
from hadar.solver.actor.domain.message import Start, Next


def create_dispatcher(name: str, node: InputNode, waiter: Waiter) -> Dispatcher:
    return Dispatcher.start(name=name, waiter=waiter, input=node)


def solve(study: Study) -> Result:
    waiter = Waiter(wait_ms=100)

    dispatchers = [create_dispatcher(name, node, waiter) for name, node in study.nodes.items()]
    for d in dispatchers:
        d.tell(Start())

    waiter.wait()

    nodes = {}
    for d in dispatchers:
        name, node = d.ask(Next())
        nodes[name] = node

    #for d in dispatchers:
    #    plot(d.ask(Snapshot()))

    ActorRegistry.stop_all()
    return Result(nodes=nodes)