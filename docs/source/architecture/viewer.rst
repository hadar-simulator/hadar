Viewer
======

Even with the highest level analyzer features. Data remains simple matrix or tables. Viewer is the end of Hadar framework, it will create amazing plot to bring most valuable data for humain analysis.

Viewer use Analyzer API to build plots. It like an extract layer to convert numeric result to visual result.

There are many viewers, all inherent from :code:`ABCPlotting` abstract class. Available plots are identical between viewers, only technologies used to build these plots change. Today, we have one type of plotting :code:`HTMLPlotting` which is coded upon plotly library to build html interactive plots.
