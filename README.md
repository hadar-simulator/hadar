# Hadar
![PyPI](https://img.shields.io/pypi/v/hadar)
![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/hadar-simulator/hadar/main/master)
![https://sonarcloud.io/dashboard?id=hadar-solver_hadar](https://sonarcloud.io/api/project_badges/measure?project=hadar-solver_hadar&metric=alert_status)
![https://sonarcloud.io/dashboard?id=hadar-solver_hadar](https://sonarcloud.io/api/project_badges/measure?project=hadar-solver_hadar&metric=coverage)
![GitHub](https://img.shields.io/github/license/hadar-simulator/hadar)


Hadar is a adequacy python library for deterministic and stochastic computation

## Adequacy problem
### Basic

Each kind of network has a needs of adequacy. On one side, some network nodes need to consume
items such as watt, litter, package. And other side, some network nodes produce items.
Applying adequacy on network, is tring to find the best available exchanges to avoid any lack at the best cost.

For example, a electric grid can have some nodes wich produce too more power and some nodes wich produce not enough power.
```
+---------+             +---------+
| Node A  |             | Node B  |
|         |             |         |
| load=20 +-------------+ load=20 |
| prod=30 |             | prod=10 |
|         |             |         |
+---------+             +---------+
```


In this case, A produce 10 more and B need 10 more. Perform adequecy is quiet easy : A will share 10 to B
```
+---------+             +---------+
| Node A  |             | Node B  |
|         |   share 10  |         |
| load=20 +------------>+ load=20 |
| prod=30 |             | prod=10 |
|         |             |         |
+---------+             +---------+
```

### Complexity comes soon
Above example is simple, but problem become very tricky with 10, 20 or 500 nodes !

Moreovore all have a price ! Node can have many type of production, and each kind of production has its unit cost. Node can have also many consumptions with specific unavailability cost. Links between node have also max capacity and cost.

Network adequacy is not simple.

## Hadar
Hadar compute adequacy from simple to complex network. For example, to compute above network, just few line need:
``` python
from hadar.solver.input import *
from hadar.solver.study import solve

study = Study(['a', 'b']) \
    .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[20], type='load')) \
    .add_on_node('a', data=Production(cost=10, quantity=[30], type='prod')) \
    .add_on_node('b', data=Consumption(cost=10 ** 6, quantity=[20], type='load')) \
    .add_on_node('b', data=Production(cost=20, quantity=[10], type='prod')) \
    .add_border(src='a', dest='b', quantity=[10], cost=2) \

res = solve(study)
```
