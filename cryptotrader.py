# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

import argparse
import datetime as dt
import os
import time
from multiprocessing import Process

import pandas as pd
from dateutil.relativedelta import relativedelta

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


def get_date_range(number_of_days:int):
    now = dt.datetime.now()
    dt_end = now.strftime("%Y%m%d")
    dt_start = (now - relativedelta(days=number_of_days)).strftime("%Y%m%d")
    #return f'start={dt_start}&end={dt_end}'
    return dt_start, dt_end


def control():

    # calcular día de hoy y de ayer
    date = dt.datetime.now().date()
    last_date = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S') - dt.timedelta(days=1)
    time_last_ticker = dt.datetime.strptime(last_date.strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
    time_now_ticker = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
    # filename = '{}_{}.csv'.format("coinmarketcap", date)

    # recuperar el precio y volumen de las últimas cryptos creadas
    # repetir el proceso cada 5 minutos
    while True:
        # if True: #
        if dt.datetime.now().minute % 5 == 0 and dt.datetime.now().second <= 1:
            html = coinmarketcap.requestList("https://coinmarketcap.com/es/new/")
            tokens = coinmarketcap.parseList(html)
            # recuperar los precios y volumenes dado el nombre de la crypto
            # empezar a analizar los valores
            for token in tokens:
                df3 = pd.read_csv(token+".csv", index_col=0)

                # para cada crypto, recuperar el precio y volumen relativos
                for i in range(0, len(df3.index)-1):

                    volumen1 = df3['volume'].iloc[i].astype(float)
                    volumen2 = df3['volume'].iloc[i+1].astype(float)
                    cambio_relativo_volume = 1 / (volumen1 / volumen2)
                    price1 = df3.iloc[i]['price'].astype(float)
                    price2 = df3.iloc[i+1]['price'].astype(float)
                    cambio_relativo_price = 1 / (price1 / price2)
                    data = pd.json_normalize({'time': time_now_ticker, 'name': token, 'price_relative': cambio_relativo_price, 'volume_relative': cambio_relativo_volume})
                    if os.path.isfile(token+"_changes.csv"):
                        df4 = pd.read_csv(token+"_changes.csv", index_col=0)
                        df4 = df4.append(data, ignore_index=True)
                    else:
                        df4 = pd.DataFrame(data)
                    df4.to_csv(token+"_changes.csv")

                # recuperamos el archivo con los precios y volumes relativos (average)
                if os.path.isfile(token + "_changes.csv"):
                    df5 = pd.read_csv(token+"_changes.csv", index_col=0)
                    data = pd.json_normalize({'time': time_now_ticker, 'name': token, 'price_relative_average': df5['price_relative'].mean(), 'volume_relative_average': df5['volume_relative'].mean()})
                    df5 = pd.DataFrame(data)
                    df5.to_csv(token+"_relative.csv")

                    # # si el precio está aumentando y el volumen también
                    # # si desde la primera cifra hasta ahora ha incrementado el volumen en x%
                    # last_volume = df3["volume"].iloc[-1]
                    # ini_volume = df3["volume"].iloc[0]
                    # last_price = df3["price"].iloc[-1]
                    # ini_price = df3["price"].iloc[0]
                    # if (last_volume > ini_volume) and (last_price > ini_price) and last_volume > 200000:
                    #     # comprar
                    #     pass


        else:
            time.sleep(1)


def buyORsell():
    pass


if __name__ == '__main__':

    p = Process(target=control)
    s = Process(target=buyORsell)
    p.start()
    s.start()

    p.join()
    s.join()
    print()
