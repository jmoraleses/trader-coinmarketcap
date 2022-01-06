from __future__ import (absolute_import, division, print_function, unicode_literals)

import datetime as dt
import os

import backtrader as bt
import backtrader.feeds as btfeed
import optuna as optuna
import pandas as pd

optuna.logging.set_verbosity(optuna.logging.WARNING)


data = None
class Bits(bt.Strategy):
    params = (
        ('range', 1),
        ('price_relative_range', 1),
        ('volume_relative_range', 1),
        ('percentage', 1),
        ('percentage_lost', 1),
        ('datasize', 1),
    )

    def __init__(self):
        self.range = self.params.range
        self.price_relative_range = self.params.price_relative_range
        self.volume_relative_range = self.params.volume_relative_range
        self.percentage = self.params.percentage
        self.percentage_lost = self.params.percentage_lost
        self.datasize = self.params.datasize
        self.contador = 0
        self.breaking = False
        self.buying = False
        self.eur = self.broker.get_value()
        self.capital = self.eur
        self.volumen_relativo = 0
        self.precio_relativo = 0
        self.coins =0
        self.capital_win = 0
        self.capital_now = 0
        self.capital_loss = 0

    def average(self):
        self.precios = 0
        self.volumenes = 0
        for self.i in range(self.range -1):
            if self.contador + self.i <= self.datasize -1:
                self.precios += self.data.open[self.i] / self.data.open[self.i + 1]
                self.volumenes += self.data.volume[self.i] / self.data.volume[self.i + 1]
            else:
                self.breaking = True
                # self.stop()
                break
        self.volumen_relativo = self.volumenes / self.range
        self.precio_relativo = self.precios / self.range
        self.contador += 1

    def next(self):
        if not self.breaking:
            self.average()

        if (self.precio_relativo >= self.price_relative_range) and (self.volumen_relativo >= self.volume_relative_range) and self.buying is False:
            self.capital = self.eur
            self.coins = self.capital / self.data.open[0]
            self.order = self.buy(size=self.coins, price=self.data.open[0])
            self.buying = True
            self.capital_win = self.capital + (self.capital * (self.percentage / 100))
            self.capital_lost = self.capital - (self.capital * (self.percentage_lost / 100))

        if self.buying is True:
            self.capital_now = self.data.open[0] * self.coins
            if self.capital_now >= self.capital_win or self.capital_now < self.capital_lost:
                self.order = self.sell(size=self.coins, price=self.data.open[0])
                self.eur = self.capital_now
                self.buying = False

    def stop(self):
        # if self.breaking is True:
        # pass
        # else:
        self.order = self.close()
        # print(self.capital_now)
        # print('value: {}, cash: {}'.format(str(self.broker.get_value()), str(self.broker.get_cash())))

size = 0
def opt_objective(trial):
    global data
    global size
    range = trial.suggest_int('range', 2, 8) #8 = 40min
    price_relative_range = trial.suggest_float('price_relative_range', 0.4, 1.0)
    volume_relative_range = trial.suggest_float('volume_relative_range', 0.4, 1.0)
    percentage = trial.suggest_int('percentage', 30, 90)
    percentage_lost = trial.suggest_int('percentage_lost', 20, 50)
    datasize = trial.suggest_int('datasize', size, size)

    cerebro = bt.Cerebro()
    cerebro.broker.set_coc(True)
    cerebro.broker.set_coo(True)
    cerebro.broker.setcash(cash=100.0) # 100€
    # cerebro.addwriter(bt.WriterFile, out='analisis.txt')
    # cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    cerebro.addstrategy(Bits, range=range, price_relative_range=price_relative_range, volume_relative_range=volume_relative_range, percentage=percentage, percentage_lost=percentage_lost, datasize=datasize)
    cerebro.adddata(data)
    cerebro.run()

    return float(cerebro.broker.get_value())


def optuna_search(token):
    global data
    global size
    filename = "csv/" + token + ".csv"
    time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')

    if os.path.isfile(filename):
        df = pd.read_csv(filename, index_col=0)
        size = df.index.max()
        time_ini = dt.datetime.strptime(df['time'].iloc[0], '%Y-%m-%d %H:%M:%S')
        data = btfeed.GenericCSVData(
            dataname=filename,
            fromdate=time_ini,
            todate=time_now,
            nullvalue=0.0,
            dtformat='%Y-%m-%d %H:%M:%S',
            datetime=1,
            open=4,
            high=4,
            low=4,
            close=4,
            volume=5,
            adj_close=4,
            openinterest=-1,
            timeframe=bt.TimeFrame.Minutes,
            compression=5,
        )

        study = optuna.create_study(direction="maximize")
        study.optimize(opt_objective, n_trials=2000) # ciclos de optimizacion
        parametros_optimos = study.best_params
        trial = study.best_trial
        print('Token: {}, saldo máximo: {}'.format(token, trial.value))
        print(parametros_optimos)
        print()



if __name__ == '__main__':
    files = os.listdir('csv/')
    for file in files:
        if os.path.isfile(os.path.join('csv/', file)):
            token = file.split('.')[0]
            optuna_search(token)
    # optuna_search("Metaland-DAO")