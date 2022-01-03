""" Module for requesting data from coinmarketcap.org and parsing it. """

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


def requestMarketCap(slug):
    """Request market cap data for a given coin slug."""
    print("{0}".format(slug))
    return _request("{0}".format(slug))


def parseList(broken_html, type):
    """Parse the information returned by requestList for view 'all'."""
    global slug, name
    data = []
    soup = BeautifulSoup(broken_html, 'html.parser')
    tbody = soup.find('tbody')

    for row in tbody.find_all('tr'):
        symbol = row.find('p', class_='coin-item-symbol').text
        img = row.select_one("td > div > img").get('src')
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
        market_cap = row.findAll("td")[6].text.replace('$', '').replace(',', '')
        volume_24h = row.findAll("td")[7].text.replace('$', '').replace(',', '')

        # a = row.find('a', class_='cmc-link')
        # if a is not None:
        #     slug = a.get('href')
        #     name = a.find('p').text

        if img.find('1839') != -1:
            data.append({'symbol': symbol, 'price': price, 'price_1h': price_1h, 'price_1h_change': price_1h_change,
                         'price_24h': price_24h, 'price_24h_change': price_24h_change,
                         'market_cap': market_cap, 'volume_24h': volume_24h})
            # data.append({'symbol': symbol, 'name': name, 'slug': slug, 'binance': 'Binance Coin'})

    # print(data)
    return data

