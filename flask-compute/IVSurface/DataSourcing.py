from datetime import datetime
import pandas as pd
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from db import SessionLocal, OptionData, UnderlyingData, YieldData


def get_underlying_price(ticker):
    session = SessionLocal()
    record = session.query(UnderlyingData).filter(UnderlyingData.ticker == ticker).order_by(UnderlyingData.date.desc()).first()
    session.close()
    if record:
        return float(record.close)
    else:
        raise ValueError("No underlying price data available.")

def get_option_data(ticker, contract_type="calls", start_date=None, end_date=None):
    """
    Retrieve option data from the database.
    Returns a tuple: (list of (DataFrame, time-to-expiry), underlying price S)
    """
    session = SessionLocal()
    query = session.query(OptionData).filter(OptionData.ticker == ticker, OptionData.option_type == contract_type)
    if start_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        query = query.filter(OptionData.expiration_date >= start_date_obj)
    if end_date:
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        query = query.filter(OptionData.expiration_date <= end_date_obj)
    records = query.all()
    session.close()
    # Group records by expiration date
    data_dict = {}
    for rec in records:
        exp_date = rec.expiration_date
        data_dict.setdefault(exp_date, []).append({
            "strike": float(rec.strike),
            "bid": float(rec.bid),
            "ask": float(rec.ask),
            "lastPrice": float(rec.last_price)
        })
    data_list = []
    now = datetime.now()
    for exp_date, recs in data_dict.items():
        T = (exp_date - now.date()).days / 365.0
        if T <= 0:
            continue
        df = pd.DataFrame(recs)
        data_list.append((df, T))
    S = get_underlying_price(ticker)
    return data_list, S

def get_risk_free_rate():
    """
    Retrieve the risk-free rate from yield data (using 3-Month T-bill data)
    """
    return 0.042
