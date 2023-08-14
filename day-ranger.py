"""
Strategy Name:
    Day Ranger

Command Arguments:
    KEY: alarm      VALUES: off
    KEY: refresh    VALUES: <int>
    KEY: sort       VALUES: pipadrave, symbol, pos

Description:
    This script does the following:
    (1) Calculates how much % the price has moved vs the average of that same day's range.  
        100% means the price had reached the day's average move and will likely reverse in direction.
    (2) Determines position of the current price with respect to the pip range.
        100% means the price is continuing to exceed the highest-high price. 0% means exceeding the lowest-low.
    (3) Get the total of how many AdRs have been surpassed by today's pip movement

    # Table Field Description #
    Symbol       - major currency pair
    Highest-High - current day's highest-high price level
    Lowest-Low   - current day's lowest-low price level
    Pip-Move     - total pips price has moved today 
    AdR-Ave      - average of all same-day's pip moves
    Pip/AdR_Ave  - percent average of today's pip move vs the average of all same-day's pip moves (AdR)
    All_AdR<Pip  - percent count of how many the today's pip move have passed over each same-day's pip moves
    Price_Pos    - current bid level from lowest-low level; 0.00 means the current bid price is going down, 100.00 is going up
    Spread       - currency pair's spread in real time
    
Trade Timing Sample:
    pip/ave_adr >= 100%
    All_AdR<Pip >= 70%
    price_position: >= 90% or <= 10%

CHANGELOG:
    2023Jul10 - added auto_trade
    2023Jul07 - AdR_All/Pip > All_AdR<pip, pip_adr_all > all_adr_pip, added threshold_spread
              - added initial open trade
    2023Jul05 - added spread, alarm disablement, added alarm/refresh/sort arguments, 
              - renamed Price_Level > Price_Pos, Pips-Today > Pip-Move
    2023Jul01 - fixed weekend issues; individualized data highlighting; winsound beeping
    2023Feb05 - added Price_Level
    2023Feb04 - added Pip/AdR-All 
    2023Feb03 - initial code; highest-high, lowest-low, pips-today, ave-adr, pip/adr_ave
"""

import sys
sys.path.append("./modules")
import mt5mods
import MetaTrader5 as mt5
from datetime import datetime
import os
import datetime
import time
import pytz
import numpy as np
import pandas as pd
from colorama import init, Fore
#from getpass import getpass
#from fbchat import Client
#from fbchat.models import *


# Threshold Values
# ================
threshold_pipadrave  =  120
threshold_pipadrall  =  50
threshold_price_high =  99
threshold_price_low  =  1
threshold_spread     =  25
init_lot_size        =  1.0


def get_tradetype_and_price(pricePos, symbolPair):
    if pricePos >= threshold_price_high:
        openPrice = mt5.symbol_info_tick(symbolPair).bid
        tradeType = mt5.ORDER_TYPE_SELL
        return tradeType, openPrice
    elif pricePos <= threshold_price_low:
        openPrice = mt5.symbol_info_tick(symbolPair).ask
        tradeType = mt5.ORDER_TYPE_BUY
        return tradeType, openPrice
    else:
        pass


def order_send_request(symbolPair, lotSize, tradeType, orderPrice):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbolPair,
        "volume": lotSize,
        "type": tradeType,
        "price": orderPrice,
        "sl": 0.0,
        "tp": 0.0,
        "deviation": 20,
        "magic": 123456,
        "comment": "",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)


def recalculate_lot_size(lotSize, pipAdrAve):
    if   pipAdrAve >= 190:
        return lotSize * 4.0
    elif pipAdrAve >= 180:
        return lotSize * 3.5  
    elif pipAdrAve >= 170:
        return lotSize * 3.0
    elif pipAdrAve >= 160:
        return lotSize * 2.5
    elif pipAdrAve >= 150:
        return lotSize * 2.0
    elif pipAdrAve >= 140:
        return lotSize * 1.5
    elif pipAdrAve >= 130:
        return lotSize * 1.0
    else:
        return lotSize


def main():

    # Process Passed Arguments
    # ========================
    if len(sys.argv) > 0:
        alarm_status = ""
        refresh_time = 0
        sort_by = ""
        auto_trade = "off"
        arguments = sys.argv[1:]
        for argument in arguments:
            key, value = argument.split('=')
            if key == 'alarm':
                alarm_status = value
            elif key == 'refresh':
                refresh_time = int(value)
            elif key == 'sort':
                sort_by = value
            elif key == 'trade':
                auto_trade = value
            else:
                pass

    # Market Open Check
    # =================
    try:
        while (True):
            is_close, broker_dt = mt5mods.is_forex_market_close()
            if is_close == True:
                print("  Forex market is closed.  Broker time is:", broker_dt)
                time.sleep(5)
            else:
                break
    except KeyboardInterrupt:
        print("  Program terminated.")
        mt5.shutdown()
        sys.exit()

    ## For FB Messenger chat message
    ## recipient not working using user-id or email, instead received by email/password credential
    #email = "egbsjunkmail@gmail.com"
    #password = ""
    #recipient_id = ""
    #client = Client(email, password)

    # Number of days to check for historical day's range (AdR)
    #adr_days = 120

    mt5mods.mt5_login()

    # Get all values of the Average Day Range
    # =======================================
    adr_values = mt5mods.get_today_adr_values()
    if adr_values.empty:
        print("adr_values is empty. Program terminated")
        mt5.shutdown()
        sys.exit()

    try:
        while True:

            try:
                os.system("cls")

                # Define the field names and data types for final result
                dtype = [('symbol', 'U10'), ('pip', 'i4'), ('highest', 'f8'), ('lowest', 'f8'), ('aveadr', 'i4'), 
                         ('pipadrave', 'f2'), ('pos', 'f2'), ('pipadrall', 'f2'), ('spread', 'i4')]
                # Create a structured array
                data = np.array([], dtype=dtype)

                # Get the unique trading pairs and currencies
                trading_pairs = set()
                trading_currencies = set()
                num_positions = mt5.positions_total()
                if num_positions > 0:
                    positions = mt5.positions_get()
                    for pos in positions:
                        pos_symbol = pos.symbol
                        trading_currencies.add(pos_symbol[:3])
                        trading_currencies.add(pos_symbol[3:-2])
                        trading_pairs.add(pos_symbol)

                symbols = mt5mods.get_major_pairs()
                for symbol in symbols:

                    price = symbol.bid
                    spread = symbol.spread

                    # get today's pip range and hh/ll prices
                    # ======================================
                    try:
                        (highest_high, lowest_low, pip) = mt5mods.todays_pip_range(symbol.name)
                    except Exception as e:
                        print("Error occurred in", symbol.name, "todays_pip_range.")
                        continue

                    # get the adr of the day
                    # ======================
                    try:
                        adr_days = 360  # Number of days to check for historical day's range (AdR); not today's index!
                        ave_adr = mt5mods.average_day_range(symbol.name, adr_days)
                        # calculate the % of pip per adr
                        pip_adr_ave = round((pip / ave_adr) * 100, 2)
                    except Exception as e:
                        print("Error occurred in average_day_range:", e)
                        mt5.shutdown()
                        sys.exit()

                    # get the current price's chart position
                    # ======================================
                    try:
                        if highest_high > 0 and lowest_low > 0 and price > 0:
                            price_position = mt5mods.get_price_position(highest_high, lowest_low, price)
                        else:
                            price_position = 0.00
                    except Exception as e:
                        print("Error occurred at get_price_position:", e)
                        mt5.shutdown()
                        sys.exit()

                    # get the adr values
                    # ==================
                    try:
                        # get the total number of rows of a specific currency pair where the pip moves of this same day 
                        #  is less than today's pip move 
                        adr_less_than_pips_total = adr_values[(adr_values['pair'] == symbol.name) & (adr_values['pips'] < pip)].shape[0]
                        
                        # get the total rows of a specific currency pair
                        adr_symbol_total = adr_values[(adr_values['pair'] == symbol.name)].shape[0]
                        
                        # get the percentage of total adr < today's pip move
                        all_adr_pip = round((adr_less_than_pips_total / adr_symbol_total) * 100, 2)

                    except Exception as e:
                        print("Error occurred at adr_values:", e)
                        mt5.shutdown()
                        sys.exit()

                    # create a new array entry and add to data array
                    # ==============================================
                    new_entry = np.array([(symbol.name, pip, highest_high, lowest_low, ave_adr, pip_adr_ave, price_position, 
                                           all_adr_pip, spread)], dtype=dtype)
                    data = np.concatenate((data, new_entry))


                ##############################
                ##  START OF TABLE DISPLAY  ##
                ##############################

                # Table sort method
                # =================
                if sort_by == "pipadrave":
                    data = np.sort(data, order='pipadrave')[::-1]
                elif sort_by == "symbol":
                    data = np.sort(data, order='symbol')
                elif sort_by == "pos":
                    data = np.sort(data, order='pos')[::-1]
                else:
                    data = np.sort(data, order='pipadrave')[::-1]

                # Strategy Title & Argument Variables
                # ===================================
                print("\n  -=[ DAY-RANGER ]=-")
                if alarm_status == "off":
                    print("  Alarm-Status:", alarm_status, end='')
                if refresh_time > 0:
                    print("  Refresh-Time:", refresh_time, end='')
                if sort_by != "":
                    print("  Sort-By:", sort_by, end='')
                if auto_trade != "":
                    print("  Auto-Trade:", auto_trade, end='')
                print("")

                #print("  Thresholds: ", "pip_adr_ave >=", threshold_pipadrave, "," , "all_adr_pip >=", threshold_pipadrall, 
                #      ",", threshold_price_high, ">= price_pos <=", threshold_price_low, ",", "spread <=", threshold_spread)
                print("  Trading-Pairs:", trading_pairs, "  ", "Trading-Currencies:", trading_currencies)
                init()
                play_alarm = False

                # Field Names
                # ===========
                print("  ---------+-----------+-----------+------+------+---------+---------+--------+-----")
                print("    Symbol |   Highest |    Lowest |  Pip |  AdR | Pip/AdR | All_AdR |  Price | Sprd")
                print("           |      High |       Low | Move |  Ave |   Ave-% |  <Pip-% |  Pos-% |        ")
                print("  ---------+-----------+-----------+------+------+---------+---------+--------+-----")
                print("                 T H R E S H O L D S             |     {:>3d} |     {:>3d} |   {:>2d}/{:>1d} |  {:>3d}".
                      format(threshold_pipadrave,threshold_pipadrall,threshold_price_high,threshold_price_low,threshold_spread))
                print("  ---------+-----------+-----------+------+------+---------+---------+--------+----- ")
                
                # Table Values
                # ============
                for x in data:
                    pair, pip, hh, ll, ave_adr, pip_adr_ave, price_pos, all_adr_pip, spread = x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8]

                    if pair in trading_pairs:
                        print(Fore.YELLOW + ("  {}   {:>9.5f}   {:>9.5f}   {:>4d}   {:>4d}    " + Fore.RESET).
                            format(pair, hh, ll, pip, ave_adr), end='')
                    else:
                        print(("  {}   {:>9.5f}   {:>9.5f}   {:>4d}   {:>4d}    ").
                            format(pair, hh, ll, pip, ave_adr), end='')
                    
                    if pip_adr_ave >= threshold_pipadrave:
                        print(Fore.GREEN + ("{:>6.2f}    " + Fore.RESET).format(pip_adr_ave), end='')
                    else:
                        print(("{:>6.2f}    ").format(pip_adr_ave), end='')

                    if all_adr_pip >= threshold_pipadrall:
                        print(Fore.GREEN + ("{:>6.2f}   " + Fore.RESET).format(all_adr_pip), end='')
                    else:
                        print(("{:>6.2f}   ").format(all_adr_pip), end='')

                    if price_pos >= threshold_price_high or price_pos <= threshold_price_low:
                        print(Fore.GREEN + ("{:>6.2f}   " + Fore.RESET).format(price_pos), end='')
                    else:
                        print(("{:>6.2f}   ").format(price_pos), end='')
                    
                    if spread <= threshold_spread:
                        print((Fore.GREEN + "{:>4d}" + Fore.RESET).format(spread))
                    else:
                        print(("{:>4d}").format(spread))


                    # Trigger sound alarm and notification
                    # ====================================
                    if (pip_adr_ave >= threshold_pipadrave and all_adr_pip >= threshold_pipadrall and 
                        (price_pos >= threshold_price_high or price_pos <= threshold_price_low)) and spread <= threshold_spread:
                        now = datetime.datetime.now()
                        hour_now = now.hour
                        if hour_now >= 3 and hour_now <= 6:
                            pass
                        else:
                            num_positions = mt5.positions_total()

                            if num_positions == 0 and auto_trade == "on":
                                trade_type, open_price = get_tradetype_and_price(price_pos, pair)
                                lot_size = recalculate_lot_size(init_lot_size, pip_adr_ave)
                                order_send_request(pair, lot_size, trade_type, open_price)

                            if num_positions > 0 and auto_trade == "on":
                                quote_currency = pair[:3]
                                base_currency = pair[3:-2]
                                if base_currency not in trading_currencies and quote_currency not in trading_currencies:
                                    trade_type, open_price = get_tradetype_and_price(price_pos, pair)
                                    lot_size = recalculate_lot_size(init_lot_size, pip_adr_ave)
                                    order_send_request(pair, lot_size, trade_type, open_price)

                            # Set off alarm only open trading pair
                            if num_positions > 0 and pair in trading_pairs:
                                play_alarm = True

                                # FB Messenger alert
                                #message = "Day-Ranger Alert: " + pair
                                #client.send(Message(text=message), thread_id=client.uid, thread_type=ThreadType.USER)


                # Sound alarm
                # ===========
                if play_alarm == True and alarm_status != "off":
                    mt5mods.play_beep(play_alarm)

                # Refresh time
                # ============
                print("")
                total_time = 9
                if refresh_time > 0:
                    total_time = refresh_time

                # Count-down timer
                # ================
                interval = 1
                start = time.time()
                while time.time() - start < total_time:
                    remaining = int(total_time - (time.time() - start))
                    print(f"\r  Refresh count-down: {remaining:}", end="")
                    time.sleep(interval)

            except Exception as e:
                print("Error: ", e)

        mt5.shutdown()

    except KeyboardInterrupt:
        print("\n  Program terminated.")
        mt5.shutdown()

if __name__ == "__main__":
    main()
