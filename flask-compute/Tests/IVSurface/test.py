import yfinance as yf
import numpy as np
from datetime import datetime
from math import log, sqrt, exp
from scipy.stats import norm

def black_scholes_call(S, K, T, r, sigma):
    """
    Computes the Black-Scholes price of a European call option.
    
    S: current stock price
    K: strike price
    T: time to expiration (years)
    r: risk-free interest rate (annual)
    sigma: volatility of the underlying (annual)
    """
    if T <= 0 or sigma <= 0:
        # Very rough edge-case handling:
        return max(0.0, S - K)
    
    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    
    return (S * norm.cdf(d1)) - (K * exp(-r * T) * norm.cdf(d2))

def implied_vol_call(market_price, S, K, T, r=0.0, tol=1e-6, max_iter=100):
    """
    Computes implied volatility via Newton-Raphson for a European call option.
    
    market_price: observed market price of the option
    S: current stock price
    K: strike price
    T: time to expiration (years)
    r: risk-free interest rate
    tol: stopping tolerance
    max_iter: maximum iterations for Newton-Raphson
    """
    # Check for an intrinsic value floor:
    intrinsic_value = max(0.0, S - K * exp(-r * T))
    if market_price < intrinsic_value:
        return np.nan  # Below intrinsic value => no valid implied vol
    
    # Initial guess (30% volatility)
    sigma = 0.30
    
    for _ in range(max_iter):
        # Current guess for the option price
        price_guess = black_scholes_call(S, K, T, r, sigma)
        diff = price_guess - market_price
        
        if abs(diff) < tol:
            return sigma
        
        # Vega: derivative of call price wrt volatility
        d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
        vega = S * norm.pdf(d1) * sqrt(T)
        
        if vega < 1e-8:  # Avoid division by very small vega
            break
        
        # Newton-Raphson update
        sigma -= diff / vega
        
        # Keep sigma in a reasonable range
        if sigma < 1e-8:
            sigma = 1e-8
    
    # If not converged, return the last iteration's sigma
    return sigma

def get_calls_data(ticker_str):
    """
    Retrieves the first-listed calls from yfinance for a given ticker symbol.
    Returns:
      - DataFrame of calls (option chain)
      - Underlying spot price S
      - Time to expiration T (in years)
    """
    ticker = yf.Ticker(ticker_str)
    expirations = ticker.options
    if not expirations:
        raise ValueError(f"No option data available for ticker {ticker_str}.")
    
    first_expiry = expirations[0]
    calls = ticker.option_chain(first_expiry).calls
    
    # Get current stock price (last close)
    stock_data = ticker.history(period="1d")
    if stock_data.empty:
        raise ValueError(f"Could not retrieve stock price for {ticker_str}.")
    S = stock_data["Close"].iloc[-1]
    
    # Compute time to expiration
    expiry_dt = datetime.strptime(first_expiry, "%Y-%m-%d")
    now = datetime.now()
    T = (expiry_dt - now).days / 365.0
    if T <= 0:
        raise ValueError("The nearest listed option appears to be expired or expiring today.")
    
    return calls, S, T

def compute_implied_vols(ticker_str, r=0.0):
    """
    High-level function that:
     1. Fetches the calls DataFrame for a given ticker
     2. Iterates over each call option, computing:
        - implied volatility
        - moneyness (S/K)
        - time to expiration (T) for that contract
     3. Returns three arrays (numpy lists):
        - implied_vols
        - moneyness_array
        - time_to_expiry_array
    """
    calls, S, T = get_calls_data(ticker_str)
    
    implied_vols = []
    moneyness_array = []
    time_to_expiry_array = []
    
    for _, row in calls.iterrows():
        K = row["strike"]
        bid = row.get("bid", np.nan)
        ask = row.get("ask", np.nan)
        
        # Prefer mid of bid/ask if they exist, otherwise use lastPrice
        if not np.isnan(bid) and not np.isnan(ask):
            option_price = 0.5 * (bid + ask)
        else:
            option_price = row.get("lastPrice", np.nan)
        
        if np.isnan(option_price):
            continue  # skip if we can't determine a price
        
        # Implied Vol
        iv = implied_vol_call(option_price, S, K, T, r=r)
        
        # Moneyness (S/K)
        money = S / K
        
        # Append to arrays
        implied_vols.append(iv)
        moneyness_array.append(money)
        time_to_expiry_array.append(T)
    
    return implied_vols, moneyness_array, time_to_expiry_array

# Example usage:
if __name__ == "__main__":
    ticker_symbol = "AAPL"  # Choose any ticker you like
    ivs, mny, ttes = compute_implied_vols(ticker_symbol)
    
    print("Implied Volatilities:", ivs)
    print("Moneyness (S/K):", mny)
    print("Time to Expiration (years):", ttes)
