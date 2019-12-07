import time

from domain import Consumption, Production, Border, Start
from node import Broker, DispatcherRegistry


def main():

    resolver = DispatcherRegistry()

    a = Broker.start(name='a', resolver=resolver,
                     consumptions=[Consumption(cost=10**6, quantity=1000)],
                     productions=[Production(cost=10, quantity=1500, type='nuclear')],
                     borders=[Border(dest='b', capacity=1000, cost=2)])

    b = Broker.start(name='b', resolver=resolver,
                     consumptions=[Consumption(cost=10**6, quantity=1000)],
                     productions=[Production(cost=10, quantity=500, type='nuclear')])

    a.tell(Start())
    b.tell(Start())

if __name__ == '__main__':
    main()






