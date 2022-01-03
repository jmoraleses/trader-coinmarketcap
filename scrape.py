""" Core scraper for coinmarketcap.com. """
import argparse
import db
import logging
import coinmarketcap
import sys
import time
import traceback

# # Parse min market cap argument
# parser = argparse.ArgumentParser(description='Scrape data from coinmarketcap into local database.')
# parser.add_argument('min_market_cap', metavar='min_cap', type=int, nargs='?', default=0,
#                    help='minimum market cap [usd] for currency to be scraped (default: scrape all)')
#
# args = parser.parse_args()

# # Configuration
timestamp_0 = 1367174841000
timestamp_1 = int(round(time.time() * 1000))
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p')
#
# # Database
database = db.Database()


def scrapeTokenList(url):
    """Scrape token list."""
    html = coinmarketcap.requestList(url)
    data = coinmarketcap.parseList(html, 'tokens')
    return data

