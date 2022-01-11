import argparse
import datetime as dt
import json
import os
import time
from multiprocessing import Process
import pandas as pd
import requests
from bs4 import BeautifulSoup
from web3 import Web3
import coinmarketcap

capital = 100.0
# address = None
# private_key = None
position_open = 0
position_max = 3  # cantidad total de transacciones permitidas al mismo tiempo
all_tokens = []


#closeTransaction
#parse_args
#closeAll in main()


def parse_args():
    parser = argparse.ArgumentParser(description='Crypto broker trading')

    parser.add_argument('-t', '--terminate',
                        type=bool,
                        required=False,
                        default=False,
                        help='Close all open transactions')

    parser.add_argument('-c', '--capital',
                        type=float,
                        required=False,
                        default=100.0,
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

    def __init__(self, *args, **kwargs):
        global capital
        self.range = 12
        self.price_relative_range = 0.85
        self.volume_relative_range = 1.0
        self.percentage = 300
        self.percentage_lost = 35
        self.precio_relativo_negativo = 1.4
        self.precio_relativo_num = -2
        self.price_relative_range_minimum = 0.4
        self.volumen_relativo = 0
        self.precio_relativo = 0
        self.valor_relativo_inicial = 0
        self.coins = 0
        self.capital_win = 0
        self.capital_now = 0
        self.capital_loss = 0
        self.capital_before = 0
        self.precio_relativo_n = 0
        self.capital_lost = 0
        self.capital_before = 0
        self.i = 0
        self.capital = capital


    def trading(self, df, token, last_operation):
        global position_max
        global position_open
        self.data = df
        self.datasize = df.index.max()
        self.volume_ini = df.iloc[0]['volume']
        self.token = token
        self.token_url = df.iloc[-1]['url_token']
        self.last_operation = last_operation


        if self.datasize >= self.range:

            self.price_min = df['price'].iloc[[0, self.range]].mean()
            if 0.001 > self.price_min: # > 0.00002:

                self.precio_relativo = self.data.iloc[-self.range]['price'] / self.data.iloc[-1]['price']
                self.volumen_relativo = self.data.iloc[-self.range]['volume'] / self.data.iloc[-1]['volume']
                self.valor_relativo_inicial = (self.data.iloc[0]['volume'] / self.data.iloc[self.range]['volume']) / (self.data.iloc[0]['price'] / self.data.iloc[self.range]['price'])

                if self.valor_relativo_inicial > 0.75:
                    self.percentage = 80

                if 30000 < self.volume_ini < 3000000 and self.valor_relativo_inicial > 0.1 and self.valor_relativo_inicial < 1.15:
                    # buy
                    if self.precio_relativo <= self.price_relative_range and self.precio_relativo >= self.price_relative_range_minimum and self.volumen_relativo <= self.volume_relative_range and self.last_operation is "nothing" and self.last_operation is not 'buy':

                        self.coins = self.capital / self.data.iloc[-1]['price']
                        self.capital_win = self.capital + (self.capital * (self.percentage / 100))
                        # self.capital_lost = self.capital - (self.capital * (self.percentage_lost / 100))
                        # call buy
                        if position_open < position_max:
                            buy(self.token, self.token_url, self.data.iloc[-1]['price'])
                        return
                    #

                    # sell
                    if self.last_operation == "buy":

                        self.precio_relativo_n = self.data.iloc[self.precio_relativo_num]['price'] / self.data.iloc[-1]['price']
                        self.capital_now = self.data.iloc[-1]['price'] * self.coins

                        if self.capital_now > self.capital_before:
                            self.capital_lost = self.capital_now - (self.capital_now * (self.percentage_lost / 100))
                        self.capital_before = self.capital_now

                        if self.precio_relativo_n >= self.precio_relativo_negativo or self.capital_now >= self.capital_win or self.capital_now <= self.capital_lost:
                            # call close transaction (sell)
                            closeTransaction(self.token, self.data.iloc[-1]['price'])
                            return
                    #
        ###

    def run(self):
        global all_tokens
        while True:

            if dt.datetime.now().minute % 30 == 0 and dt.datetime.now().second <= 1:
                html = coinmarketcap.requestList("https://coinmarketcap.com/es/new/")
                all_tokens = find_tokens(html)
            # if True:
            if dt.datetime.now().minute % 5 == 0 and dt.datetime.now().second <= 1:
                i = 0
                data = []
                processes = []

                files = os.listdir('csv/')
                for file_dead in files:
                    name_file = file_dead.replace(' ', '-').replace('.csv', '').replace('.', '')
                    if name_file not in all_tokens:
                        # cerrar operaciones abiertas de un token si ya no existe en la lista
                        closeTransaction(name_file, 0)
                        # if name_file is not "": ###
                            # delete file
                            # os.remove("csv/" + name_file + ".csv")
                            # print("Se ha cerrado la operacion y eliminado el archivo csv de: {} por desaparecer de la lista".format(name_file))

                for file in files:
                    if os.path.isfile(os.path.join('csv/', file)):

                        # comprobamos si existe alguna operación anterior sobre el token
                        last_operation = 'nothing'
                        name_file_operations = 'csv/operations/' + file.replace('.csv', '') + "_operations.csv"
                        if os.path.isfile(name_file_operations):
                            df_operations = pd.read_csv(name_file_operations, index_col=0)
                            if df_operations.iloc[-1]['operation'] == 'buy':
                                last_operation = 'buy'
                            elif df_operations.iloc[-1]['operation'] == 'sell':
                                last_operation = 'sell'

                        data.append(pd.read_csv("csv/" + file, index_col=0))
                        processes.append(Process(target=self.trading, args=(data[i], file.replace('.csv', ''), last_operation,)))
                        i += 1

                # print("start")
                [x.start() for x in processes]
                [x.join() for x in processes]

            else:
                time.sleep(1)


def getABI():
    # Get ABI from BSCscan
    bsc = "https://bsc-dataseed.binance.org/"
    web3 = Web3(Web3.HTTPProvider(bsc))
    url_eth = "https://api.bscscan.com/api"
    router_pancake_address = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
    contract_address = web3.toChecksumAddress(router_pancake_address)
    API_ENDPOINT = url_eth + "?module=contract&action=getabi&address=" + str(contract_address)
    r = requests.get(url=API_ENDPOINT)
    response = r.json()
    PancakeABI = json.loads(response["result"])
    # print(PancakeABI)
    file = open("pancakeABI.txt", "w")
    json.dump(PancakeABI, file)
    file.close()


def buy(token_name, token_url, price):
    global address
    global private_key
    global position_open
    global position_max

    bsc = "https://bsc-dataseed.binance.org/"
    web3 = Web3(Web3.HTTPProvider(bsc))
    # This is global Pancake V2 Swap router address
    router_pancake_address = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

    # Asignamos el contrato de pancakeSwap
    PancakeABI = open('pancakeABI.txt', 'r').read()
    # getABI() # not used
    # print(PancakeABI)

    # Wrapped BNB
    spend = web3.toChecksumAddress(
        "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c")  # Wrapped BNB token 0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c
    balance_ = web3.eth.get_balance(address)
    balance = web3.fromWei(balance_, 'ether')
    # print(balance_)
    balance = 100.0 ###
    # print(balance)

    # Setup the PancakeSwap contract
    contract = web3.eth.contract(address=router_pancake_address, abi=PancakeABI)
    nonce = web3.eth.get_transaction_count(address)
    contract_id = web3.toChecksumAddress(token_url)  # token_url #Contract id is the new token we are swaping to

    try:

        if position_open < position_max:
            coins = float(balance - (balance / 10)) / float(position_max - position_open)
            position_open += 1

            # # Create the transaction
            # pancakeswap2_txn = contract.functions.swapExactETHForTokens(
            #     0,  # coins or you can put a 0 if you don't want to care
            #     [spend, contract_id],
            #     address,
            #     (int(time.time()) + 1000000)
            # ).buildTransaction({
            #     'from': address,
            #     'value': web3.toWei(coins, 'ether'),  # This is the Token(BNB) amount you want to Swap from
            #     'gas': 250000,
            #     'gasPrice': web3.toWei('7', 'gwei'),
            #     'nonce': nonce,
            # })
            #
            # signed_txn = web3.eth.account.sign_transaction(pancakeswap2_txn, private_key=private_key)
            # tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            # print('Buy {} tx: {}'.format(token_name, web3.toHex(tx_token)))

            # Guardar en csv la fecha, la compra y la cantidad de tokens
            time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
            data = pd.json_normalize(
                {'time': time_now, 'name': token_name, 'operation': 'buy', 'coins': coins, 'price': price, 'token_url': token_url})
            if os.path.isfile("csv/operations/" + token_name + "_operations.csv"):
                df_buy = pd.read_csv("csv/operations/" + token_name + "_operations.csv", index_col=0)
                df_buy = df_buy.append(data, ignore_index=True)
                df_buy.to_csv("csv/operations/" + token_name + "_operations.csv")
            else:
                df_buy = pd.DataFrame(data)
                df_buy.to_csv("csv/operations/" + token_name + "_operations.csv")

            print('{} Buy {}: {} {}'.format(time_now, token_name, coins, price))
            return True

    except ValueError:
        time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
        print("{} Error al realizar la transacción de compra con {}".format(time_now, token_name))
        return False


def sell(token_name, token_url, coins, price):
    global address
    global private_key
    global position_open

    bsc = "https://bsc-dataseed.binance.org/"
    web3 = Web3(Web3.HTTPProvider(bsc))
    # This is global Pancake V2 Swap router address
    router_pancake_address = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

    # Asignamos el contrato de pancakeSwap
    PancakeABI = open('pancakeABI.txt', 'r').read()
    # getABI() # not used
    # print(PancakeABI)

    # Token to BNB
    spend = web3.toChecksumAddress(token_url) # token url

    # Setup the PancakeSwap contract
    contract = web3.eth.contract(address=router_pancake_address, abi=PancakeABI)
    nonce = web3.eth.get_transaction_count(address)
    contract_id = web3.toChecksumAddress("0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c") # to Wrapped BNB token

    try:

        # # Create the transaction
        # pancakeswap2_txn = contract.functions.swapExactETHForTokens(
        #     0,  # coins or you can put a 0 if you don't want to care
        #     [spend, contract_id],
        #     address,
        #     (int(time.time()) + 1000000)
        # ).buildTransaction({
        #     'from': address,
        #     'value': web3.toWei(coins, 'ether'),  # This is the Token(BNB) amount you want to Swap from
        #     'gas': 250000,
        #     'gasPrice': web3.toWei('7', 'gwei'),
        #     'nonce': nonce,
        # })
        #
        # signed_txn = web3.eth.account.sign_transaction(pancakeswap2_txn, private_key=private_key)
        # tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        # print('Sell {} tx: {}'.format(token_name, web3.toHex(tx_token)))
        time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
        print('{} Sell {}: {} {}'.format(time_now, token_name, coins, price))
        position_open -= 1

        # guardar en el archivo transacciones la venta
        time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
        data = pd.json_normalize(
            {'time': time_now, 'name': token_name, 'operation': 'sell', 'coins': coins, 'price': price,
             'token_url': token_url})

        if os.path.isfile("csv/operations/" + token_name + "_operations.csv"):
            df_sell = pd.read_csv("csv/operations/" + token_name + "_operations.csv", index_col=0)
            df_sell = df_sell.append(data, ignore_index=True)
            df_sell.to_csv("csv/operations/" + token_name + "_operations.csv")
        else:
            df_sell = pd.DataFrame(data)
            df_sell.to_csv("csv/operations/" + token_name + "_operations.csv")

        return True

    except ValueError:
        time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
        print("{} Error al realizar la transacción de venta de {}".format(time_now, token_name))
        return False


def closeTransaction(token_name, price):
    # si existe el archivo de operaciones continuar
    filename = "csv/operations/" + token_name + "_operations.csv"
    if os.path.isfile(filename):
        df_close = pd.read_csv(filename, index_col=0)
        if df_close.iloc[-1]['operation'] == 'buy':
            token_url = df_close.iloc[-1]['token_url']
            coins = df_close.iloc[-1]['coins']
            # sell token
            sell(token_name, token_url, coins, price)




def closeAllTransactions():
    files = os.listdir('csv/operations/')
    for file in files:
        if file.endswith("_operations.csv"):
            closeTransaction(file.replace('_operations.csv', ''), 0)


def find_tokens(broken_html):
    tokens = []
    soup = BeautifulSoup(broken_html, 'html.parser')
    tbody = soup.find('tbody')
    for row in tbody.find_all('tr'):
        try:
            img = row.select_one("td > div > img").get('src')
            if img.find('1839') != -1:
                name = row.find('a', class_='cmc-link').find('p').text
                if name not in tokens:
                    tokens.append(name.replace(' ', '-').replace('.', ''))
        except:
            print('Error al rasrear la lista')
    return tokens


def main():
    global all_tokens
    global capital
    global address
    global private_key
    # args = parse_args()
    # capital = float(args.capital)
    # address = str(args.address)
    # private_key = str(args.private_key)
    # terminate = bool(args.terminate)
    terminate = False ###

    # Comprobamos los tokens del listado
    html = coinmarketcap.requestList("https://coinmarketcap.com/es/new/")
    all_tokens = find_tokens(html)

    if not os.path.exists("csv"):
        os.makedirs("csv")
    if not os.path.exists("csv/operations"):
        os.makedirs("csv/operations")

    if terminate is True:
        pass ###
        # closeAllTransactions()
    elif address is not '' and private_key is not '' and capital > 0.0:
        time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
        print('{} start'.format(time_now))
        Broker().run()


if __name__ == '__main__':
    main()
