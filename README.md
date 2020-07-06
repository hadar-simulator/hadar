# Hadar
[![PyPI](https://img.shields.io/pypi/v/hadar)](https://pypi.org/project/hadar/)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/hadar-simulator/hadar/main/master)](https://github.com/hadar-simulator/hadar/action)
[![https://sonarcloud.io/dashboard?id=hadar-solver_hadar](https://sonarcloud.io/api/project_badges/measure?project=hadar-solver_hadar&metric=alert_status)](https://sonarcloud.io/dashboard?id=hadar-solver_hadar)
[![https://sonarcloud.io/dashboard?id=hadar-solver_hadar](https://sonarcloud.io/api/project_badges/measure?project=hadar-solver_hadar&metric=coverage)](https://sonarcloud.io/dashboard?id=hadar-solver_hadar)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/hadar-simulator/hadar/master?filepath=examples)
[![website](https://img.shields.io/badge/website-hadar--simulator.org-blue)](https://www.hadar-simulator.org/)
[![GitHub](https://img.shields.io/github/license/hadar-simulator/hadar)](https://github.com/hadar-simulator/hadar/blob/master/LICENSE)


Hadar is a adequacy python library for deterministic and stochastic computation

## Adequacy problem
### Basic

Each kind of network has a needs of adequacy. On one side, some network nodes need to consume
items such as watt, litter, package. And other side, some network nodes produce items.
Applying adequacy on network, is tring to find the best available exchanges to avoid any lack at the best cost.

For example, a electric grid can have some nodes wich produce too more power and some nodes which produce not enough power.

![adequacy](examples/Get%20Started/figure.png)


### Complexity comes soon
Above example is simple, but problem become very tricky with 10, 20 or 500 nodes !

Moreover all have a price ! Node can have many type of production, and each kind of production has its unit cost. Node can have also many consumptions with specific unavailability cost. Links between node have also max capacity and cost.

Network adequacy is not simple.

## Hadar
Hadar computes adequacy from simple to complex network. For example, to compute above network, just few lines need:

``` python
import hadar as hd

study = hd.Study(horizon=3)\
    .network()\
        .node('a')\
            .consumption(cost=10 ** 6, quantity=[20, 20, 20], name='load')\
            .production(cost=10, quantity=[30, 20, 10], name='prod')\
        .node('b')\
            .consumption(cost=10 ** 6, quantity=[20, 20, 20], name='load')\
            .production(cost=10, quantity=[10, 20, 30], name='prod')\
        .link(src='a', dest='b', quantity=[10, 10, 10], cost=2)\
        .link(src='b', dest='a', quantity=[10, 10, 10], cost=2)\
    .build()

optimizer = hd.LPOptimizer()
res = optimizer.solve(study)
```

And few more lines to display graphics results.

```python
plot = hd.HTMLPlotting(agg=hd.ResultAnalyzer(study, res),
                       node_coord={'a': [2.33, 48.86], 'b': [4.38, 50.83]})
plot.network().node('a').stack()
plot.network().map(t=0, zoom=2.5)
```

Get more information and examples at [https://www.hadar-simulator.org/](https://www.hadar-simulator.org/)