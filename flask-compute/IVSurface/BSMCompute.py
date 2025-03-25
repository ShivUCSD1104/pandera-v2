# flask-compute/IVSurface/BSMCompute.py
import numpy as np
from math import log, sqrt, exp
from scipy.stats import norm
from .DataSourcing import get_risk_free_rate, get_option_data

def black_scholes_call(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return max(0.0, S - K)
    d1 = (log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    return S * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)

def black_scholes_put(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return max(0.0, K - S)
    d1 = (log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    return K * exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def implied_vol_call(market_price, S, K, T, r=0.0, tol=0.001, max_iter=100):
    intrinsic_value = max(0.0, S - K * exp(-r * T))
    if market_price < intrinsic_value:
        return np.nan
    sigma = 0.3
    for _ in range(max_iter):
        price_guess = black_scholes_call(S, K, T, r, sigma)
        diff = price_guess - market_price
        if abs(diff) < tol:
            return sigma
        d1 = (log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
        vega = S * norm.pdf(d1) * sqrt(T)
        if vega < 1e-8:
            break
        sigma -= diff / vega
        if sigma < 1e-8:
            sigma = 1e-8
    return sigma

def implied_vol_put(market_price, S, K, T, r=0.0, tol=0.01, max_iter=100):
    intrinsic_value = max(0.0, K * exp(-r * T) - S)
    if market_price < intrinsic_value:
        return np.nan
    sigma = 0.3
    for _ in range(max_iter):
        price_guess = black_scholes_put(S, K, T, r, sigma)
        diff = price_guess - market_price
        if abs(diff) < tol:
            return sigma
        d1 = (log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
        vega = S * norm.pdf(d1) * sqrt(T)
        if vega < 1e-8:
            break
        sigma -= diff / vega
        if sigma < 1e-8:
            sigma = 1e-8
    return sigma

def compute_implied_vols(ticker_str, contract_type="calls", start_date=None, end_date=None):
    r = get_risk_free_rate()
    data_list, S = get_option_data(ticker_str, contract_type=contract_type, start_date=start_date, end_date=end_date)
    ivs, mny, ttes = [], [], []
    for options_df, T in data_list:
        for _, row in options_df.iterrows():
            K = row["strike"]
            bid = row.get("bid", np.nan)
            ask = row.get("ask", np.nan)
            market_price = 0.5 * (bid + ask) if not (np.isnan(bid) or np.isnan(ask)) else row.get("lastPrice", np.nan)
            if np.isnan(market_price):
                continue
            if contract_type == "calls":
                iv = implied_vol_call(market_price, S, K, T, r=r)
                money = S / K
            else:
                iv = implied_vol_put(market_price, S, K, T, r=r)
                money = K / S
            if np.isnan(iv):
                continue
            ivs.append(iv)
            mny.append(money)
            ttes.append(T)
    return ivs, mny, ttes
