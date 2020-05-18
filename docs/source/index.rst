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

You are in the technical documentation.

* If you want to discover Hadar and the project, please go to https://www.hadar-simulator.org for an overview

* If you want to start using Hadar, you can begin with `tutorials <https://hadar-simulator.org/tutorials>`_

* If you want to understand Hadar engine, see **Architecture**

* If you want to look at a method or object behavior search inside **References**

* If you want to help us coding Hadar, please read **Dev Guide** before.

* If you want to see Mathematics model used in Hadar, go to **Mathematics**.


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