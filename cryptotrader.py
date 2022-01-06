# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

import argparse
import datetime as dt
import os
import time
from multiprocessing import Process

import optuna
import pandas as pd
from dateutil.relativedelta import relativedelta
import backtrader_optuna
import coinmarketcap


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


def get_date_range(number_of_days: int):
    now = dt.datetime.now()
    dt_end = now.strftime("%Y%m%d")
    dt_start = (now - relativedelta(days=number_of_days)).strftime("%Y%m%d")
    # return f'start={dt_start}&end={dt_end}'
    return dt_start, dt_end


all_tokens = []


def control():
    global all_tokens

    if not os.path.exists("csv"):
        os.makedirs("csv")

    # calcular día de hoy y de ayer
    date = dt.datetime.now().date()
    last_date = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                                     '%d-%m-%Y %H:%M:%S') - dt.timedelta(days=1)
    time_last_ticker = dt.datetime.strptime(last_date.strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
    time_now_ticker = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
    # filename = '{}_{}.csv'.format("coinmarketcap", date)

    # recuperar el precio y volumen de las últimas cryptos creadas
    # repetir el proceso cada 5 minutos
    while True:
        # if True: #
        if dt.datetime.now().minute % 5 == 0 and dt.datetime.now().second <= 1:
            time_now_ticker = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
            html = coinmarketcap.requestList("https://coinmarketcap.com/es/new/")
            tokens = coinmarketcap.parseList(html)
            all_tokens = tokens
            # recuperar los precios y volumenes dado el nombre de la crypto
            # empezar a analizar los valores
            for token in tokens:
                df3 = pd.read_csv("csv/" + token + ".csv", index_col=0)

                # para cada crypto, recuperar el precio y volumen relativos
                for i in range(0, len(df3.index) - 1):

                    volumen1 = df3['volume'].iloc[i].astype(float)
                    volumen2 = df3['volume'].iloc[i + 1].astype(float)
                    if volumen1 is 0 or volumen2 is 0:
                        break
                    cambio_relativo_volume = 1 / (volumen1 / volumen2)
                    price1 = df3.iloc[i]['price'].astype(float)
                    price2 = df3.iloc[i + 1]['price'].astype(float)
                    if price1 is 0 or price2 is 0:
                        break
                    cambio_relativo_price = 1 / (price1 / price2)
                    data = pd.json_normalize(
                        {'time': time_now_ticker, 'name': token, 'price_relative': cambio_relativo_price,
                         'volume_relative': cambio_relativo_volume})
                    if os.path.isfile("csv/" + token + "_changes.csv"):
                        df4 = pd.read_csv("csv/" + token + "_changes.csv", index_col=0)
                        df4 = df4.append(data, ignore_index=True)
                    else:
                        df4 = pd.DataFrame(data)
                    df4.to_csv("csv/" + token + "_changes.csv")

                # recuperamos el archivo con los precios y volumes relativos (average)
                if os.path.isfile("csv/" + token + "_changes.csv"):
                    df5 = pd.read_csv("csv/" + token + "_changes.csv", index_col=0)
                    data = pd.json_normalize(
                        {'time': time_now_ticker, 'name': token, 'price_relative_average': df5['price_relative'].mean(),
                         'volume_relative_average': df5['volume_relative'].mean()})
                    df5 = pd.DataFrame(data)
                    df5.to_csv("csv/" + token + "_relative.csv")
                    # average 1 hora
                    # if (df5.index >= 12):
                    #     data2 = pd.json_normalize({'time': time_now_ticker, 'name': token,
                    #                                'price_relative_average': df5['price_relative'].iloc[-12].mean(),
                    #                                'volume_relative_average': df5['volume_relative'].iloc[-12].mean()})
                    #     df8 = pd.DataFrame(data2)
                    #     df8.to_csv("csv/" + token + "_relative_1h.csv")
                    #
                    # # average 2 hora
                    # if (df5.index >= 24):
                    #     data3 = pd.json_normalize({'time': time_now_ticker, 'name': token,
                    #                                'price_relative_average': df5['price_relative'].iloc[-24].mean(),
                    #                                'volume_relative_average': df5['volume_relative'].iloc[-24].mean()})
                    #     df9 = pd.DataFrame(data3)
                    #     df9.to_csv("csv/" + token + "_relative_2h.csv")


        else:
            time.sleep(1)


def buyORsell():
    global all_tokens
    for token in all_tokens:
        if os.path.isfile("csv/" + token + "_changes.csv"):
            df9 = pd.read_csv("csv/" + token['name'] + "_changes.csv", index_col=0)
            if (df9.index >= 12):
                if df9['price_relative_average'].iloc[-12].mean() > 1.1 and df9['volume_relative_average'].iloc[-12].mean() > 1.1:
                    print("Buy " + token['name'] + " a " + df9['price'].iloc[-1] + " a las " + dt.datetime.now())



def optuna():
    time.sleep(300)
    global all_tokens
    for token in all_tokens:
        backtrader_optuna.optuna_search(token)


if __name__ == '__main__':
    p = Process(target=control)
    # s = Process(target=buyORsell)
    o = Process(target=optuna)
    p.start()
    # s.start()
    o.start()
    p.join()
    # s.join()
    o.join()
    print()
