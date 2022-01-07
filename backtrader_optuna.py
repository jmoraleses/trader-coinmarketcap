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
        ('price_relative_range_min', 1),
        ('volume_relative_range', 1),
        ('percentage', 1),
        ('percentage_lost', 1),
        ('datasize', 1),
    )

    def __init__(self):
        self.range = self.params.range
        self.price_relative_range = self.params.price_relative_range
        self.price_relative_range_min = self.params.price_relative_range_min
        self.volume_relative_range = self.params.volume_relative_range
        self.percentage = self.params.percentage
        self.percentage_lost = self.params.percentage_lost
        self.datasize = self.params.datasize
        self.contador = 0
        self.breaking = False
        self.buying = False
        self.eur = self.broker.get_cash()
        self.capital = self.eur
        self.volumen_relativo = 0
        self.precio_relativo = 0
        self.coins =0
        self.capital_win = 0
        self.capital_now = 0
        self.capital_loss = 0
        self.capital_before = 0
        self.i = 0
        self.volume_ini = self.data.volume[0]

    def next(self):

        if self.contador - self.range >= 0 and self.contador - self.range < self.datasize:
            self.precio_relativo = self.data.open[-self.range] / self.data.open
            self.volumen_relativo = self.data.volume[-self.range] / self.data.volume

            if self.volume_ini < 850000 and self.volume_ini > 300000:

                if (self.precio_relativo >= self.price_relative_range_min and self.precio_relativo <= self.price_relative_range) and (self.volumen_relativo <= self.volume_relative_range) and self.buying is False:
                    self.capital = self.eur
                    self.coins = self.capital / self.data.open
                    self.order = self.buy(size=self.coins, price=self.data.open)
                    self.buying = True
                    self.capital_win = self.capital + (self.capital * (self.percentage / 100))
                    self.capital_lost = self.capital - (self.capital * (self.percentage_lost / 100))

                if self.buying is True:
                    self.capital_now = self.data.open * self.coins
                    if self.capital_now > self.capital_before:
                        self.capital_lost = self.capital_now - (self.capital_now * (self.percentage_lost / 100))
                    if self.capital_now >= self.capital_win or self.capital_now < self.capital_lost:
                        self.order = self.sell(size=self.coins, price=self.data.open)
                        # self.order = self.close()
                        self.eur = self.capital_now
                        # self.buying = False
                        # self.stop()
                    self.capital_before = self.capital_now

        self.contador += 1


    def stop(self):
        pass
        # if self.breaking is True:
        # return self.capital_now
        # else:
        # self.order = self.close()
        # print(self.capital_now)
        # print('value: {}, cash: {}'.format(str(self.broker.get_value()), str(self.broker.get_cash())))


size = 0
def opt_objective(trial):
    global data
    global size
    range = trial.suggest_int('range', 4, 4) #12 = 1hrs
    price_relative_range = trial.suggest_float('price_relative_range', 0.85, 0.85)
    price_relative_range_min = trial.suggest_float('price_relative_range_min', 0.20, 0.20)
    volume_relative_range = trial.suggest_float('volume_relative_range', 1.0, 1.0)
    percentage = trial.suggest_int('percentage', 1500, 1500)
    percentage_lost = trial.suggest_int('percentage_lost', 2, 2)
    datasize = trial.suggest_int('datasize', size, size)

    cerebro = bt.Cerebro()
    cerebro.broker.set_coc(True)
    cerebro.broker.set_coo(True)
    cerebro.broker.setcash(cash=100.0) # 100€
    # cerebro.addwriter(bt.WriterFile, out='analisis.txt')
    # cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    cerebro.addstrategy(Bits, range=range, price_relative_range=price_relative_range, price_relative_range_min=price_relative_range_min, volume_relative_range=volume_relative_range, percentage=percentage, percentage_lost=percentage_lost, datasize=datasize)
    cerebro.adddata(data)
    cerebro.run()
    # print('value: {}, cash: {}'.format(cerebro.broker.get_value(), cerebro.broker.get_cash()))
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
        study.optimize(opt_objective, n_trials=1) # ciclos de optimizacion
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