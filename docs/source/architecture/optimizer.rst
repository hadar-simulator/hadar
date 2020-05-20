Optimizer
=========

Optimizer is the heart of Hadar. Behind it, there are :

#. Input object called :code:`Study`. Output object called :code:`Result`. These two objects encapsulate all data needed to compute adequacy.

#. Many optimizers. User can choose in which will solve study.

Therefore :code:`Optimizer` is an abstract class builded on *Strategy* pattern. User can select optimizer or create their own by implemented :code:`Optimizer.solve(study: Study) -> Result`

Today, two optimizers are present :code:`LPOptimizer` and :code:`RemoteOptimizer`

TODO ULM Optimizer

RemoteOptimizer
---------------

Let's start by the simplest. :code:`RemoteOptimizer` is a client to hadar server. As you may know Hadar exist like a python library, but has also a tiny project to package hadar inside web server. You can find more details on this server in this `repository.  <https://github.com/hadar-simulator/simple-server>`_

Client implements :code:`Optimizer` interface. Like that, to deploy compute on a datacenter, only one line of code changes. ::

    import hadar as hd
    # Normal : optim = hd.LPOptimizer()
    optim = hd.RemoteOptimizer(host='example.com')
    res = optim.solve(study=study)


LPOptimizer
-----------

Before read this chapter, we kindly advertise you to read :ref:`Linear Model <linear-model>`

:code:`LPOptimizer` translate data into optimization problem. Hadar algorithms focus only on modeling problem and uses `or-tools <https://developers.google.com/optimization>`_ to solve problem.

To achive modeling goal, :code:`LPOptimizer` is designed to receive :code:`Study` object, convert data into or-tools *Variables*. Then *Variables* are placed inside objective and constraint equations. Equations are solved by or-tools. Finally *Variables* are converted to :code:`Result` object.

Analyze that in details.

InputMapper
************

If you look in code, you will see two domain. One at :code:`hadar.optimizer.[input/output]` and another at :code:`hadar.optimizer.lp.domain` . If you look carefully it seems the same :code:`Consumption` , :code:`OutputConsumption` in one hand, :code:`LPConsumption` in other hand. The only change is a new attribute in :code:`LP*` called :code:`variable` . Variables are the parameters of the problem. It's what or-tools has to find, i.e. power used for production, capacity used for border and lost of load for consumption.

Therefore, :code:`InputMapper` roles are just to create new object with ortools Variables initialized, like we can see in this code snippet. ::

    # hadar.optimizer.lp.mapper.InputMapper.get_var
    LPLink(dest=l.dest,
           cost=float(l.cost),
           src=name,
           quantity=l.quantity[scn, t],
           variable=self.solver.NumVar(0, float(l.quantity[scn, t]),
              'link on {} to {} at t={} for scn={}'.format(name, l.dest, t, scn)
           )
     )

OutputMapper
************

At the end, :code:`OutputMapper` does the reverse thing. :code:`LP*` objects have computed variables. We need to extract result find by or-tool to :code:`Result` object.

Mapping of :code:`LPProduction` and :code:`LPLink` are straight forward. I propose you to look at :code:`LPConsumption` code ::

    self.nodes[name].consumptions[i].quantity[scn, t] =
    vars.consumptions[i].quantity - vars.consumptions[i].variable.solution_value()

Line seems strange due to complex index. First we select good node *name*, then good consumption *i*, then good scenario *scn* and at this end good timestep *t*. Rewritting without index, this line means :

.. math::
    Cons_{final} = Cons_{given} - Cons_{var}

Keep in mind that :math:`Cons_{var}` is the lost of load. So we need to substract it from initial consumption to get really consumption sustained.

Modeler
*******

Hadar has to build problem optimization. These algorithms are encapsulated inside two builders.

:code:`ObjectiveBuilder` get node by its method :code:`add_node`. Then for all productions, consumptions, links, it adds :math:`variable * cost` into objective equation.

:code:`AdequacyBuilder` is a bit more tricky. For each node, it will create a new adequacy contraint equation (c.f. :ref:`Linear Model <linear-model>`). Coefficients, here are 1 or -1 depending of *inner* power or *outer* power. You also have see these lines ::

    self.constraints[(t, link.src)].SetCoefficient(link.variable, -1)  # Export from src
    self.importations[(t, link.src, link.dest)] = link.variable  # Import to dest

Hadar has to set power importation to *dest* node equation. But maybe this node is not yet setup and this constraint equation doesn't exist yet. Therefore he has to store all constraint equations and all link capacities. And at the end :code:`build()` is called ::

    def build(self):
        """
        Call when all node are added. Apply all import flow for each node.

        :return:
        """
        # Apply import link in adequacy
        for (t, src, dest), var in self.importations.items():
            self.constraints[(t, dest)].SetCoefficient(var, 1)

Which will add importation terms into all adequacy constraints to finalize equations.

:code:`solve_batch` method resolve study scenario by scenario. It iterates over node and time, calls :code:`InputMapper`, then constructs problem with :code:`*Buidler`, and asks or-tools to solve problem.

:code:`solve_lp` applies the last iteration over scenarios and it's the entry point for linear programming optimizer. After all scenarios are solved, results are mapped to :code:`Result` object.

Or-tools, multiprocessing & pickle nightmare
............................................

Scenarios are distributed over cores by mutliprocessing library. :code:`solve_batch` is the compute method called by multiprocessing. Therefore all input data received by this method and output data returned must be serializable by pickle (used by multiprocessing). However, output has ortools :code:`Variable` object which is not serializable.

Hadar doesn't need complet :code:`Variable` object. Indeed, it just want value solution found by or-tools. So we will help pickle by creating more simpler object ::

    class SerializableVariable(DTO):
        def __init__(self, var: Variable):
            self.val = var.solution_value()

        def solution_value(self):
            return self.val

Then specify cleary how to serialize object by implementing :code:`__reduce__` method ::

    # hadar.optimizer.lp.domain.LPConsumption
    def __reduce__(self):
        """
        Help pickle to serialize object, specially variable object
        :return: (constructor, values...)
        """
        return self.__class__, (self.quantity, SerializableVariable(self.variable), self.cost, self.name)

It should work, but in fact not... I don't know why, when multiprocessing want to serialize returned data, or-tools :code:`Variable` are empty, and mutliprocessing failed. Nevermind, we just need to handle serialization oneself ::

    # hadar.optimizer.lp.solver._solve_batch
    return pickle.dumps(variables)

TODO ULM LPOptimizer

Study
-----

:code:`Study` is a *API object* I means it encapsulates all data needed to compute adequacy. It's the glue between workflow (or any other preprocessing) and optimizer. Study has an hierarchical structure of 3 levels :

#. node level with node name as key.

#. type elements level with *consumption*, *production* and *link* entries. Represented by :code:`InputNode` object.

#. element with index as key. Represented by :code:`Consumption`, :code:`Production`, :code:`Link` objects

Most important attribute could be :code:`quantity` which represent quantity of power used in network. For link, is a transfert capacity. For production is a generation capacity. For consumption is a forced load to sustain.

User can construct Study step by step thanks to a *fluent API* ::

    import hadar as hd

    study = hd.Study(['a', 'b'], horizon=3) \
      .add_on_node('a', data=hd.Consumption(cost=10 ** 6, quantity=[20, 20, 20], name='load')) \
      .add_on_node('a', data=hd.Production(cost=10, quantity=[30, 20, 10], name='prod')) \
      .add_on_node('b', data=hd.Consumption(cost=10 ** 6, quantity=[20, 20, 20], name='load')) \
      .add_on_node('b', data=hd.Production(cost=20, quantity=[10, 20, 30], name='prod')) \
      .add_link(src='a', dest='b', quantity=[10, 10, 10], cost=2) \
      .add_link(src='b', dest='a', quantity=[10, 10, 10], cost=2) \


    optim = hd.LPOptimizer()
    res = optim.solve(study)

To help user, quantity field is flexible:

* lists are converted to numpy array

* if user give a scalar, hadar extends to create (scenario, horizon) matrix size

* if user give (horizon, ) matrix or list, hadar copies N time scenario to make (secnario, horizon) matrix size

* if user give (scenario, 1) matrix or list, hadar copies N time timestep to make (scenario, horizon) matrix size

Study includes also check mechanism to be sure: node existe, consumption is unique, etc.

Result
------

:code:`Result` look like :code:`Study`, it has the same hierarchical structure, same element, just different naming to respect *Domain Driven Development* . Indeed, :code:`Result` is used as output computation, therefore we can reuse the same object.
:code:`Result` is the glue between optimizer and analyzer (or any else postprocessing).

:code:`Result` souldn't be created by user. User will only read it. So, :code:`Result` has not fluent API to help construction.
