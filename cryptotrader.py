# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
import argparse
import datetime as dt
import decimal
import json
import pandas as pd
from dateutil.relativedelta import relativedelta
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import coinmarketcap


api_key = 'c78fb3e5-004d-4b44-8613-0f55a60e99c7'

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


def get_coinmarketcap_latest_api():

    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {
        'start': '1',
        'limit': '10',
        'price_max': '1',
        'cryptocurrency_type': 'tokens',
        'convert': 'EUR',
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        #

        df_data_id = pd.DataFrame(data['data'], columns=['id', 'symbol', 'date_added'])
        df_data_quote = pd.DataFrame(data['data'], columns=['quote'])
        df_quote_json = pd.Series(df_data_quote['quote']).apply(lambda x: x['EUR'])
        df_data_quote_eur = pd.read_json(df_quote_json.to_json(), orient='index')
        df = pd.concat([df_data_id, df_data_quote_eur], axis=1)
        df = pd.DataFrame(df, columns=['id', 'symbol', 'date_added', 'price', 'volume_24h', 'volume_change_24h',
                   'percent_change_1h', 'percent_change_24h', 'percent_change_7d',
                   'percent_change_30d', 'percent_change_60d',
                   'percent_change_90d', 'market_cap', 'market_cap_dominance',
                   'fully_diluted_market_cap', 'last_updated'])

        # print(df)
        return df
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)


def round_down(value, decimals):
    with decimal.localcontext() as ctx:
        d = decimal.Decimal(value)
        ctx.rounding = decimal.ROUND_FLOOR
        return round(d, decimals)


if __name__ == '__main__':

    # calcular día de hoy y de ayer
    date = dt.datetime.now().date()
    last_date = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S') - dt.timedelta(days=1)
    time_last_ticker = dt.datetime.strptime(last_date.strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
    time_now_ticker = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
    filename = '{}_{}.csv'.format("coinmarketcap", date)

    # recuperar las últimas cryptos creadas
    html = coinmarketcap.requestList("https://coinmarketcap.com/es/new/")
    tokens = coinmarketcap.parseList(html)
    df = pd.DataFrame(tokens)
    df.to_csv(filename)
    print(df)

    print()
