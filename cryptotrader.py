# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

import argparse
import datetime as dt
import decimal
import json
import os.path
from time import sleep

import backtrader.feeds as btfeed
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from scrape import scrapeTokenList, scrapeMarketCap

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


def coinNames():
    """Gets ID's of all coins on cmc"""
    names = []
    response = requests.get("https://api.coinmarketcap.com/v1/ticker/?limit=0")
    respJSON = json.loads(response.text)
    for i in respJSON:
        names.append(i['id'])
    return names


def gather():
    historicaldata = []
    counter = 1

    startdate, enddate = get_date_range(2)
    names = 'BTC'
    coin = names[0]
    # for coin in names:
    sleep(10)
    r = requests.get("https://coinmarketcap.com/currencies/{0}/historical-data/?start={1}&end={2}".format(coin, startdate, enddate))
    data = r.text
    soup = BeautifulSoup(data, "html.parser")
    table = soup.find('table', attrs={ "class" : "table"})

    #Add table header to list
    if len(historicaldata) == 0:
        headers = [header.text for header in table.find_all('th')]
        headers.insert(0, "Coin")

    for row in table.find_all('tr'):
        currentrow = [val.text for val in row.find_all('td')]
        if(len(currentrow) != 0):
            currentrow.insert(0, coin)
        historicaldata.append(currentrow)

    print("Coin Counter -> " + str(counter), end='\r')
    counter += 1

    return headers, historicaldata

#
# def _gather():
#     """ Scrape data off cmc"""
#     #
#     # if(len(sys.argv) == 3):
#     #     names = CoinNames()
#     # else:
#     #     names = [sys.argv[3]]
#
#     headers, historicaldata = gather()
#
#     Save(headers, historicaldata)
#
# def Save(headers, rows):
#
#     if(len(sys.argv) == 3):
#         FILE_NAME = "HistoricalCoinData.csv"
#     else:
#         FILE_NAME = sys.argv[3] + ".csv"
#
#     with open(FILE_NAME, 'w') as f:
#         writer = csv.writer(f)
#         writer.writerow(headers)
#         writer.writerows(row for row in rows if row)
#     print("Finished!")

def get_date_range(number_of_days:int):
    now = dt.datetime.now()
    dt_end = now.strftime("%Y%m%d")
    dt_start = (now - relativedelta(days=number_of_days)).strftime("%Y%m%d")
    #return f'start={dt_start}&end={dt_end}'
    return dt_start, dt_end



def get_coinmarketcap_latest():
    start_date, end_date = get_date_range(2)
    url = f'https://coinmarketcap.com/currencies/bitcoin/historical-data/?start={start_date}&end={end_date}'
    print(url)
    # response = requests.get(url.format(start_date, end_date))

    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')

    name = soup.find_all('a', class_='cmc-link')
    print(name)

    # print(soup.prettify())

    data = []
    table = soup.find('table', id='')
    for row in table.find_all('tr'):
        cells = row.findChildren('td')
        values = []
        for cell in cells:
            value = cell.string
            values.append(value)
        try:
            Date = values[0]
            Open = values[1]
            High = values[2]
            Low = values[3]
            Close = values[4]
            Volume = values[5]
            MarketCap = values[6]
        except IndexError:
            continue
        data.append([Date, Open, High, Low, Close, Volume, MarketCap])
    # Print data
    for item in data:
        print(item)
    return data



# def float_helper(string):
#     try:
#         return float(string)
#     except ValueError:
#         return None

# def coinmarketcap_get_btc()-> pd.DataFrame: #(start_date: str, end_date: str)
#     # Build the url
#     start_date, end_date = get_date_range(2)
#     url = f'https://coinmarketcap.com/currencies/bitcoin/historical-data/?start={start_date}&end={end_date}'
#     # Make the request and parse the tree
#     response = requests.get(url, timeout=5)
#     tree = lxml.html.fromstring(response.text)
#     # Extract table and raw data
#     table = tree.find_class('table-responsive')[0]
#     raw_data = [_.text_content() for _ in table.find_class('text-right')]
#     # Process the data
#     col_names = ['Date'] + raw_data[:6]
#     row_list = []
#     for x in raw_data[6:]:
#         _, date, _open, _high, _low, _close, _vol, _m_cap, _ = x.replace(',', '').split('\n')
#         row_list.append([date, float_helper(_open), float_helper(_high), float_helper(_low),
#                          float_helper(_close), float_helper(_vol), float_helper(_m_cap)])
#     return pd.DataFrame(data=row_list, columns=col_names)


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

    # calcular día de hoy y de ayer
    date = dt.datetime.now().date()
    timeframe = dt.datetime.strftime(date, '%d-%m-%Y')
    print(timeframe)
    timeframe_before_1_day = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days=1), '%d-%m-%Y %H:%M:%S')
    filename = '{}_{}.csv'.format("coinmarketcap", timeframe)

    # # recuperar las últimas cryptos creadas
    tokens = scrapeTokenList("https://coinmarketcap.com/es/new/")
    # print(df)
    for token in tokens:
        min_market_cap = 0.0
        scrapeMarketCap("https://coinmarketcap.com/es/currencies" + token['slug'], token['name'], 'token', min_market_cap)

    # if (scrapeMarketCap("https://coinmarketcap.com/es/currencies" + token['slug'], token['name'], 'token', min_market_cap):
    #     logging.info("Minimum market cap reached. Stopped scraping tokens.")
    #     break
    # df = get_coinmarketcap_latest()
    #
    # # guardar datos en csv
    # df.to_csv(filename)
    # print(df)

    # get_coinmarketcap_latest()
    # df = get_coinmarketcap_latest()
    # print(df)

    print()

    # df = pd.read_csv(filename, sep=',', header=0,
    #                  #names=['price', 'volume_24h', 'volume_change_24h', 'percent_change_1h', 'percent_change_24h', 'percent_change_7d', 'percent_change_30d', 'percent_change_60d', 'percent_change_90d', 'market_cap', 'market_cap_dominance', 'fully_diluted_market_cap', 'last_updated'],
    #                  low_memory=False)
