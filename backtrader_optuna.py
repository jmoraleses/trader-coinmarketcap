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
        ('volume_ini', 1),
        ('precio_relativo_negativo', 1),
        ('precio_relativo_num', 1),
        ('price_min_range', 1),
        ('price_relative_range_minimum', 1),
    )

    def __init__(self):
        self.range = self.params.range
        self.price_relative_range = self.params.price_relative_range
        self.volume_relative_range = self.params.volume_relative_range
        self.percentage = self.params.percentage
        self.percentage_lost = self.params.percentage_lost
        self.datasize = self.params.datasize
        self.volume_ini = self.params.volume_ini
        self.precio_relativo_negativo = self.params.precio_relativo_negativo
        self.precio_relativo_num = self.params.precio_relativo_num
        self.price_min = self.params.price_min_range
        self.price_relative_range_minimum = self.params.price_relative_range_minimum
        self.contador = 0
        self.breaking = False
        self.buying = False
        self.eur = self.broker.get_cash()
        self.capital = self.eur
        self.volumen_relativo = 0
        self.precio_relativo = 0
        self.valor_relativo_inicial = 0
        self.coins = 0
        self.capital_win = 0
        self.capital_now = 0
        self.capital_loss = 0
        self.capital_before = 0
        self.capital_lost = 0
        self.precio_relativo_n = 0
        self.i = 0
        self.finish = False


    def next(self):
        # if True:
        if 0.001 > self.price_min:# > 0.00002:

            if 0 <= self.contador - self.range < self.datasize:
                self.precio_relativo = self.data.open[-self.range] / self.data.open
                self.volumen_relativo = self.data.volume[-self.range] / self.data.volume

                if self.contador == self.range:
                    self.valor_relativo_inicial = self.volumen_relativo / self.precio_relativo
                    print(str(self.valor_relativo_inicial))

                if 1.0 > self.valor_relativo_inicial > 0.75:
                    self.percentage = 85


                if self.volume_ini < 3000000 and self.valor_relativo_inicial > 0.1 and self.valor_relativo_inicial < 1.05 and self.finish is False:

                    if self.precio_relativo <= self.price_relative_range and self.precio_relativo >=self.price_relative_range_minimum and self.volumen_relativo <= self.volume_relative_range and self.buying is False:

                        self.coins = self.capital / self.data.open
                        self.buying = True
                        self.capital_win = self.capital + (self.capital * (self.percentage / 100))
                        self.capital_lost = self.capital - (self.capital * (self.percentage_lost / 100))
                        self.order = self.buy(size=self.coins, price=self.data.open)

                    if self.buying is True:
                        self.precio_relativo_n = self.data.open[self.precio_relativo_num] / self.data.open
                        self.capital_now = self.data.open * self.coins

                        if self.capital_now > self.capital_before:
                            self.capital_lost = self.capital_now - (self.capital_now * (self.percentage_lost / 100))
                        self.capital_before = self.capital_now

                        if self.precio_relativo_n >= self.precio_relativo_negativo or self.capital_now >= self.capital_win or self.capital_now <= self.capital_lost:
                            self.order = self.close()
                            self.finish = True

            self.contador += 1


    def stop(self):
        pass
        # print('value: {}, cash: {}'.format(str(self.broker.get_value()), str(self.broker.get_cash())))


price_min_range = 0
rango = 12
size = 0
def opt_objective(trial):
    global data
    global size
    global volume_ini
    global rango
    global price_min_range

    range_index = trial.suggest_int('range', rango, rango) #12 = 1hrs #7
    price_relative_range = trial.suggest_float('price_relative_range', 0.85, 0.85)
    price_relative_range_minimum = trial.suggest_float('price_relative_range_minimum', 0.40, 0.40)
    volume_relative_range = trial.suggest_float('volume_relative_range', 1.0, 1.0)
    percentage = trial.suggest_int('percentage', 300, 300) #250
    percentage_lost = trial.suggest_float('percentage_lost', 30, 30) #35
    datasize = trial.suggest_int('datasize', size, size)
    volume_ini = trial.suggest_int('volume_ini', volume_ini, volume_ini)
    precio_relativo_negativo = trial.suggest_float('precio_relativo_negativo', 1.40, 1.40) #1.40
    precio_relativo_num = trial.suggest_int('precio_relativo_num', -2, -2)
    price_min_range = trial.suggest_float('price_min', price_min_range, price_min_range)

    cerebro = bt.Cerebro()
    cerebro.broker.set_coc(True)
    cerebro.broker.set_coo(True)
    cerebro.broker.setcash(cash=100.0) # 100€
    # cerebro.addwriter(bt.WriterFile, out='analisis.txt')
    # cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    cerebro.addstrategy(Bits, range=range_index, price_relative_range=price_relative_range, volume_relative_range=volume_relative_range, percentage=percentage, percentage_lost=percentage_lost, datasize=datasize, volume_ini=volume_ini, precio_relativo_negativo=precio_relativo_negativo, precio_relativo_num=precio_relativo_num, price_min_range=price_min_range, price_relative_range_minimum=price_relative_range_minimum)
    cerebro.adddata(data)
    cerebro.run()
    if float(cerebro.broker.get_value()) != 100.0:
        cerebro.plot()
    # print('value: {}, cash: {}'.format(cerebro.broker.get_value(), cerebro.broker.get_cash()))
    return float(cerebro.broker.get_value())


def optuna_search(token):
    global df
    global data
    global size
    global volume_ini
    global rango
    global price_min_range

    filename = "csv/" + token + ".csv"
    time_now = dt.datetime.strptime(dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S')

    if os.path.isfile(filename):
        df = pd.read_csv(filename, index_col=0)
        volume_ini = df['volume'].iloc[0].astype(float)
        if df.index.max() >= rango:
            price_min_range = df['price'].iloc[[0, rango]].mean()
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
            print(token)
            optuna_search(token)
    # optuna_search("Crypto-Arcade-Punk")
    # optuna_search("Multistarter")
    # optuna_search("BullDog-Coin")
    # optuna_search("Community-Token")
    # optuna_search("DogeWhisky")
    # optuna_search("Metaland-DAO")
    # optuna_search("YmplePay")