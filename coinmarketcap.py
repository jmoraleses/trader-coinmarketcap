""" Module for requesting data from coinmarketcap.org and parsing it. """
from datetime import datetime
import json
import logging
from io import StringIO

import lxml.html
from random import random
import requests
import time

from bs4 import BeautifulSoup
from future.utils import iteritems
from lxml import etree

# baseUrl = "http://coinmarketcap.com"
# graphBaseUrl = "http://graphs2.coinmarketcap.com" #Coinmarket cap endpoint changed from graphs to graphs2

countRequested = 0
interReqTime = 20
lastReqTime = None


def _request(target):
    """Private method for requesting an arbitrary query string."""
    global countRequested
    global lastReqTime
    if lastReqTime is not None and time.time() - lastReqTime < interReqTime:
        timeToSleep = random()*(interReqTime-time.time()+lastReqTime)*2
        logging.info("Sleeping for {0} seconds before request.".format(timeToSleep))
        time.sleep(timeToSleep)
    logging.info("Issuing request for the following target: {0}".format(target))
    r = requests.get(target)
    lastReqTime = time.time()
    countRequested += 1
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
        a = row.find('a', class_='cmc-link')
        if a is not None:
            slug = a.get('href')
            name = a.find('p').text
        symbol = row.find('p', class_='coin-item-symbol').text
        img = row.select_one("td > div > img").get('src')
        if img.find('1839') != -1:
            data.append({'symbol': symbol, 'name': name, 'slug': slug, 'binance': 'Binance Coin'})

    # print(data)
    return data


def parseMarketCap(jsonDump, slug):
    """ """
    data = []
    rawData = json.loads(jsonDump)

    print(rawData)
    # Covert data in document to wide format
    dataIntermediate = {}
    targetFields = [str(key.replace('_data', '')) for key in rawData.keys()]
    for field, fieldData in iteritems(rawData):
        for row in fieldData:
            time = int(row[0]/1000)
            if time not in dataIntermediate:
                dataIntermediate[time] = dict(zip(targetFields, [None]*len(targetFields)))
            dataIntermediate[time][field] = row[1]

    # Generate derived data & alter format
    times = sorted(dataIntermediate.keys())
    for time in times:
        datum = dataIntermediate[time]
        datum['slug'] = slug
        datum['time'] = datetime.utcfromtimestamp(time)

        if (datum['market_cap_by_available_supply'] is not None
            and datum['price_usd'] is not None
            and datum['price_usd'] is not 0):
            datum['est_available_supply'] = float(datum['market_cap_by_available_supply'] / datum['price_usd'])
        else:
            datum['est_available_supply'] = None

        data.append(datum)

    return data
