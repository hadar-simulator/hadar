.. _viewer:

Viewer
======

Even with the highest level analyzer features. Data remains simple matrix or tables. Viewer is the end of Hadar framework, it will create amazing plot to bring most valuable data for human analysis.

Viewer use Analyzer API to build plots. It like an extract layer to convert numeric result to visual result.

Viewer is split in two domains. First part implements the *FluentAPISelector*, use ResultAnalyzer to compute result and perform last compute before display graphics. This behaviour are coded inside all :code:`*FluentAPISelector` classes.

These classes are directly used by user when asking for a graphics ::

    plot = ...
    plot.network().node('fr').consumption('load').gaussian(t=4)
    plot.network().map(t=0, scn=0)
    plot.network().node('de').stack(scn=7)

For Viewer, Fluent API has these rules:

* API begins by :code:`network`.

* User can only go downstream step by step into data. He must specify element choice at each step.

* When he reaches wanted scope (network, node, production, etc), he can call graphics available for the current scope.


Second part belonging to Viewer is only for plotting. Hadar can handle many different libraries and technologies for plotting. New plotting has just to implement :code:`ABCPlotting` and :code:`ABCElementPlotting` . Today one HTML implementation exist with plotly library inside :code:`HTMLPlotting` and :code:`HTMLElementPlotting`.

Data send to plotting classes are complete, pre-computed and ready to display.