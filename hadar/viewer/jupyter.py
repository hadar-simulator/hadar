from typing import Dict, List

import matplotlib
import ipywidgets as widgets
from IPython.display import display, clear_output

from hadar.aggregator.result import *
from hadar.viewer.html import HTMLPlotting


class JupyterPlotting(HTMLPlotting):
    def __init__(self, agg, unit_quantity: str = '',
                 time_start=None, time_end=None,
                 cmap=matplotlib.cm.coolwarm,
                 node_coord: Dict[str, List[float]] = None,
                 map_element_size: int = 1):

        HTMLPlotting.__init__(self, agg, unit_quantity, time_start, time_end, cmap, node_coord, map_element_size)

    def dropmenu(self, plot, items):
        menu = widgets.Dropdown(options=items, value=items[0],
                                description='Node:', disabled=False)
        output = widgets.Output()

        def _plot(select):
            with output:
                clear_output()
                fig = plot(self, select)
                fig.show()

        def _on_event(event):
            if event['name'] == 'value' and event['type'] == 'change':
                _plot(event['new'])

        menu.observe(_on_event)
        display(menu, output)
        _plot(items[0])

    def stack(self, node: str = None):
        if node is not None:
            return HTMLPlotting.stack(self, node).show()
        else:
            nodes = list(self.agg.result.nodes.keys())
            self.dropmenu(HTMLPlotting.stack, nodes)
