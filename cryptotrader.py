# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

import argparse
import datetime as dt
import decimal
import json
import os.path

import backtrader.feeds as btfeed
import pandas as pd
import requests


def parse_args():
    parser = argparse.ArgumentParser(description='CCXT Market')

    parser.add_argument('-s', '--symbol',
                        type=str,
                        required=True,
                        help='The Symbol of the Instrument/Currency Pair To Download')

    parser.add_argument('-a', '--apikey',
                        type=str,
                        required=False,
                        default='',
                        help='The exchange api key')

    return parser.parse_args()


def get_binance_bars(symbol_data, interval, starttime, endtime):
    url = "https://api.binance.com/api/v3/klines"

    starttime = str(int(starttime.timestamp() * 1000))
    endtime = str(int(endtime.timestamp() * 1000))
    limit = '1000'

    req_params = {"symbol": symbol_data, 'interval': interval, 'startTime': starttime, 'endTime': endtime,
                  'limit': limit}

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

    df_data['adj_close'] = df_data['close']

    df_data.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in df_data.datetime]

    return df_data


def round_down(value, decimals):
    with decimal.localcontext() as ctx:
        d = decimal.Decimal(value)
        ctx.rounding = decimal.ROUND_FLOOR
        return round(d, decimals)



def antes():

    # Pasando argumento
    # -s CAKE/BUSD -hora "02/01/2021 00:00:00" -cash 70.0 -t 4h -cycle 100
    args = parse_args()
    horadecomienzo = str(args.horadecomienzo)
    symbol = str(args.symbol)
    cash = float(args.cash)
    timeframe = str(args.timeframe)
    cycle = int(args.cycle)
    # horadecomienzo = str("02/01/2021 00:00:00")
    # symbol = str("CAKE/BUSD")
    # cash = float(70.0)
    # timeframe = str("4h")
    # cycle = 100

    exchange = str("binance")
    horadecomienzo = horadecomienzo.replace("/", "-")
    simbolos = symbol.split(sep='/')
    first_symbol = simbolos[0]
    second_symbol = simbolos[1]
    symbol_out = symbol.replace("/", "")
    filename = '{}-{}.csv'.format(symbol_out, timeframe)

    # Tiempo
    # last_date = dt.datetime(2021, 1, 10, 0, 0, 0)
    last_date = dt.datetime.strptime(horadecomienzo, '%d-%m-%Y %H:%M:%S') - dt.timedelta(days=1)
    last_datetime_ticker = dt.datetime.strptime(last_date.strftime('%d-%m-%Y %H:%M:%S'),
                                                '%d-%m-%Y %H:%M:%S')  # (2021, 1, 13)
    last_datetime = dt.datetime.strptime(horadecomienzo, '%d-%m-%Y %H:%M:%S')
    last_datetime_format = last_datetime.strftime('%d-%m-%Y %H:%M:%S')
    time_actual_ticker = dt.datetime.now()  # dt.datetime(2021, 7, 23)
    time_actual = dt.datetime.now().date()  # dt.datetime(2021, 7, 23)

    # intervalos = ['1d', '12h', '3h', '2h', '1h', '30m', '15m', '5m', '3m', '1m']
    resultados = []
    resultadosOpt = []
    i = timeframe
    # for i in intervalos:

    # Recuperar los valores de la gráfica desde binance y guardarlos en el csv
    if not os.path.isfile(filename):
        df_list = []
        while True:
            new_df = get_binance_bars(symbol_out, i, last_datetime_ticker, time_actual_ticker)  # timeframe

            if new_df is None:
                break
            df_list.append(new_df)
            last_datetime_ticker = max(new_df.index) + dt.timedelta(0, 1)
        df = pd.concat(df_list)
        df.columns
        # data = bt.feeds.PandasData(dataname=df)
        df.to_csv(filename)
        df = pd.read_csv(filename, sep=',', header=0,
                         names=['time', 'datetime', 'open', 'high', 'low', 'close', 'volume', 'adj_close'],
                         low_memory=False)
        df.to_csv(filename)

    # time.sleep(5)
    print('Intervalo: {}'.format(i))
    # print('Intervalo: {}'.format(timeframe))

    # timeframe y compresión
    # compression_actual, timeframe_actual = timeFrame(i)  # (timeframe)

    # Cargar csv
    data = btfeed.GenericCSVData(
        dataname=filename,
        fromdate=last_datetime_ticker,
        todate=time_actual,
        nullvalue=0.0,
        dtformat='%Y-%m-%d %H:%M:%S',
        datetime=1,
        open=3,
        high=4,
        low=5,
        close=6,
        volume=7,
        adj_close=8,
        openinterest=-1,
        # timeframe=timeframe_actual,
        # compression=compression_actual,
    )
    datos = data

    # print('precio actual: {}'.format(precioactual))
    ######

    # # optuna
    # study = optuna.create_study(direction="maximize")
    # study.optimize(opt_objective, n_trials=cycle)

    # print(study.best_params)
    # parametros_optimos = study.best_params
    # trial = study.best_trial
    # print('Saldo máximo: {}'.format(trial.value))
    # print(parametros_optimos)
    print()



if __name__ == '__main__':




    print()


