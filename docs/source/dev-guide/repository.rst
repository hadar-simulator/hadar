Repository Organization
=======================

Hadar `repository <https://hadar-simulator/hadar>`_ is split in many parts.

* :code:`hadar/` source code

* :code:`tests/` unit and integration tests perform by unittest

* :code:`examples/` set of notebooks used like End to End test when executed during CI or like `tutorials <https://www.hadar-simulator.org/tutorials>`_ when exported to html.

* :code:`docs/` sphinx documentation hosted by readthedocs at https://docs.hadar-simulator.org . Main website is hosted by Github Pages and source code can be find in `this repository <https://github.com/hadar-simulator/hadar-simulator.github.io>`_

* :code:`.github/` github configuration to use Github Action for CI.

Ticketing
---------

We use all github features to organize development. We implement a Agile methodology and try to recreate Jira behavior in github. Therefore we swap Jira features to Github such as :

+----------------------+---------------------+
| Jira                 | github swap         |
+======================+=====================+
| User Story / Bug     | Issue               |
+----------------------+---------------------+
| Version = Sprint     | Project             |
+----------------------+---------------------+
| task                 | check list in issue |
+----------------------+---------------------+
| Epic                 | Milestone           |
+----------------------+---------------------+

Devops
------

We respect *git flow* pattern. Main developments are on :code:`develop` branch. We accept :code:`feature/**` branch but is not mandatory.

CI pipelines are backed on *git flow*, actions are sum up in table below :


+----------+----------------+--------------------+----------------------+
| action   |     develop    | release/**         | master               |
+==========+================+====================+======================+
| TU + IT  |3.6, 3.7, 3.8 / | linux-3.7          | linux-3.7            |
|          |linux, mac, win |                    |                      |
+----------+----------------+--------------------+----------------------+
| E2E      |                | from source code   | from test.pypip.org  |
+----------+----------------+--------------------+----------------------+
| Sonar    |  yes           | yes                | yes                  |
+----------+----------------+--------------------+----------------------+
| package  |                | to test.pypip.org  | to pypip.org         |
+----------+----------------+--------------------+----------------------+
