import plotly.graph_objects as go
import numpy as np
import pandas as pd
from .data import get_data

def generate_order_flow_html(ticker, start_date=None, end_date=None):
    """
    Generates a 3D surface Plotly JSON for order flow data.
    The logic and data gathering remain unchanged; we simply
    wrap them in a function that returns the figure's JSON.
    """
    
    TICKER = ticker

    # Gather data
    apx, bpx, avc, bvc, times = get_data(TICKER, start_date=start_date, end_date=end_date)
    # Prepare figure exactly as before
    op = 0.8
    scaler = 8
    inds = np.arange(500, len(apx), scaler)

    fig = go.Figure(
        data=[
            go.Surface(
                x=apx[inds],
                y=np.arange(len(apx[inds])),
                z=avc[inds],
                colorscale='OrRd',
                opacity=op
            )
        ]
    )

    fig.add_surface(
        x=bpx[inds],
        y=np.arange(len(bpx[inds])),
        z=bvc[inds],
        colorscale='BuGn',
        opacity=op
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(
                nticks=4, 
                range=[min(apx[inds].min(), bpx[inds].min()), 
                       max(apx[inds].max(), bpx[inds].max())],
            ),
            yaxis=dict(
                nticks=4,
                range=[0, len(apx[inds])]
            ),
            zaxis=dict(
                nticks=4,
                range=[0, max(avc[inds].max(), bvc[inds].max())]
            ),
        ),
        margin=dict(l=0, r=0, b=0, t=0),
    )

    fig.update_layout(
        scene=dict(
            xaxis_title="Price",
            yaxis_title="Time",
            zaxis_title="CumulativeVolume"
        ),
        title = f"Order Flow of {ticker}"
    )

    # Return the Plotly figure as JSON (instead of showing it)
    return fig.to_json()
