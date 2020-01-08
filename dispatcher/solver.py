import time

from pykka import ActorRegistry

from dispatcher.actor import Dispatcher, Waiter
from dispatcher.domain import *


def create_dispatcher(name: str, node: NodeQuantity) -> Dispatcher:
    return Dispatcher.start(name=name,
                            min_exchange=1,
                            consumptions=node.consumptions,
                            productions=node.productions,
                            borders=node.borders)


def solve(study: Study) -> Study:
    waiter = Waiter(wait_ms=2)

    dispatcher = [create_dispatcher(name, node) for name, node in study.nodes.items()]
    for d in dispatcher:
        d.tell(Start())

    waiter.wait()

    nodes = {}
    for d in dispatcher:
        name, (cons, prod, borders) = d.ask(Next())
        nodes[name] = NodeQuantity(consumptions=cons, productions=prod, borders=borders)

    ActorRegistry.stop_all()
    return Study(nodes=nodes)
