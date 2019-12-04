import uuid
from typing import List
from copy import copy

from pykka import ThreadingActor

from domain import *
from manager import DispatcherRegistry


class Dispatcher(ThreadingActor):

    def __init__(self, name,
                 uuid_generate=lambda: uuid.uuid1(),
                 registry: DispatcherRegistry = DispatcherRegistry(),
                 consumptions: List[Consumption] = [],
                 productions: List[Production] = [],
                 borders: List[Border] = []):
        super().__init__()

        self.name = name
        self.uuid_generate = uuid_generate
        self.consumptions = sorted(consumptions, key=lambda x: x.cost, reverse=True)
        self.raw_productions = productions
        self.borders = borders
        self.registry = registry
        self.registry.add(self)

        self.state = self.optimize_adequacy(self.raw_productions)
        print(self.name, 'cost=', self.state.cost)

    def on_receive(self, message):
        """
        Mail box of actor.

        :param message: next message to process
        :return:
        """
        print('received at', self.name, ':', message)
        if isinstance(message, Start):
            self.send_proposal(productions=self.state.productions_free)
            return
        if isinstance(message, ProposalOffer):
            return self.receive_proposal_offer(proposal=message)
        if isinstance(message, Proposal):
            self.receive_proposal(proposal=message)
            return

    def send_proposal(self, productions: List[Production], path_node: List[str] = []):
        """
        Send production proposal to all border.

        :param productions: production capacity to sell
        :param path_node: history node already receive this proposal
        :return:
        """

        for b in self.borders:
            proposales = [Proposal(id=self.uuid_generate(),
                                   cost=prod.cost + b.cost,
                                   quantity=prod.quantity,
                                   path_node=[self.name] + path_node)
                          for prod in productions]
            for prop in proposales:
                if b not in prop.path_node:
                    self.registry.get(b.dest).tell(prop)


    def receive_proposal(self, proposal: Proposal):
        prod = Production(cost=proposal.cost, quantity=proposal.quantity, type='import', id=proposal.id)
        new_state = self.optimize_adequacy([prod] + self.state.productions_used)
        if new_state.cost < self.state.cost:
            self.responce_proposal(proposal, new_state)
        else:
            self.send_proposal(productions=[prod], path_node=proposal.path_node)

    def receive_proposal_offer(self, proposal: ProposalOffer) -> ProposalFinal:
        print(self.name, 'receive offer !')

    def responce_proposal(self, proposal: Proposal, new_state: NodeState):
        prod_asked = Dispatcher.find_production(new_state.productions_used, proposal.id)
        prop_asked = ProposalOffer(id=proposal.id, cost=proposal.cost, quantity=prod_asked.quantity, path_node=proposal.path_node)
        prop_final = self.registry.get(proposal.path_node[0]).ask(prop_asked)
        print(prop_final)


    def optimize_adequacy(self, productions: List[Production]) -> NodeState:
        """
        Compute adequacy by optimizing mix cost

        :param productions: production capacities
        :return: NodeState with new production used stack, free production, current rac and cost
        """
        productions.sort(key=lambda x: x.cost)

        productions_used = []
        productions_free = []

        rac = - sum([c.quantity for c in self.consumptions])
        cost = 0

        # Compute prod cost
        for prod in productions:
            used = min(prod.quantity, max(0, -rac))
            productions_used.append(Dispatcher.copy_production(prod, used))
            rac += prod.quantity
            cost += prod.cost*used

            free = prod.quantity - used
            if free > 0:
                productions_free.append(Dispatcher.copy_production(prod, free))

        # Compute load cost
        i = 0
        reverse = self.consumptions[::-1]
        gap = rac
        while gap < 0 and i < len(reverse):
            cons = reverse[i]
            cost += cons.cost*min(abs(gap), cons.quantity)
            gap = cons.quantity

        return NodeState(productions_used, productions_free, cost, rac)

    @staticmethod
    def find_production(prods: List[Production], id: uuid) -> Production:
        return list(filter(lambda x: x.id == id, prods))[0]

    @staticmethod
    def copy_production(production: Production, quantity: int) -> Production:
        p = copy(production)
        p.quantity = quantity
        return p



