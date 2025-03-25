import yfinance as yf
from datetime import datetime

# Get the risk-free rate using the 3-month T-bill
def get_risk_free_rate():
    """
    Fetches the 3-month T-bill (annualized) yield from yfinance
    using the '^IRX' ticker. You can switch to a different T-Bill
    if you prefer e.g. '^IRX' -> 3-month, '^FVX' -> 5-year, etc.
    
    Returns the yield in decimal form (e.g. 0.045 => 4.5%).
    """
    tbill = yf.Ticker("^IRX")  # 13-week T-bill index on Yahoo
    hist = tbill.history(period="1d")
    if hist.empty:
        # Fallback if no data
        return 0.042
    
    # ^IRX is often quoted in basis points or %; typically it's in hundredths
    last_close = hist["Close"].iloc[-1]
    # Convert to decimal form (e.g. 4.5 => 0.045)
    r_decimal = last_close / 100.0
    return r_decimal


def get_option_data(ticker_str, contract_type="calls", start_date=None, end_date=None):
    """
    Retrieves up to 12 option chain DataFrames (calls or puts) for a given ticker's expiration dates
    that fall within the provided start and end date. If no dates are provided, the earliest 12 expirations are used.
    
    contract_type: 'calls' or 'puts'
    Returns:
      - A list of tuples: [(options_df, T), (options_df, T), ...] for the selected expirations
      - Underlying spot price S
    """
    ticker = yf.Ticker(ticker_str)
    
    # Get all available expiration dates (as strings, typically in "YYYY-MM-DD" format)
    expirations = ticker.options
    # print(expirations, 'expirations')
    if not expirations:
        raise ValueError(f"No option data available for ticker {ticker_str}.")

    # If a start and end date are provided, filter the expiration dates accordingly.
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")
        
        filtered_expirations = [
            expiry for expiry in expirations
            if start_dt <= datetime.strptime(expiry, "%Y-%m-%d") <= end_dt
        ]
        selected_expirations = filtered_expirations[:12]  # Get up to 12 valid expirations within the range
    else:
        selected_expirations = expirations[:12]

    # Get the underlying stock price.
    # If a date range is provided, attempt to get the data from that range; otherwise, use the most recent day.
    stock_data = ticker.history(period="1d")
    # print(stock_data, 'stock data')

    if stock_data.empty:
        raise ValueError("Could not retrieve stock price history.")
    S = stock_data["Close"].iloc[-1]
    # print(selected_expirations, 'selected expirations')
    # Build a list of (DataFrame, T) for each of the selected expirations
    data_list = []
    now = datetime.now()
    
    for expiry_date in selected_expirations:
        chain = ticker.option_chain(expiry_date)
        if contract_type == "calls":
            options_df = chain.calls
        elif contract_type == "puts":
            options_df = chain.puts
        else:
            raise ValueError("contract_type must be either 'calls' or 'puts'.")
        
        expiry_dt = datetime.strptime(expiry_date, "%Y-%m-%d")
        T = (expiry_dt - now).days / 365.0
        
        # Only include if the time-to-expiry is positive
        if T > 0:
            data_list.append((options_df, T))
    
    return data_list, S
