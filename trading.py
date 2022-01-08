import datetime as dt
import os
from multiprocessing import Process
import pandas as pd


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
        self.eur = 100.0  ###
        self.capital = self.eur

    def trading(self, df, token):

        self.data = df
        self.datasize = df.index.max()
        self.volume_ini = df.iloc[0]['volume'].astype(float)
        self.token = token

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


if __name__ == '__main__':
    time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
    print(time_now)
    process = Broker()
    process.run()
