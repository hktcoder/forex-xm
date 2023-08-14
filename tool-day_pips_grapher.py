"""
This script creates the graphs of Average Day Range from Monday to Friday 
for all major currencies.  The output is saved to a sub-directory named plots.
"""

import os, sys
sys.path.append("./modules")
import mt5mods
import MetaTrader5 as mt5
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

mt5mods.mt5_login()

one_year = 240
total_days = one_year * 1

today_index, today_name, today_datetime, today_hour = mt5mods.get_today_time_info('Etc/GMT-8')

days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

major_pairs = mt5mods.get_major_pairs()
np = np.array(major_pairs)

for i in major_pairs:
    symbol = i.name
    print(symbol)
    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, total_days)
    bars_df = pd.DataFrame(bars)

    # convert epoch to datetime
    #bars_df['time'] = pd.to_datetime(bars_df['time'], unit='s')

    # add pips field and daily pip size
    pip_point = mt5.symbol_info(symbol).point
    bars_df['pips'] = (bars_df['high'] - bars_df['low']) / pip_point

    #print(bars_df.to_string())
    #print(bars_df.head(3))
    #print(bars_df.tail(3))
    #print(bars_df.info())

    # Create empty dataframes for each day of the week
    mon_df = pd.DataFrame(columns=['time', 'pips'])
    mon_df['time'] = mon_df['time'].astype('datetime64[ns]')
    mon_df['pips'] = mon_df['pips'].astype('int')

    tue_df = pd.DataFrame(columns=['time', 'pips'])
    tue_df['time'] = tue_df['time'].astype('datetime64[ns]')
    tue_df['pips'] = tue_df['pips'].astype('int')

    wed_df = pd.DataFrame(columns=['time', 'pips'])
    wed_df['time'] = wed_df['time'].astype('datetime64[ns]')
    wed_df['pips'] = wed_df['pips'].astype('int')

    thu_df = pd.DataFrame(columns=['time', 'pips'])
    thu_df['time'] = thu_df['time'].astype('datetime64[ns]')
    thu_df['pips'] = thu_df['pips'].astype('int')

    fri_df = pd.DataFrame(columns=['time', 'pips'])
    fri_df['time'] = fri_df['time'].astype('datetime64[ns]')
    fri_df['pips'] = fri_df['pips'].astype('int')

    mon_counter = 0
    tue_counter = 0
    wed_counter = 0
    thu_counter = 0
    fri_counter = 0
    for i in range(len(bars_df)):
        #dt, high, low, pips = bars_df.loc[i][0], bars_df.loc[i][2], bars_df.loc[i][3], bars_df.loc[i][8]
        epoch, pips = int(bars_df.loc[i][0]), int(bars_df.loc[i][8])
        date = datetime.fromtimestamp(epoch)
        day_idx = date.weekday()
        day_name = days_of_week[day_idx]
        if (day_idx < 5):
            new_entry = {'time': date, 'pips': pips }
            if (day_idx == 0):
                mon_df.loc[mon_counter] = new_entry
                mon_counter += 1
            elif (day_idx == 1):
                tue_df.loc[tue_counter] = new_entry
                tue_counter += 1
            elif (day_idx == 2):
                wed_df.loc[wed_counter] = new_entry
                wed_counter += 1
            elif (day_idx == 3):
                thu_df.loc[thu_counter] = new_entry
                thu_counter += 1
            elif (day_idx == 4):
                fri_df.loc[fri_counter] = new_entry
                fri_counter += 1
            else:
                pass
        i += 1

    directory_path = "plots/" + symbol
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    mon_df.plot(x='time', y='pips', kind='bar')
    plt.title(symbol + " - " + "Monday")
    plt.savefig(directory_path + "/" + symbol + "_0_mon_cool.png")
    plt.close()

    tue_df.plot(x='time', y='pips', kind='bar')
    plt.title(symbol + " - " + "Tuesday")
    plt.savefig(directory_path + "/" + symbol + "_1_tue_cool.png")
    plt.close()

    wed_df.plot(x='time', y='pips', kind='bar')
    plt.title(symbol + " - " + "Wednesday")
    plt.savefig(directory_path + "/" + symbol + "_2_wed_cool.png")
    plt.close()

    thu_df.plot(x='time', y='pips', kind='bar')
    plt.title(symbol + " - " + "Thursday")
    plt.savefig(directory_path + "/" + symbol + "_3_thu_cool.png")
    plt.close()

    fri_df.plot(x='time', y='pips', kind='bar')
    plt.title(symbol + " - " + "Friday")
    plt.savefig(directory_path + "/" + symbol + "_4_fri_cool.png")
    plt.close()

mt5.shutdown()