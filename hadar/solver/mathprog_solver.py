from hadar.solver.actor.domain.input import Study

from ortools.linear_solver import pywraplp


def solve(study: Study) -> Study:
    # Create the linear solver with the GLOP backend.
    ortools_solver = pywraplp.Solver('simple_lp_program',
                                     pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
    objective = ortools_solver.Objective()
    objective.SetMinimization()
    x_production = {}
    for name, nodes in study.nodes.items():
        sum_of_conso = {}
        for consumption in nodes.consumptions:
            for t in range(len(consumption.quantity)):
                sum_of_conso[t] = dict.get(sum_of_conso, t, 0) + consumption.quantity

        eod_constraints = {(name, t): ortools_solver.Constraint(float(load), float(load)) for t, load in
                           sum_of_conso.items()}
        # eod_constraint[t].set 'eod[' + name + ', ' + str(t) + ']'
        for production in nodes.productions:
            for t in range(len(production.quantity)):
                var_name = 'p[' + name + ', ' + production.type + ', ' + str(t) + ']'
                x_production[name, production.type, t] = ortools_solver.NumVar(0, production.quantity[t] * 1.0,
                                                                               var_name)
                objective.SetCoefficient(x_production[name, production.type, t], production.cost * 1.0)
                eod_constraints[name, t].SetCoefficient(x_production[name, production.type, t], 1)
            pass
        # dest = 'b', quantity = [20], cost = 2),
    x_border = {}
    for border in nodes.borders:
        i = name, border.dest
        j = name, border.dest
        if not (i, j) in x_border:
            x_border[i, j] = {t: ortools_solver.NumVar(0, border.quantity[t] * 1.0,
                                                       'border[' + str(i) + ', ' + str(j) + ', ' + str(t) + ']')
                              for t in range(len(border.quantity))}
        for t, x in x_border[i, j].items():
            objective.SetCoefficient(x, border.cost * 1.0)
            eod_constraints[i, t].SetCoefficient(x, -1)
            eod_constraints[j, t].SetCoefficient(x, +1)
        pass
    # Create the EOD constraint
    ortools_solver.EnableOutput()
    ortools_solver.Solve()

    print('\n--- Minimum objective function value = %d' % ortools_solver.Objective().Value())
    # print(ortools_solver.ExportModelAsLpFormat(False).replace('\\', '').replace(',_', ','), sep='\n')
    for ijk, x_t in x_production.items():
        print(x_t.name(), ' = ', x_t.solution_value())
    for ij, x in x_border.items():
        for t, x_t in x.items():
            print(x_t.name(), ' = ', x_t.solution_value())
    nodes = {}
    return Study(nodes=nodes)
