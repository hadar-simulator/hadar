import plotly.graph_objects as go
import ipywidgets as widgets
from IPython.display import display, clear_output

from hadar.aggregator.result import *


class Plotting:
    def __init__(self, agg, unit_quantity: str = '', time_start=None, time_end=None):
        self.agg = agg
        self.unit = '(%s)' % unit_quantity if unit_quantity != '' else ''
        time = [time_start is None, time_end is None]
        if time == [True, False] or time == [False, True]:
            raise ValueError('You have to give both time_start and time_end')
        elif time == [False, False]:
            self.time_index = pd.date_range(start=time_start, end=time_end, periods=self.agg.study.horizon)
        else:
            self.time_index = np.arange(self.agg.study.horizon)

    def dropmenu(self, plot, items):
        menu = widgets.Dropdown(options=items, value=items[0],
                                description='Node:', disabled=False)
        output = widgets.Output()

        def _plot(select):
            with output:
                clear_output()
                fig = plot(select)
                fig.show()

        def _on_event(event):
            if event['name'] == 'value' and event['type'] == 'change':
                _plot(event['new'])

        menu.observe(_on_event)
        display(menu, output)
        _plot(items[0])

    def time_stack(self, node: str = None):
        if node is not None:
            return self.time_stack_fig(node).show()
        else:
            nodes = list(self.agg.result.nodes.keys())
            self.dropmenu(self.time_stack_fig, nodes)

    def time_stack_fig(self, node: str):
        fig = go.Figure()
        stack = np.zeros(self.agg.study.horizon)

        # stack production with area
        prod = self.agg.agg_prod(NodeIndex(node), TypeIndex(), TimeIndex()).sort_values('cost', ascending=True)
        for i, type in enumerate(prod.index.get_level_values('type').unique()):
            stack += prod.loc[type]['used'].values
            fig.add_trace(go.Scatter(x=self.time_index, y=stack, name=type, mode='markers',
                                     fill='tozeroy' if i == 0 else 'tonexty'))

        # add import on stack with area
        balance = self.agg.get_balance(node=node)
        im = -np.clip(balance, None, 0)
        if not (im == 0).all():
            stack += im
            fig.add_trace(go.Scatter(x=self.time_index, y=stack, name='import', mode='markers', fill='tonexty'))

        # Reset stack, plot consumptions
        stack = np.zeros_like(stack)
        cons = self.agg.agg_cons(NodeIndex(node), TypeIndex(), TimeIndex()).sort_values('cost', ascending=False)
        for i, type in enumerate(cons.index.get_level_values('type').unique()):
            stack += cons.loc[type]['given'].values
            fig.add_trace(go.Scatter(x=self.time_index, y=stack, name=type, line=dict(width=4, dash='dash')))

        # Add export in consumption stack
        exp = np.clip(balance, 0, None)
        if not (exp == 0).all():
            stack += exp
            fig.add_trace(go.Scatter(x=self.time_index, y=stack, name='export', line=dict(width=4, dash='dash')))

        fig.update_layout(title_text='Stack error for node %s' % node,
                          yaxis_title="Quantity %s" % self.unit, xaxis_title="time")
        return fig
