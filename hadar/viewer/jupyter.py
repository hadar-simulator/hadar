import plotly.graph_objects as go

from hadar.aggregator.result import *


def plot_flow(agg: ResultAggregator, node: str, t: int):
    prod = agg.agg_prod(NodeIndex(node), TimeIndex(t), TypeIndex())
    print(prod)
    im = agg.agg_border(DestIndex(node), TimeIndex(t), SrcIndex())
    print(im)
    cons = agg.agg_cons(NodeIndex(node), TimeIndex(t), TypeIndex())
    print(cons)
    ex = agg.agg_border(SrcIndex(node), TimeIndex(t), DestIndex())
    print(ex)
