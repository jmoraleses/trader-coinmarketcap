from __future__ import (absolute_import, division, print_function, unicode_literals)

import datetime as dt
import os
import statistics
import backtrader as bt
import backtrader.feeds as btfeed
import optuna as optuna
import pandas as pd
import numpy as np
optuna.logging.set_verbosity(optuna.logging.WARNING)


data = None
class Bits(bt.Strategy):
    params = (
        ('range', 1),
        ('price_relative_range', 1),
        ('volume_relative_range', 1),
        ('percentage', 1),
    )

    def __init__(self):
        self.range = self.params.range
        self.price_relative_range = self.params.price_relative_range
        self.volume_relative_range = self.params.volume_relative_range
        self.percentage = self.params.percentage

        self.eur = self.broker.getcash() #self.broker.get_value()

    def average(self):
        precios = []
        volumenes = []
        for i in range(self.range, self.data.size()):
            precios.append(self.data.open[i])
            volumenes.append(self.data.volume[i])
        self.volumen_relativo = np.mean(volumenes)
        self.precio_relativo = np.mean(precios)


    def next(self):
        self.average()

        if (self.precio_relativo >= self.price_relative_range) and (self.volumen_relativo >= self.volume_relative_range):
            # self.y = self.broker.get_value() / self.data.price_relative[0]
            # self.order = self.buy(size=self.y, price=self.data.price_relative[0])
            # self.order = self.buy(size=self.broker.get_value(), price=self.data.price[0])
            self.before = self.broker.get_value()
            self.y = self.broker.get_value() / self.data.open[0]
            self.order = self.buy(size=self.y, price=self.data.open[0])

        if (self.broker.get_value() >= self.before * self.percentage):
            self.y = self.broker.get_value() / self.data.open[0]
            self.order = self.sell(size=self.y, price=self.data.open[0])


    def stop(self):
        # self.order = self.close()
        print('value: {}, cash: {}'.format(str(self.broker.get_value()), str(self.broker.get_cash())))
        print('posiciones: {}, price_relative_range: {}, volume_relative_range: {}, percentage de ganancias: {}\n'.format(self.posiciones, self.price_relative_range,
                                                            self.volume_relative_range, self.percentage))



def opt_objective(trial):
    global data
    range = trial.suggest_int('range', 5, 50) # 144 = 12hrs
    rango = range
    price_relative_range = trial.suggest_float('price_relative_range', 0.0, 2.0)
    volume_relative_range = trial.suggest_float('volume_relative_range', 0.0, 2.0)
    percentage = trial.suggest_int('percentage', 20, 100)

    cerebro = bt.Cerebro()
    cerebro.broker.set_coc(True)
    cerebro.broker.set_coo(True)
    cerebro.broker.setcash(cash=100.0) # 100€
    # cerebro.addwriter(bt.WriterFile, out='analisis.txt')
    # cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    cerebro.addstrategy(Bits, range=range, price_relative_range=price_relative_range, volume_relative_range=volume_relative_range, percentage=percentage)
    cerebro.adddata(data)
    cerebro.run()

    return float(cerebro.broker.get_value())


def optuna_search(token):
    global data
    filename = "csv/" + token + ".csv"
    time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')

    if os.path.isfile(filename):
        df = pd.read_csv(filename, index_col=0)
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
        study.optimize(opt_objective, n_trials=100) # ciclos de optimizacion
        parametros_optimos = study.best_params
        trial = study.best_trial
        print('Saldo máximo: {}'.format(trial.value))
        print(parametros_optimos)
        print()
