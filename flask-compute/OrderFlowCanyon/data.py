import databento as db
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from .utils import create_orderbook
from dotenv import load_dotenv
import os

def get_data(ticker='TSLA', start_date=None, end_date=None):
  load_dotenv()
  DATABENTO_KEY = os.getenv("API_KEY")
  client = db.Historical(DATABENTO_KEY)

  if start_date is None:
    start_date = datetime.now() - timedelta(days=3)
  if end_date is None:
    end_date = datetime.now() - timedelta(days=1)
  symbols = [ticker]

  df = client.timeseries.get_range(
      dataset="XNAS.ITCH",
      schema="mbp-10",
      symbols=symbols,
      start=start_date,
      end=end_date,
      limit=10_000,
  ).to_df()

  apx, bpx, avc, bvc, times = create_orderbook(df)
  return apx, bpx, avc, bvc, times




