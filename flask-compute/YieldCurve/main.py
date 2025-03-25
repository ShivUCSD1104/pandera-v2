import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .data import get_yield_data

def generate_yield_curve_html(issuer, start_date, end_date):
    x, y, z = get_yield_data(start_date, end_date)
    print(f"Yield data dimensions - X: {len(x)}, Y: {len(y)}, Z: {z.shape}")
    print(x, y, z)
    fig = go.Figure(data=[
        go.Surface(
            z=z,
            x=x, 
            y=y,
            colorscale="Viridis",
            colorbar=dict(title="Yield (%)")
        )
    ])
    fig.update_layout(
        title="3D Interest Rate Term Structure",
        scene=dict(
            xaxis=dict(title="Maturity (Months)"),
            yaxis=dict(title="Date"),
            zaxis=dict(title="Yield (%)")
        ),
        margin=dict(l=0, r=0, b=0, t=50)
    )
    return fig.to_json()

if __name__ == "__main__":
    import datetime
    fig_json = generate_yield_curve_html("US Treasury", "2024-01-01", "2024-12-31")
    print(fig_json)
