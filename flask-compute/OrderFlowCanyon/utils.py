import pandas as pd
import numpy as np

def create_snapshot(df, ti):
  depth = 10
  ask_prices = []
  bid_prices = []

  ask_vols = []
  bid_vols = []

  for i in range(depth):
    bv = f'bid_sz_0{i}'
    av = f'ask_sz_0{i}'
    bp = f'bid_px_0{i}'
    ap = f'ask_px_0{i}'
    
    ask_vols.append(df.iloc[ti][av])
    bid_vols.append(df.iloc[ti][bv])
    bid_prices.append(df.iloc[ti][bp])
    ask_prices.append(df.iloc[ti][ap])

  #bid_vols = np.array(bid_vols) * -1
  return ask_vols, bid_vols, ask_prices, bid_prices

def create_orderbook(df):
  times = []
  ask_vols_t = []
  bid_vols_t = []
  ask_prices_t = []
  bid_prices_t = []
  for ti in range(0, len(df), 10):
    ask_vols, bid_vols, ask_prices, bid_prices = create_snapshot(df, ti)
    ask_vols_t.append(ask_vols)
    bid_vols_t.append(bid_vols)
    ask_prices_t.append(ask_prices)
    bid_prices_t.append(bid_prices)
    snapshot_time = df.iloc[ti]['ts_in_delta']
    times.append([snapshot_time] * 10)

  apx = np.array(ask_prices_t)
  bpx = np.array(bid_prices_t)
  avx = np.array(ask_vols_t)
  bvx = np.array(bid_vols_t)
  times = np.array(times)

  #avc = np.fliplr( np.cumsum( np.fliplr(avx), axis=1 ) )
  #bvc = np.fliplr( np.cumsum( np.fliplr(bvx), axis=1 ) )
  avc = np.cumsum( avx, axis=1 )
  bvc = np.cumsum( bvx, axis=1 )
  return apx, bpx, avc, bvc, times