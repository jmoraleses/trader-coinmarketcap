""" Module for requesting data from coinmarketcap.org and parsing it. """
import json
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup


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
            price = row.findAll("td")[3].text.replace('$', '').replace('...', '000').replace('.', ',')
            price_1h_ = row.findAll("td")[4]
            price_1h = row.findAll("td")[4].text.replace('%', '').replace('.', ',')
            if price_1h_.find("span", class_='icon-Caret-up') is not None:
                price_1h_change = 'up'
            else:
                price_1h_change = 'down'
            price_24h_ = row.findAll("td")[5]
            price_24h = row.findAll("td")[5].text.replace('%', '').replace('.', ',')
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
            url_token = parseToken(token).replace('https://bscscan.com/token/', '')

            data.append({'name': name, 'symbol': symbol, 'price': price, 'price_1h': price_1h, 'price_1h_change': price_1h_change,
                         'price_24h': price_24h, 'price_24h_change': price_24h_change,
                         'market_cap': market_cap, 'volume_24h': volume_24h, 'url': url_token})
            time.sleep(1.2)

    # print(data)
    return data

def parseToken(broken_html):
    soup = BeautifulSoup(broken_html, 'html.parser')
    content = soup.find('body')
    div = content.find('div', class_='content')
    url = div.find('a', class_='cmc-link').get('href')
    # print(url)
    return url