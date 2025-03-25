import numpy as np
from scipy.interpolate import griddata
import plotly.graph_objs as go
from .BSMCompute import compute_implied_vols

def generate_iv_surface_html(ticker_symbol, start_date, end_date):
    print(f"Generating IV Surface for {ticker_symbol}")
    ivs_calls, mny_calls, ttes_calls = compute_implied_vols(ticker_symbol, "calls", start_date, end_date)
    ivs_puts, mny_puts, ttes_puts = compute_implied_vols(ticker_symbol, "puts", start_date, end_date)
    ivs = np.array(ivs_calls + ivs_puts)
    mny = np.array(mny_calls + mny_puts)
    ttes = np.array(ttes_calls + ttes_puts)

    if len(ivs) == 0:
        return f"<p>No option data found for {ticker_symbol} with the chosen parameters.</p>"

    mask = (mny >= -7) & (mny <= 7)
    ivs, mny, ttes = ivs[mask], mny[mask], ttes[mask]
    if len(ivs) == 0:
        return f"<p>After filtering, no data remains for {ticker_symbol}.</p>"

    grid_mny, grid_ttes = np.meshgrid(
        np.linspace(min(mny), max(mny), 50),
        np.linspace(min(ttes), max(ttes), 50)
    )
    grid_ivs = griddata((mny, ttes), ivs, (grid_mny, grid_ttes), method='cubic')

    surface = go.Surface(
        x=grid_mny,
        y=grid_ttes,
        z=grid_ivs,
        colorscale='Viridis'
    )
    layout = go.Layout(
        title=f"Implied Volatility Surface for {ticker_symbol}",
        scene=dict(
            xaxis_title="Moneyness (S/K or K/S)",
            yaxis_title="Time to Expiry (Years)",
            zaxis_title="Implied Volatility"
        )
    )
    fig = go.Figure(data=[surface], layout=layout)
    return fig.to_json()
