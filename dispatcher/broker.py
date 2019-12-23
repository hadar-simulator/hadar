import uuid
from typing import List
from copy import copy, deepcopy

from adequacy import optimize_adequacy
from dispatcher.domain import *


class LedgerExchange:

    def __init__(self):
        self.ledger = {}

    def add_all(self, ex: List[Exchange]):
        for e in ex:
            self.add(e)

    def add(self, ex: Exchange):
        border = ex.path_node[0]
        if border not in self.ledger.keys():
            self.ledger[border] = {}
        if ex.production_id not in self.ledger[border].keys():
            self.ledger[border][ex.production_id] = {}

        if ex.id in self.ledger[border][ex.production_id].keys():
            raise ValueError('Exchange already stored in ledger')
        self.ledger[border][ex.production_id][ex.id] = ex

    def delete(self, ex: Exchange):
        for border, productions in self.ledger.items():
            if ex.production_id in productions.keys():
                for _,  exchanges in productions.items():
                    if ex.id in exchanges.keys():
                        del self.ledger[border][ex.production_id][ex.id]

    def delete_all(self, exs: List[Exchange]):
        for ex in exs:
            self.delete(ex)

    def sum_production(self, production_id):
        acc = 0
        for border, prods in self.ledger.items():
            if production_id in prods.keys():
                acc += sum([ex.quantity for ex in prods[production_id].values()])
        return acc

    def sum_border(self, name: str):
        if name not in self.ledger.keys():
            return 0
        acc = 0
        for prod in self.ledger[name].values():
            acc += sum([ex.quantity for ex in prod.values()])
        return acc


class Broker:
    """Manage exchange and proposal shared"""
    def __init__(self, name,
                 tell,
                 ask,
                 uuid_generate=uuid.uuid4,
                 ledger_exchange: LedgerExchange = None,
                 min_exchange: int=1,
                 consumptions: List[Consumption] = [],
                 productions: List[Production] = [],
                 borders: List[Border] = []):
        super().__init__()

        self.name = name
        self.tell = tell
        self.ask = ask
        self.uuid_generate = uuid_generate
        self.consumptions = sorted(consumptions, key=lambda x: x.cost, reverse=True)
        self.raw_productions = Broker.generate_production_id(productions, self.uuid_generate)
        self.borders = borders
        self.ledger_exchanges = LedgerExchange() if ledger_exchange is None else ledger_exchange
        self.min_exchange = min_exchange

        self.state = optimize_adequacy(self.consumptions, self.raw_productions)

    def init(self):
        """
        Initiate exchange by sending proposal.

        """
        self.send_proposal(productions=self.state.productions_free)

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
        new_state = optimize_adequacy(self.consumptions, [prod] + self.state.productions_used + self.state.productions_free)
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
        # Check border capacity
        border = Broker.find_border(self.borders, path=proposal.return_path_node)
        free_border_capacity = border.capacity - self.ledger_exchanges.sum_border(border.dest)
        if not free_border_capacity:
            return []
        proposal.quantity = min(free_border_capacity, proposal.quantity)

        # Forward proposal if path has next dispatcher
        if len(proposal.path_node) > 1:
            forward = deepcopy(proposal)
            forward.path_node = proposal.path_node[1:]
            ex = self.ask(to=forward.path_node[0], mes=forward)

            # Save exchange to ledger
            for e in deepcopy(ex):
                e.path_node = self.trim_path(e.path_node)
                self.ledger_exchanges.add(e)
            return ex

        # Check production remain capacity
        quantity_free = Broker.find_production(self.state.productions_free, proposal.production_id).quantity
        quantity_used = self.ledger_exchanges.sum_production(proposal.production_id)

        # Send available exchange
        quantity_exchange = min(proposal.quantity, quantity_free - quantity_used)
        ex = self.generate_exchanges(quantity=quantity_exchange,
                                     production_id=proposal.production_id,
                                     path_node=proposal.return_path_node)
        # Save exchange in ledger
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
        prod_asked = Broker.find_production(new_state.productions_used, proposal.production_id)
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

        self.state = optimize_adequacy(consumptions=self.consumptions,
                                       productions=prod + self.state.productions_used + self.state.productions_free)

        # Forward proposal with remaining quantity
        exchanges_quantity = sum([ex.quantity for ex in exchanges])
        self.send_remain_proposal(proposal=proposal, asked_quantity=prop_asked.quantity, given_quantity=exchanges_quantity)

        self.optimize_free_productions()

    def optimize_free_productions(self):
        """
        Cancel useless exchange. Resend proposal for free productions.

        :return:
        """

        # Cancel useless exchange
        useless_exchanges = Broker.filter_exchanges(self.state.productions_free)
        self.send_cancel_exchange(useless_exchanges)

        # Resend proposal
        free_prods = Broker.filter_productions(self.state.productions_free)
        self.send_proposal(productions=free_prods)

    def receive_cancel_exchange(self, cancel: ConsumerCanceledExchange):
        """
        Delete exchange in ledger. Forward cancel or resend proposal if node are the producer of this exchange.

        :param cancel: exchanges to cancel
        :return:
        """
        # delete exchange in ledger
        self.ledger_exchanges.delete_all(cancel.exchanges)

        # Forward if path node has next
        if len(cancel.path_node) > 1:
            cancel = deepcopy(cancel)
            cancel.path_node = cancel.path_node[1:]
            self.tell(to=cancel.path_node[0], mes=cancel)
            return

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
            cancel = ConsumerCanceledExchange(exchanges=ex, path_node=path)
            self.tell(to=path[0], mes=cancel)

    def generate_exchanges(self, production_id: int, quantity: int, path_node: List[str]):
        """
        Generate list to exchanges to fill available quantity with minimum exchange capacity.

        :param production_id: id production to embedded
        :param quantity:  quantity to use to generate exchange list
        :param path_node: path node to embedded
        :return: list of exchanges. sum of capacities equals or less quantity asked
        """
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

    def compute_total(self):
        """
        Compute total production used, and exchange at borders
        :return:
        """
        # Compute productions
        productions = deepcopy(self.raw_productions)
        for p in productions:
            p.quantity = sum([used.quantity for used in self.state.productions_used if used.id == p.id])
            p.quantity += self.ledger_exchanges.sum_production(p.id)

        # Compute borders
        borders = deepcopy(self.borders)
        for b in borders:
            b.capacity = self.ledger_exchanges.sum_border(b.dest)
        return self.consumptions, productions, borders

    def trim_path(self, path: List[str]):
        """
        trim older nodes in path.

        :param path: whole path from exchange producer
        :return: trimed path with only next nodes
        """
        while path[0] != self.name and len(path) > 0:
            del path[0]
        del path[0]
        return path


    @staticmethod
    def generate_production_id(productions: List[Production], uuid_generate):
        for p in productions:
            p.id = uuid_generate()
        return productions

    @staticmethod
    def filter_exchanges(prods: List[Production]) -> List[Exchange]:
        return [prod.exchange for prod in prods if prod.exchange is not None]

    @staticmethod
    def filter_productions(prods: List[Production]) -> List[Production]:
        return [prod for prod in prods if prod.exchange is None]

    @staticmethod
    def find_production(prods: List[Production], id: uuid) -> Production:
        return list(filter(lambda x: x.id == id, prods))[0]


    @staticmethod
    def find_border(borders: List[Border], path: List[str]) -> Border:
        return [b for b in borders if b.dest in path][0]
    @staticmethod
    def copy_production(production: Production, quantity: int) -> Production:
        p = copy(production)
        p.quantity = quantity
        return p
