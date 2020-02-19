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


.. toctree::
   :maxdepth: 1
   :caption: Tutorials:

   tutorials/introduction.rst

.. toctree::
   :maxdepth: 2
   :caption: Reference:

   reference/hadar.rst