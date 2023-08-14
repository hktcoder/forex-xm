# Connect Python to MetaTrader5
# https://www.youtube.com/watch?v=zu2q28h9Uvc
#
# Trading with Python
# https://www.youtube.com/watch?v=zu2q28h9Uvc&list=PLNzr8RBV5nboxi7Hg3cv-CuTF2tO70r_P

import MetaTrader5 as mt5
from datetime import datetime
import sys, os, time
sys.path.append("./modules")
import mt5mods

sleep_timer = 2
spread_threshold = 30

mt5mods.mt5_login()

try:
    while True:
        os.system("cls")

        account_info = mt5.account_info()
        print()
        print(" Login:", account_info.login, " Balance:", account_info.balance, 
              " Equity:", account_info.equity, " Profit:", round(account_info.profit,2),"\n")
        """
        start_date = datetime(2023,7,5)
        end_date = datetime.now()
        num_orders = mt5.orders_total()
        orders = mt5.orders_get()
        num_order_history = mt5.history_orders_total(start_date, end_date)
        order_history = mt5.history_orders_get(start_date, end_date)
        num_deal_history = mt5.history_deals_total(start_date, end_date)
        deal_history = mt5.history_deals_get(start_date, end_date)
        """

        # total number of positions
        num_positions = mt5.positions_total()
        #print(" num_pos:", num_positions)

        # list of positions
        positions = mt5.positions_get()
        #print("positions:", positions)
        for pos in positions:
            #print("POSITION:\n", pos, "\n")
            if pos.type == 0:
                pos_type = "BUY"
            else:
                pos_type = "SELL"
            symbol_info = mt5.symbol_info(pos.symbol)
            spread = int(round(symbol_info.spread / 10 ** symbol_info.point, 0))
            print("",pos.symbol,pos.ticket,pos_type," open:",round(pos.price_open,5)," lot:",pos.volume," profit:",round(pos.profit,2), " spread:",spread)

       
        if num_positions > 0:

            # Argument processing
            # ===================
            close_criteria = ""
            takeprofit_price = 0.0;
            if len(sys.argv) == 2:
                close_criteria = sys.argv[1]
            elif len(sys.argv) == 3:
                close_criteria = sys.argv[1]
                if close_criteria == "@":
                    takeprofit_price = sys.argv[2]
            else:
                pass

            if close_criteria == "":
                print("\n Missing command argument.\n close_all_positions.py [ be=breakeven | 1d=1dollar | ap=allprofit | fc=forceclose | @ <price>]")
                sys.exit()

            # Close when in break even
            if close_criteria == "be" or close_criteria == "breakeven":
                print("\n Closing on break even...")
                if account_info.profit >= 0 and spread < spread_threshold:
                    for position in positions:
                        print("  position_ticket:", position.ticket, "position_profit:", position.profit)
                        mt5mods.close_position(position)
                    sys.exit()

            # Close in US$1 profit
            elif close_criteria == "1d" or close_criteria == "1dollar":
                print("\n Closing on $1 profit...")
                if account_info.profit > 1 and spread < spread_threshold:
                    for position in positions:
                        print("  position_ticket:", position.ticket, "position_profit:", position.profit)
                        mt5mods.close_position(position)
                    sys.exit()

            # All trades in profit
            elif close_criteria == "ap" or close_criteria == "allprofit":
                print("\n Closing when all in profit...")
                with_lost = False
                for position in positions:
                    if position.profit < 0:
                        with_lost = True
                if with_lost == False and spread < spread_threshold:
                    for position in positions:
                        print("  position_ticket:", position.ticket, "position_profit:", round(position.profit,2))
                        mt5mods.close_position(position)
                    sys.exit()

            # Unconditionally close all trades
            elif close_criteria == "fc" or close_criteria == "forceclose":
                print("\n Force closing all positions...")
                answer = input(" Are you sure? [Y|N]")
                if (answer == "Y" or answer == "y") and spread < spread_threshold:
                    for position in positions:
                        print("  position_ticket:", position.ticket, "position_profit:", position.profit)
                        mt5mods.close_position(position)
                    sys.exit()
                else:
                    print(" Force closure ignored.")
                    sys.exit()

            # Close at a price level
            elif close_criteria == "@":
                unique_symbol_set = set()
                unique_tradetype_set = set()  # 1=Sell, 0=Buy
                symbol_price = 0.0
                for position in positions:
                    unique_symbol_set.add(position.symbol)
                    unique_tradetype_set.add(position.type)
                    tick = mt5.symbol_info_tick(position.symbol)
                num_unique_symbol = len(unique_symbol_set)
                num_unique_tradetype = len(unique_tradetype_set)

                if num_unique_symbol == 1 and num_unique_tradetype == 1:
                    unique_symbol = unique_symbol_set.pop()
                    unique_tradetype = unique_tradetype_set.pop()
                    trade_type = ""
                    if unique_tradetype == 1:
                        trade_type = "SELL"
                        symbol_price = round(tick.bid, 5)
                        print("\n Closing all " + unique_symbol + " " + trade_type + " trades when current price " + str(symbol_price) + " <= " + takeprofit_price + "...")
                        if symbol_price <= float(takeprofit_price):
                            print(" Calling close function for SELL trades")
                            for position in positions:
                                print("  position_ticket:", position.ticket, "position_profit:", position.profit)
                                mt5mods.close_position(position)
                            sys.exit()
                    else:
                        trade_type = "BUY"
                        symbol_price = round(tick.ask, 5)
                        print("\n Closing all " + unique_symbol + " " + trade_type + " trades when current price " + str(symbol_price) + " >= " + takeprofit_price + "...")
                        if symbol_price >= float(takeprofit_price):
                            print(" Calling close function for BUY trades")
                            for position in positions:
                                print("  position_ticket:", position.ticket, "position_profit:", position.profit)
                                mt5mods.close_position(position)
                            sys.exit()
                else:
                    print("\n Not processing open trades with different currency pairs.")
                    sys.exit()

            # Unknown command argument
            else:
                print("\n Unknown command argument.")
                sys.exit()

        else:
            print(" No open position.")

        # Refresh timer
        time.sleep(sleep_timer)

    mt5.shutdown()

except KeyboardInterrupt:
    print(" Program terminated.")
    mt5.shutdown()