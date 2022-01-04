# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

import argparse
import datetime as dt
import time

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



if __name__ == '__main__':

    # calcular día de hoy y de ayer
    date = dt.datetime.now().date()
    last_date = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S') - dt.timedelta(days=1)
    time_last_ticker = dt.datetime.strptime(last_date.strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
    time_now_ticker = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
    # filename = '{}_{}.csv'.format("coinmarketcap", date)

    # recuperar el precio y volumen de las últimas cryptos creadas
    # repetir el proceso cada 5 minutos
    while(True):
        if dt.datetime.now().minute % 5 == 0 and dt.datetime.now().second <= 1:
            html = coinmarketcap.requestList("https://coinmarketcap.com/es/new/")
            tokens = coinmarketcap.parseList(html)
            # recuperar los precios y volumenes dado el nombre de la crypto
            # empezar a analizar los valores
            for token in tokens:
                df = pd.read_csv(token)


        else:
            time.sleep(1)

    print()
