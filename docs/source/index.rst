.. hadar-simulator documentation master file, created by
   sphinx-quickstart on Wed Feb 19 13:28:27 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Hadar!
===========================================
.. image:: https://img.shields.io/pypi/v/hadar
.. image:: https://img.shields.io/github/workflow/status/hadar-solver/hadar/main/master
.. image:: https://sonarcloud.io/api/project_badges/measure?project=hadar-solver_hadar&metric=alert_status
.. image:: https://sonarcloud.io/api/project_badges/measure?project=hadar-solver_hadar&metric=coverage
.. image:: https://img.shields.io/github/license/hadar-solver/hadar


Hadar is a adequacy python library for deterministic and stochastic computation

Adequacy problem
^^^^^^^^^^^^^^^^

Each kind of network has a needs of adequacy. On one side, some network nodes need to consume
items such as watt, litter, package. And other side, some network nodes produce items.
Applying adequacy on network, is tring to find the best available exchanges to avoid any lack at the best cost.

For example, a electric grid can have some nodes wich produce too more power and some nodes wich produce not enough power.

.. image:: https://mermaid.ink/img/eyJjb2RlIjoiZ3JhcGggTFJcblx0QVtBPGJyLz5sb2FkPTIwPGJyLz5wcm9kPTMwXSAtLT5CW0I8YnIvPmxvYWQ9MjA8YnIvPnByb2Q9MTBdXG5cdFx0XHRcdFx0IiwibWVybWFpZCI6eyJ0aGVtZSI6ImRlZmF1bHQifSwidXBkYXRlRWRpdG9yIjpmYWxzZX0

In this case, A produce 10 more and B need 10 more. Perform adequecy is quiet easy : A will share 10 to B

.. image:: https://mermaid.ink/img/eyJjb2RlIjoiZ3JhcGggTFJcblx0QVtBPGJyLz5sb2FkPTIwPGJyLz5wcm9kPTMwXSAtLT4gfHNoYXJlIDEwfCBCW0I8YnIvPmxvYWQ9MjA8YnIvPnByb2Q9MTBdXG5cdFx0XHRcdFx0IiwibWVybWFpZCI6eyJ0aGVtZSI6ImRlZmF1bHQifX0)

Hadar compute adequacy from simple to complex network. For example, to compute above network, just few line need::

   from hadar.solver.input import *
   from hadar.solver.study import solve

   study = Study(['a', 'b']) \
      .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[20, 20], type='load')) \
      .add_on_node('a', data=Production(cost=10, quantity=[30, 30], type='prod')) \
      .add_on_node('b', data=Consumption(cost=10 ** 6, quantity=[20, 20], type='load')) \
      .add_on_node('b', data=Production(cost=20, quantity=[10, 10], type='prod')) \
      .add_border(src='a', dest='b', quantity=[10, 10], cost=2) \

   res = solve(study)

Then you can analyze by yourself result or use hadar aggragator and plotting::

   from hadar.aggregator.result import ResultAggregator
   from hadar.viewer.jupyter import JupyterPlotting
   plot = JupyterPlotting(agg=ResultAggregator(study, res),
                       node_coord={'a': [2.33, 48.86], 'b': [4.38, 50.83]})
   plot.stack(node='a')

.. image:: /_static/get-started-1.png

Or ::

   plot.stack(node='b')
.. image:: /_static/get-started-2.png

Or ::

   plot.exchanges_map(t=0)
.. image:: /_static/get-started-3.png

.. toctree::
   :maxdepth: 1
   :caption: Architecture:

   architecture/overview.rst
   architecture/workflow.rst
   architecture/optimizer.rst
   architecture/analyzer.rst
   architecture/viewer.rst

.. toctree::
   :maxdepth: 1
   :caption: Mathematics:

   mathematics/linear-model.rst

.. toctree::
   :maxdepth: 1
   :caption: Dev Guide:

   dev-guide/repository.rst
   dev-guide/best-practices.rst
   dev-guide/devops.rst

.. toctree::
   :maxdepth: 1
   :caption: Reference:

   reference/hadar.workflow.rst
   reference/hadar.optimizer.rst
   reference/hadar.analyzer.rst
   reference/hadar.viewer.rst

.. toctree::
   :maxdepth: 1
   :caption: Legal Terms

   terms/terms.rst