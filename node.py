import uuid
from typing import List
from copy import copy, deepcopy

from pykka import ThreadingActor

from domain import *
from manager import DispatcherRegistry


class LedgerExchange:

    def __init__(self):
        self.ledger = {}

    def add_all(self, ex: List[Exchange]):
        for e in ex:
            self.add(e)

    def add(self, ex: Exchange):
        if ex.production_id not in self.ledger.keys():
            self.ledger[ex.production_id] = {}

        if ex.id in self.ledger[ex.production_id].keys():
            raise ValueError('Exchange already stored in ledger')
        self.ledger[ex.production_id][ex.id] = ex

    def delete(self, ex: Exchange):
        if ex.production_id in self.ledger.keys():
            del self.ledger[ex.production_id][ex.id]

    def delete_all(self, exs: List[Exchange]):
        for ex in exs:
            self.delete(ex)

    def sum_production(self, production_id):
        if production_id not in self.ledger.keys():
            return 0
        return sum([ex.quantity for ex in self.ledger[production_id].values()])


class Dispatcher(ThreadingActor):

    def __init__(self, name,
                 uuid_generate=uuid.uuid4,
                 registry: DispatcherRegistry = DispatcherRegistry(),
                 ledger_exchange: LedgerExchange = None,
                 min_exchange: int=1,
                 consumptions: List[Consumption] = [],
                 productions: List[Production] = [],
                 borders: List[Border] = []):
        super().__init__()

        self.name = name
        self.uuid_generate = uuid_generate
        self.consumptions = sorted(consumptions, key=lambda x: x.cost, reverse=True)
        self.raw_productions = Dispatcher.generate_production_id(productions, self.uuid_generate)
        self.borders = borders
        self.ledger_exchanges = LedgerExchange() if ledger_exchange is None else ledger_exchange
        self.min_exchange = min_exchange
        self.registry = registry
        self.registry.add(self)
        self.events = []


        self.state = self.optimize_adequacy(self.raw_productions)
        print(self.name, 'cost=', self.state.cost)

    def on_receive(self, message):
        """
        Mail box of actor.

        :param message: next message to process
        :return:
        """
        self.events.append(Event(type='recv', message=message))
        if isinstance(message, Start):
            self.send_proposal(productions=self.state.productions_free)
        elif isinstance(message, Snapshot):
            return self
        elif isinstance(message, ProposalOffer):
            ex = self.receive_proposal_offer(proposal=message)
            self.events.append(Event(type='recv res', message=ex))
            return ex
        elif isinstance(message, Proposal):
            self.receive_proposal(proposal=message)
        elif isinstance(message, CanceledExchange):
            self.receive_cancel_exchange(cancel=message)

    def tell(self, to: str, mes):
        self.events.append(Event(type='tell', message=mes))
        self.registry.get(to).tell(mes)

    def ask(self, to: str, mes):
        self.events.append(Event(type='ask', message=mes))
        res = self.registry.get(to).ask(mes)
        self.events.append(Event(type='ask res', message=res))
        return res

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
                    self.tell(to=b.dest, mes=prop)

    def receive_proposal(self, proposal: Proposal):
        """
        Decide to use proposal or to spread to border.

        :param proposal: proposal from network
        :return:
        """
        # TODO test
        prod = Production(cost=proposal.cost, quantity=proposal.quantity, type='import', id=proposal.production_id)
        new_state = self.optimize_adequacy([prod] + self.state.productions_used + self.state.productions_free)
        if new_state.cost < self.state.cost:
            self.make_offer(proposal, new_state)
        else:
            self.send_proposal(productions=[prod], path_node=proposal.path_node)

    def receive_proposal_offer(self, proposal: ProposalOffer) -> List[Exchange]:
        """
        Return exchanges available for proposal offer according to border capacity and production free.

        :param proposal: proposal offer returning by a dispatcher
        :return: exchanges still available to respond to offer
        """
        # TODO check border capacity

        # Forward proposal if path has next dispatcher
        if len(proposal.path_node) > 1:
            forward = deepcopy(proposal)
            forward.path_node = proposal.path_node[1:]
            return self.registry.get(forward.path_node[0]).ask(forward)

        quantity_free = Dispatcher.find_production(self.state.productions_free, proposal.production_id).quantity
        quantity_used = self.ledger_exchanges.sum_production(proposal.production_id)

        quantity_exchange = min(proposal.quantity, quantity_free - quantity_used)
        ex = self.generate_exchanges(quantity=quantity_exchange,
                                     production_id=proposal.production_id,
                                     path_node=proposal.return_path_node)

        if quantity_exchange > 0:
            self.ledger_exchanges.add_all(ex)
        return [deepcopy(e) for e in ex]


    def make_offer(self, proposal: Proposal, new_state: NodeState):
        """
        Ask offer to dispatcher producer. Update state and exchange according to offer response.

        :param proposal: initial proposal from dispatcher producer
        :param new_state: state computed with proposal production
        :return:
        """
        # Build offer
        prod_asked = Dispatcher.find_production(new_state.productions_used, proposal.production_id)
        prop_asked = ProposalOffer(production_id=proposal.production_id,
                                   cost=proposal.cost,
                                   quantity=prod_asked.quantity,
                                   path_node=proposal.path_node,
                                   return_path_node=proposal.path_node[-2::-1]+[self.name])

        # Receive offer result
        exchanges = self.ask(to=proposal.path_node[0], mes=prop_asked)
        prod = []
        for ex in exchanges:
            ex.path_node = proposal.path_node
            prod.append(Production(id=ex.production_id, cost=prop_asked.cost, quantity=ex.quantity, type='exchange', exchange=ex))

        self.state = self.optimize_adequacy(prod + self.state.productions_used + self.state.productions_free)

        # Forward proposal with remaining quantity
        exchanges_quantity = sum([ex.quantity for ex in exchanges])
        self.send_remain_proposal(proposal=proposal, asked_quantity=prop_asked.quantity, given_quantity=exchanges_quantity)

        # Cancel useless exchange
        useless_exchanges = Dispatcher.find_exchanges(self.state.productions_free)
        self.send_cancel_exchange(useless_exchanges)

        # TODO inspect production free to create proposal

    def receive_cancel_exchange(self, cancel: CanceledExchange):
        # TODO cancel border capacity

        # Forward if path node has next
        if len(cancel.path_node) > 1:
            cancel = deepcopy(cancel)
            cancel.path_node = cancel.path_node[1:]
            self.registry.get(cancel.path_node[0]).tell(cancel)
            return

        # Delete exchange
        self.ledger_exchanges.delete_all(cancel.exchanges)

        # Send proposal with exchange canceled
        quantity = sum([ex.quantity for ex in cancel.exchanges])
        prod_id = cancel.exchanges[0].production_id
        cost = [p.cost for p in self.raw_productions if p.id == prod_id][0]
        prod_free = Production(cost=cost, quantity=quantity, id=prod_id)
        self.send_proposal([prod_free])

    def send_remain_proposal(self, proposal: Proposal, asked_quantity: int, given_quantity: int):
        """
        Compute if remain quantity in proposal can be spread.

        :param proposal: initial proposal
        :param asked_quantity: quantity asked by dispatcher
        :param given_quantity: quantity given by producer dispatcher
        :return:
        """
        if asked_quantity < proposal.quantity and asked_quantity == given_quantity:
            prod = (Production(cost=proposal.cost,
                               quantity=proposal.quantity - asked_quantity,
                               id=proposal.production_id))
            self.send_proposal([prod], proposal.path_node)

    def send_cancel_exchange(self, exchanges: List[Exchange]):
        """
        Send canceled exchange order regrouped by production.

        :param exchanges: exchanges to cancel
        :return:
        """
        productions = {}
        for ex in exchanges:
            if ex.production_id not in productions.keys():
                productions[ex.production_id] = [[], []]
            productions[ex.production_id][0].append(ex)
            productions[ex.production_id][1] = ex.path_node

        for prod_id, (ex, path) in productions.items():
            cancel = CanceledExchange(exchanges=ex, path_node=path)
            self.tell(to=path[0], mes=cancel)

    def optimize_adequacy(self, productions: List[Production]) -> NodeState:
        """
        Compute adequacy by optimizing mix cost

        :param productions: production capacities
        :return: NodeState with new production used stack, free production, current rac and cost
        """

        productions = Dispatcher.clean_production(productions)

        productions_used = []
        productions_free = []

        rac = - sum([c.quantity for c in self.consumptions])
        cost = 0

        # Compute prod cost
        for prod in productions:
            used = min(prod.quantity, max(0, -rac))
            if used:
                productions_used.append(Dispatcher.copy_production(prod, used))
            rac += prod.quantity
            cost += prod.cost*used

            free = prod.quantity - used
            if free:
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

    def generate_exchanges(self, production_id: int, quantity: int, path_node: List[str]):
        length = int(quantity / self.min_exchange)
        exchanges = [Exchange(quantity=self.min_exchange,
                              id=self.uuid_generate(),
                              production_id=production_id,
                              path_node=path_node)
                     for i in range(0, length)]

        remain = quantity - length*self.min_exchange
        if remain:
            exchanges += [Exchange(quantity=remain, id=self.uuid_generate(), production_id=production_id, path_node=path_node)]
        return exchanges

    @staticmethod
    def clean_production(productions: List[Production]) -> List[Production]:
        productions = deepcopy(productions)
        productions.sort(key=lambda x: x.cost)

        # Merge same production (same id and exchange id)
        i = 0
        while i < len(productions):
            while i+1 < len(productions) and Dispatcher.is_same_prod(productions[i], productions[i+1]):
                productions[i].quantity += productions[i+1].quantity
                del productions[i+1]
            i += 1
        return productions

    @staticmethod
    def is_same_prod(a: Production, b: Production):
        if a.id != b.id:
            return False
        if a.type != b.type:
            return False
        if a.exchange != b.exchange:
            return False
        if a.exchange is None and b.exchange is None:
            return True
        return a.exchange.id == b.exchange.id

    @staticmethod
    def generate_production_id(productions: List[Production], uuid_generate):
        for p in productions:
            p.id = uuid_generate()
        return productions

    @staticmethod
    def find_exchanges(prods: List[Production]) -> List[Exchange]:
        return [prod.exchange for prod in prods if prod.exchange is not None]

    @staticmethod
    def find_production(prods: List[Production], id: uuid) -> Production:
        return list(filter(lambda x: x.id == id, prods))[0]

    @staticmethod
    def copy_production(production: Production, quantity: int) -> Production:
        p = copy(production)
        p.quantity = quantity
        return p


