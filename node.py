import uuid
from typing import List
from copy import copy

from pykka import ThreadingActor

from domain import *
from manager import DispatcherRegistry


class LedgerExchange:

    def __init__(self):
        self.ledger = {}

    def add(self, ex: Exchange):
        if ex.production not in self.ledger.keys():
            self.ledger[ex.production] = {}

        if ex.id in self.ledger[ex.production].keys():
            raise ValueError('Exchange already stored in ledger')
        self.ledger[ex.production][ex.id] = ex

    def delete(self, ex: Exchange):
        if ex.production in self.ledger.keys():
            del self.ledger[ex.production][ex.id]

    def sum_production(self, production_id):
        if production_id not in self.ledger.keys():
            return 0
        return sum([ex.quantity for ex in self.ledger[production_id].values()])

class Dispatcher(ThreadingActor):

    def __init__(self, name,
                 uuid_generate=uuid.uuid1,
                 registry: DispatcherRegistry = DispatcherRegistry(),
                 ledger_exchange: LedgerExchange = LedgerExchange(),
                 consumptions: List[Consumption] = [],
                 productions: List[Production] = [],
                 borders: List[Border] = []):
        super().__init__()

        self.name = name
        self.uuid_generate = uuid_generate
        self.consumptions = sorted(consumptions, key=lambda x: x.cost, reverse=True)
        self.raw_productions = Dispatcher.generate_production_id(productions, self.uuid_generate)
        self.borders = borders
        self.ledger_exchanges = ledger_exchange
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
            proposals = [Proposal(production_id=prod.id,
                                  cost=prod.cost + b.cost,
                                  quantity=prod.quantity,
                                  path_node=[self.name] + path_node)
                          for prod in productions]
            for prop in proposals:
                if b not in prop.path_node:
                    self.registry.get(b.dest).tell(prop)


    def receive_proposal(self, proposal: Proposal):
        # TODO test
        prod = Production(cost=proposal.cost, quantity=proposal.quantity, type='import', id=proposal.production_id)
        new_state = self.optimize_adequacy([prod] + self.state.productions_used)
        if new_state.cost < self.state.cost:
            self.responce_proposal(proposal, new_state)
        else:
            self.send_proposal(productions=[prod], path_node=proposal.path_node)

    def receive_proposal_offer(self, proposal: ProposalOffer) -> Exchange:
        # TODO check border capacity and backward
        quantity_free = Dispatcher.find_production(self.state.productions_free, proposal.production_id).quantity
        quantity_used = self.ledger_exchanges.sum_production(proposal.production_id)

        quantity_exchange = min(proposal.quantity, quantity_free - quantity_used)
        ex = Exchange(quantity=quantity_exchange, id=self.uuid_generate(), production_id=proposal.production_id)

        if quantity_exchange > 0:
            self.ledger_exchanges.add(ex)
        return ex


    def responce_proposal(self, proposal: Proposal, new_state: NodeState):
        prod_asked = Dispatcher.find_production(new_state.productions_used, proposal.production_id)
        prop_asked = ProposalOffer(production_id=proposal.production_id, cost=proposal.cost, quantity=prod_asked.quantity, path_node=proposal.path_node)
        exchange = self.registry.get(proposal.path_node[0]).ask(prop_asked)
        print(exchange)

        # TODO follow accept exchange or refuse


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
    def generate_production_id(productions: List[Production], uuid_generate):
        for p in productions:
            p.id = uuid_generate()
        return productions

    @staticmethod
    def find_production(prods: List[Production], id: uuid) -> Production:
        return list(filter(lambda x: x.id == id, prods))[0]

    @staticmethod
    def copy_production(production: Production, quantity: int) -> Production:
        p = copy(production)
        p.quantity = quantity
        return p


