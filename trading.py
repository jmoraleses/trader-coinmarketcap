import os
import sys
import time

import pandas as pd
import datetime as dt
from multiprocessing import Process
import signal

from past.builtins import raw_input


class Bits(object):

    # params = (
    #     ('range', 7),
    #     ('price_relative_range', 0.85),
    #     ('volume_relative_range', 1.0),
    #     ('percentage', 250),
    #     ('percentage_lost', 35),
    #     ('precio_relativo_negativo', 1.4),
    #     ('precio_relativo_num', -2),
    # )

    def __init__(self, data):
        self.data = data
        self.range = 7
        self.price_relative_range = 0.85
        self.volume_relative_range = 1.0
        self.percentage = 250
        self.percentage_lost = 35
        self.precio_relativo_negativo = 1.4
        self.precio_relativo_num = -2
        self.datasize = data.index.max()
        self.volume_ini = data['volume'].iloc[0].astype(float)
        self.contador = 0
        self.volumen_relativo = 0
        self.precio_relativo = 0
        self.coins = 0
        self.capital_win = 0
        self.capital_now = 0
        self.capital_loss = 0
        self.capital_before = 0
        self.precio_relativo_n = 0
        self.i = 0
        self.buying = False
        self.finish = False
        self.eur = 100.0  ###
        self.capital = self.eur
        print(self.datasize)

    def execute(self):
        ###
        if 0 <= self.contador - self.range < self.datasize and self.contador <= self.datasize: #<=
            self.precio_relativo = self.data.open[self.contador-self.range] / self.data.open[self.contador]
            self.volumen_relativo = self.data.volume[self.contador-self.range] / self.data.volume[self.contador]

            if 500000 < self.volume_ini < 3000000 and self.finish is False:
                if self.precio_relativo <= self.price_relative_range and self.volumen_relativo <= self.volume_relative_range and self.buying is False:
                    self.coins = self.capital / self.data.open[self.contador]
                    self.buying = True
                    self.capital_win = self.capital + (self.capital * (self.percentage / 100))
                    self.capital_lost = self.capital - (self.capital * (self.percentage_lost / 100))
                    # call buy
                    print("buy")
                    return
                    #

                if self.buying is True:

                    self.precio_relativo_n = self.data.open[self.contador-self.precio_relativo_num] / self.data.open
                    self.capital_now = self.data.open * self.coins

                    # if self.capital_now > self.capital_before:
                    #     self.capital_lost = self.capital_now - (self.capital_now * (self.percentage_lost / 100))
                    # self.capital_before = self.capital_now

                    if self.precio_relativo_n >= self.precio_relativo_negativo or self.capital_now >= self.capital_win:
                        self.finish = True
                        # call sell
                        print("sell")
                        return
                        #

        self.contador += 1
        ###

process = []
def cancell_operations(signum, frame):
    global process
    print("Cancelando operaciones...")
    #

    #
    sys.exit(0)




if __name__ == '__main__':
    signal.signal(signal.SIGINT, cancell_operations)

    # time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')
    while True:
        if dt.datetime.now().minute % 5 == 0 and dt.datetime.now().second <= 1:
            i = 0
            files = os.listdir('csv/')
            data = []
            for file in files:
                if os.path.isfile(os.path.join('csv/', file)):
                    data.append(pd.read_csv("csv/" + file, index_col=0))
                    process.append(Process(target=Bits, args=(data[i],)))
                    i += 1

            for i in range(len(process)):
                process[i].start()
            for i in range(len(files)):
                process[i].join()
