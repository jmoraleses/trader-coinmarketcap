""" Module for requesting data from coinmarketcap.org and parsing it. """
import json
import os
import random
import time
import datetime as dt
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests import Timeout, TooManyRedirects, Session

api_key = 'c78fb3e5-004d-4b44-8613-0f55a60e99c7'

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


def _request(target):
    """Private method for requesting an arbitrary query string."""
    r = requests.get(target)
    if r.status_code == requests.codes.ok:
        return r.text
    else:
        raise Exception("Could not process request. \
            Received status code {0}.".format(r.status_code))


def requestList(url):
    """Request a list of news tokens."""
    return _request("{0}".format(url))


def requestMarketCap(url):
    """Request market cap data for a given coin slug."""
    # print("{0}".format(url))
    return _request("{0}".format(url))

def parseList(broken_html):
    """Parse the information returned by requestList for view 'all'."""
    data = []
    soup = BeautifulSoup(broken_html, 'html.parser')
    tbody = soup.find('tbody')

    for row in tbody.find_all('tr'):
        symbol = row.find('p', class_='coin-item-symbol').text
        img = row.select_one("td > div > img").get('src')

        if img.find('1839') != -1:
            # price = row.findAll("td")[3].text.replace('$', '').replace('...', '000').replace('.', ',')
            price_1h_ = row.findAll("td")[4]
            price_1h = row.findAll("td")[4].text.replace('%', '')#.replace('.', ',')
            if price_1h_.find("span", class_='icon-Caret-up') is not None:
                price_1h_change = 'up'
            else:
                price_1h_change = 'down'
            price_24h_ = row.findAll("td")[5]
            price_24h = row.findAll("td")[5].text.replace('%', '')#.replace('.', ',')
            if price_24h_.find("span", class_='icon-Caret-up') is not None:
                price_24h_change = 'up'
            else:
                price_24h_change = 'down'
            market_cap = row.findAll("td")[6].text.replace('$', '').replace(',', '').replace('--', '0')
            volume_24h = row.findAll("td")[7].text.replace('$', '').replace(',', '')
            name = row.find('a', class_='cmc-link').find('p').text
            # url = row.find('a', class_='cmc-link').get('href')

            #data get url for each token
            token = requestMarketCap("https://coinmarketcap.com/currencies/" + name.replace(' ', '-'))  # +"/historical-data/?start="+time_last_ticker+"&end="+time_now_ticker)
            url_token, price_token, volume_token = parseToken(token)

            time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
            data = pd.json_normalize({'time': time_now, 'name': name, 'symbol': symbol, 'price': price_token, 'volume': volume_token,
                         'price_1h': price_1h, 'price_1h_change': price_1h_change,
                         'price_24h': price_24h, 'price_24h_change': price_24h_change,
                         'market_cap': market_cap, 'volume_24h': volume_24h, 'url': url_token})


            filename = '{}.csv'.format(name.replace(' ', '-'))
            if os.path.isfile(filename):
                df = pd.read_csv(filename)
                df = df.append(data, ignore_index=True)
            else:
                df = pd.DataFrame(data)
            df.to_csv(filename)

        time.sleep(random.randint(2, 7))

    # print(data)
    return data

def parseToken(broken_html):
    soup = BeautifulSoup(broken_html, 'html.parser')
    content = soup.find('body')
    div = content.find('div', class_='content')
    url = div.find('a', class_='cmc-link').get('href').replace('https://bscscan.com/token/', '')
    tbody = soup.find('tbody')
    price = tbody.findAll("td")[0].text.replace('$', '')#.replace('.', ',')
    volume = tbody.findAll("td")[3].find("span").text.replace('$', '').replace(',', '')#.replace('.', ',')
    # print(price)
    # print(volume)
    # print(url)
    return url, price, volume