import plotly.graph_objects as go

def print_node(node=''):
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=["nuclear", "eolien", "load", "b", "c"],
        ),
        link=dict(
            source=[0, 1, 0, 0],  # indices correspond to labels, eg A1, A2, A2, B1, ...
            target=[2, 2, 3, 4],
            value=[3, 12, 2, 2]
        ))])

    fig.update_layout(title_text="Node A", font_size=10)
    fig.show()


def print_balance(res=None):
    edge_trace = go.Scatter(
        x=[0, 1, None, 0, 1, None], y=[0, 0, None, 0, 1, None],
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_trace = go.Scatter(
        x=[0, 1, 1], y=[0, 0, 1],
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='Picnic',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node balance',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    node_trace.marker.color = [20, -10, -10]
    node_trace.text = ['node a export 20', 'node b import 10', 'node c import 10']

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='Network global import / export',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    fig.show()