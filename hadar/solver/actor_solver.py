from pykka import ActorRegistry

from hadar.solver.actor.actor import Dispatcher, Waiter
from hadar.solver.actor.domain.input import Study, InputNode
from hadar.solver.actor.domain.message import Start, Next, Snapshot
from tests.utils import plot


def create_dispatcher(name: str, node: InputNode) -> Dispatcher:
    return Dispatcher.start(name=name,
                            consumptions=node.consumptions,
                            productions=node.productions,
                            borders=node.borders)


def solve(study: Study) -> Study:
    waiter = Waiter(wait_ms=300)

    dispatchers = [create_dispatcher(name, node) for name, node in study.nodes.items()]
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
    return Study(nodes=nodes)
