from copy import deepcopy, copy

from solver.actor.domain import *


def is_same_prod(a: Production, b: Production):
    """
    Compare production.

    :param a: production to compare
    :param b: production to compare
    :return: return True if id, type and exchange are the same.
    """
    if a.id != b.id:
        return False
    if a.type != b.type:
        return False
    if a.exchange != b.exchange:
        return False
    if a.exchange is None and b.exchange is None:
        return True
    return a.exchange.id == b.exchange.id


def clean_production(productions: List[Production]) -> List[Production]:
    """
    Make a copy of production. Sort them. Regroupe quantity if same production.

    :param productions: production to clean before optimize
    :return: productions copied, sorted and grouped
    """
    productions = deepcopy(productions)
    productions.sort(key=lambda x: x.cost)

    # Merge same production (same id and exchange id)
    i = 0
    while i < len(productions):
        while i+1 < len(productions) and is_same_prod(productions[i], productions[i+1]):
            productions[i].quantity += productions[i+1].quantity
            del productions[i+1]
        i += 1
    return productions


def copy_production(production: Production, quantity: int) -> Production:
    """
    Copy production and update quantity
    :param production:
    :param quantity:
    :return:
    """
    p = copy(production)
    p.quantity = quantity
    return p


def optimize_adequacy(consumptions: List[Consumption], productions: List[Production]) -> NodeState:
    """
    Compute adequacy by optimizing mix cost

    :param productions: production capacities
    :return: NodeState with new production used stack, free production, current rac and cost
    """

    productions = clean_production(productions)

    productions_used = []
    productions_free = []

    rac = - sum([c.quantity for c in consumptions])
    cost = 0

    # Compute prod cost
    for prod in productions:
        used = min(prod.quantity, max(0, -rac))
        if used:
            productions_used.append(copy_production(prod, used))
        rac += prod.quantity
        cost += prod.cost*used

        free = prod.quantity - used
        if free:
            productions_free.append(copy_production(prod, free))

    # Compute load cost
    i = 0
    reverse = consumptions[::-1]
    gap = rac
    while gap < 0 and i < len(reverse):
        cons = reverse[i]
        cost += cons.cost*min(abs(gap), cons.quantity)
        gap = cons.quantity

    return NodeState(productions_used, productions_free, cost, rac)
