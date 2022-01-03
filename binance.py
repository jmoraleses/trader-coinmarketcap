import json
import datetime as dt
import pandas as pd
import requests


def get_binance_bars(symbol_data, interval, starttime, endtime):
    url = "https://api.binance.com/api/v3/klines"

    starttime = str(int(starttime.timestamp() * 1000))
    endtime = str(int(endtime.timestamp() * 1000))
    limit = '64'

    req_params = {"symbol": symbol_data, 'interval': interval, 'startTime': starttime, 'endTime': endtime, 'limit': limit}

    print(json.loads(requests.get(url, params=req_params).text))
    df_data = pd.DataFrame(json.loads(requests.get(url, params=req_params).text))

    if len(df_data.index) == 0:
        return None

    df_data = df_data.iloc[:, 0:6]
    df_data.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']

    df_data.open = df_data.open.astype("float")
    df_data.high = df_data.high.astype("float")
    df_data.low = df_data.low.astype("float")
    df_data.close = df_data.close.astype("float")
    df_data.volume = df_data.volume.astype("float")

    df_data['adj_close'] = df_data['open']

    df_data.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in df_data.datetime]

    return df_data