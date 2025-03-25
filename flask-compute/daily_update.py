import os
import requests
from datetime import datetime
from db import SessionLocal, OptionData, UnderlyingData, YieldData

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

def fetch_stock_data(ticker):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}&outputsize=compact"
    response = requests.get(url)
    return response.json()

def update_underlying_data(ticker):
    data = fetch_stock_data(ticker)
    time_series = data.get("Time Series (Daily)", {})
    session = SessionLocal()
    try:
        for date_str, daily_data in time_series.items():
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            exists = session.query(UnderlyingData).filter(UnderlyingData.ticker == ticker, UnderlyingData.date == date_obj).first()
            if not exists:
                close_price = float(daily_data["4. close"])
                record = UnderlyingData(
                    ticker=ticker,
                    date=date_obj,
                    close=close_price,
                    fetch_date=datetime.utcnow().strftime("%Y-%m-%d")
                )
                session.add(record)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error updating underlying data for {ticker}: {e}")
    finally:
        session.close()

def fetch_option_data(ticker):
    url = f"https://www.alphavantage.co/query?function=HISTORICAL_OPTIONS&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    return response.json()

def update_option_data(ticker):
    data = fetch_option_data(ticker)
    session = SessionLocal()
    try:
        for option in data.get("data", []):
            expiration_str = option.get("expiration")
            exp_date = datetime.strptime(expiration_str, "%Y-%m-%d").date()
            
            option_type = option.get("type", "").lower()
            mapped_type = "calls" if option_type == "call" else "puts" if option_type == "put" else option_type

            strike = float(option.get("strike", 0))
            bid = float(option.get("bid", 0))
            ask = float(option.get("ask", 0))
            last_price = float(option.get("last", 0))
            
            exists = session.query(OptionData).filter(
                OptionData.ticker == ticker,
                OptionData.expiration_date == exp_date,
                OptionData.option_type == mapped_type,
                OptionData.strike == strike
            ).first()
            
            if not exists:
                record = OptionData(
                    ticker=ticker,
                    expiration_date=exp_date,
                    option_type=mapped_type,
                    strike=strike,
                    bid=bid,
                    ask=ask,
                    last_price=last_price,
                    fetch_date=datetime.utcnow().strftime("%Y-%m-%d")
                )
                session.add(record)
        
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error updating options data for {ticker}: {e}")
    finally:
        session.close()

def fetch_yield_data(ticker):
    url = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&sinterval=daily&maturity={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    return response.json()

def update_yield_data():
    yields_info = {
        "^IRX": "3month",
        "^FVX": "5year",
        "^TNX": "10year",
        "^TYX": "30year"
    }
    
    session = SessionLocal()
    try:
        for ticker, maturity in yields_info.items():
            data = fetch_yield_data(maturity)
            print(data)
            yield_list = data.get("data", [])
            
            for entry in yield_list:
                date_obj = datetime.strptime(entry["date"], "%Y-%m-%d").date()
                exists = session.query(YieldData).filter(
                    YieldData.ticker == ticker, 
                    YieldData.date == date_obj
                ).first()
                if not exists:
                    close_price = float(entry["value"])
                    record = YieldData(
                        label=maturity,
                        ticker=ticker,
                        date=date_obj,
                        close=close_price,
                        fetch_date=datetime.utcnow().strftime("%Y-%m-%d")
                    )
                    session.add(record)
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error updating yield data: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    tickers = ["AAPL", "GOOGL", "MSFT"]
    for ticker in tickers:
        update_underlying_data(ticker)
        update_option_data(ticker)
    update_yield_data()
    print("Daily update complete.")