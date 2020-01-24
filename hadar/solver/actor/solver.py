import time

from pykka import ActorRegistry

from hadar.solver.actor.actor import Dispatcher, Waiter, Result
from hadar.solver.input import *
from hadar.solver.actor.domain.message import Start, Next


def create_dispatcher(name: str, node: InputNode) -> Dispatcher:
    return Dispatcher.start(name=name,
                            consumptions=node.consumptions,
                            productions=node.productions,
                            borders=node.borders)


def solve(study: Study) -> Result:
    waiter = Waiter(wait_ms=300)

    dispatchers = [create_dispatcher(name, node) for name, node in study.nodes.items()]
    for d in dispatchers:
        d.tell(Start())

    time.sleep(2)  # TODO use waiter

    nodes = {}
    for d in dispatchers:
        name, node = d.ask(Next())
        nodes[name] = node

    #for d in dispatchers:
    #    plot(d.ask(Snapshot()))

    ActorRegistry.stop_all()
    return Result(nodes=nodes)