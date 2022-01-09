import argparse
import datetime as dt
import os
import pprint
from multiprocessing import Process
import pandas as pd
import requests
from web3 import Web3
import time, json


capital = None
address = None
private_key = None
position_open = 0
position_max = 4

def parse_args():
    parser = argparse.ArgumentParser(description='Crypto broker trading')

    parser.add_argument('-t', '--terminate',
                        type=bool,
                        required=False,
                        default=False,
                        help='Close all open transactions')

    parser.add_argument('-c', '--capital',
                        type=str,
                        required=False,
                        default='',
                        help='Capital to trade')

    parser.add_argument('-a', '--address',
                        type=str,
                        required=False,
                        default='',
                        help='Wallet address')

    parser.add_argument('-k', '--private_key',
                        type=str,
                        required=False,
                        default='',
                        help='Wallet private key')

    return parser.parse_args()



class Broker(object):

    # params = (
    #     ('range', 7),
    #     ('price_relative_range', 0.85),
    #     ('volume_relative_range', 1.0),
    #     ('percentage', 250),
    #     ('percentage_lost', 35),
    #     ('precio_relativo_negativo', 1.4),
    #     ('precio_relativo_num', -2),
    # )

    def __init__(self, *args, **kwargs):
        global capital
        self.range = 7
        self.price_relative_range = 0.85
        self.volume_relative_range = 1.0
        self.percentage = 250
        self.percentage_lost = 35
        self.precio_relativo_negativo = 1.4
        self.precio_relativo_num = -2
        self.volumen_relativo = 0
        self.precio_relativo = 0
        self.coins = 0
        self.capital_win = 0
        self.capital_now = 0
        self.capital_loss = 0
        self.capital_before = 0
        self.precio_relativo_n = 0
        self.capital_lost = 0
        self.i = 0
        self.buying = False
        self.finish = False
        self.capital = capital

    def trading(self, df, token):

        self.data = df
        self.datasize = df.index.max()
        self.volume_ini = df.iloc[0]['volume'].astype(float)
        self.token = token
        self.token_url = df.iloc[-1]['url_token']

        if self.data.index.max() >= self.range:

            self.precio_relativo = self.data.iloc[-1 - self.range]['price'] / self.data.iloc[-1]['price']
            self.volumen_relativo = self.data.iloc[-1 - self.range]['volume'] / self.data.iloc[-1]['volume']

            if 500000 < self.volume_ini < 3000000 and self.finish is False:
                if self.precio_relativo <= self.price_relative_range and self.volumen_relativo <= self.volume_relative_range and self.buying is False:
                    self.buying = True
                    self.coins = self.capital / self.data.iloc[-1]['price']
                    self.capital_win = self.capital + (self.capital * (self.percentage / 100))
                    # self.capital_lost = self.capital - (self.capital * (self.percentage_lost / 100))
                    # call buy
                    print("buy")
                    t = False
                    while t is False:
                        t = buy(self.token_url)
                    return
                    #

                if self.buying is True:
                    self.precio_relativo_n = self.data.iloc[-1 - self.precio_relativo_num]['price'] / \
                                             self.data.iloc[-1]['price']
                    self.capital_now = self.data.iloc[-1]['price'] * self.coins

                    # if self.capital_now > self.capital_before:
                    #     self.capital_lost = self.capital_now - (self.capital_now * (self.percentage_lost / 100))
                    # self.capital_before = self.capital_now

                    if self.precio_relativo_n >= self.precio_relativo_negativo or self.capital_now >= self.capital_win:
                        self.finish = True
                        # call sell
                        print("sell")

                        return
                        #
        ###

    def run(self):
        while True:
            if dt.datetime.now().minute % 5 == 0 and dt.datetime.now().second <= 1:
                i = 0
                data = []
                processes = []
                files = os.listdir('csv/')
                for file in files:
                    if os.path.isfile(os.path.join('csv/', file)):
                        data.append(pd.read_csv("csv/" + file, index_col=0))
                        processes.append(Process(target=self.trading, args=(data[i], file,)))
                        i += 1

                print("start")
                [x.start() for x in processes]
                # [x.join() for x in processes]


def closeAllTransactions():
    pass


def buy(token_url):
    global address
    global private_key
    global position_open
    global position_max


    sender_address = address

    bsc = "https://bsc-dataseed.binance.org/"
    web3 = Web3(Web3.HTTPProvider(bsc))
    # print(web3.isConnected())

    # This is global Pancake V2 Swap router address
    router_pancake_address = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

    # Get ABI from BSCscan
    # url_eth = "https://api.bscscan.com/api"
    # router_pancake_address = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
    # contract_address = web3.toChecksumAddress(router_pancake_address)
    # API_ENDPOINT = url_eth + "?module=contract&action=getabi&address=" + str(contract_address)
    # r = requests.get(url=API_ENDPOINT)
    # response = r.json()
    # PancakeABI = json.loads(response["result"])
    # # print(PancakeABI)
    # #
    # file = open("pancakeABI.txt", "w")
    # json.dump(PancakeABI, file)
    # file.close()
    #

    PancakeABI = open('pancakeABI.txt', 'r').read()
    # print(PancakeABI)

    # always spend using Wrapped BNB
    # I guess you want to use other coins to swap you can do that, but for me I used Wrapped BNB
    spend = web3.toChecksumAddress("0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82") #now cake  # Wrapped BNB token 0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c
    # Print out your balances just for checking
    balance = web3.eth.get_balance(sender_address)
    print(balance)
    humanReadable = web3.fromWei(balance, 'ether')
    print(humanReadable)



    # Setup the PancakeSwap contract
    contract = web3.eth.contract(address=router_pancake_address, abi=PancakeABI)
    nonce = web3.eth.get_transaction_count(sender_address)
    contract_id = web3.toChecksumAddress("0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c") #token_url #Contract id is the new token we are swaping to

    if position_open < position_max:
        coins_base = float(balance) / float(position_max - position_open)
        position_open += 1

    try:
        # Create the transaction
        pancakeswap2_txn = contract.functions.swapExactETHForTokens(
            0, # coins # here setup the minimum destination token you want to have, you can do some math, or you can put a 0 if you don't want to care
            [spend, contract_id],
            sender_address,
            (int(time.time()) + 1000000)
        ).buildTransaction({
            'from': sender_address,
            'value': web3.toWei(coins_base, 'ether'),  # This is the Token(BNB) amount you want to Swap from
            'gas': 250000,
            'gasPrice': web3.toWei('7', 'gwei'),
            'nonce': nonce,
        })

        signed_txn = web3.eth.account.sign_transaction(pancakeswap2_txn, private_key=private_key)
        tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print('tx: {}'.format(web3.toHex(tx_token)))
        return True

    except ValueError:
        print("Error al realizar la transacción")
        return False


def sell(eur, url):
    pass


def main():
    global capital
    global address
    global private_key
    args = parse_args()
    capital = str(args.capital)
    address = str(args.address)
    private_key = str(args.private_key)
    closeAll = str(args.terminate)
    # if closeAll == 'True':
    #     closeAllTransactions()
    # elif wallet is not '':
    #     time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
    #     print(time_now)
    #     process = Broker()
    #     process.run()
    buy("0xbba24300490443bb0e344bf6ec11bac3aa91df72")



if __name__ == '__main__':
    main()
