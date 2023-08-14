"""
Connect Python to MetaTrader5
https://www.youtube.com/watch?v=zu2q28h9Uvc

Trading with Python
https://www.youtube.com/watch?v=zu2q28h9Uvc&list=PLNzr8RBV5nboxi7Hg3cv-CuTF2tO70r_P

Command Arguments:
    pair= - gbpusd or eurchf
    type= - buy or sell
    lot=  - 0.10 or 1.0
"""

import MetaTrader5 as mt5
from datetime import datetime
import sys
import os
sys.path.append("./modules")
import mt5mods

os.system("cls")

mt5mods.mt5_login()

# Display account info
# ====================
account_info = mt5.account_info()
print("")
print(" Login:", account_info.login, " Balance:", account_info.balance, " Equity:", account_info.equity, " Profit:", account_info.profit)

# Position list
# =============
num_positions = mt5.positions_total()
print(" num_pos:", num_positions)
positions = mt5.positions_get()
for pos in positions:
    if pos.type == 0:
        pos_type = "BUY"
    else:
        pos_type = "SELL"
    print(" symbol:",pos.symbol,"  ticket:",pos.ticket,"  type:",pos_type,"  price_open:",pos.price_open,"  profit:",pos.profit)

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

# Default argument values
# =======================
currency_pair = ""
trade_type = ""
lot_size = 0.10

# Argument processing
# ===================
if len(sys.argv) == 4:
    currency_pair = sys.argv[1].upper() + "m#"
    trade_type = sys.argv[2].upper()
    lot_size = float(sys.argv[3])
else:
    print("")
    print(" Missing command arguments.")
    print("  Syntax : open_position.py <currency_pair> <trade_type> <lot_size>")
    print("  Example: open_position_py usdcad sell 1.0")

if (currency_pair != "" and trade_type != ""):
    if trade_type == "BUY":
        price = mt5.symbol_info_tick(currency_pair).ask
        trade_type = mt5.ORDER_TYPE_BUY
    elif trade_type == "SELL":
        price = mt5.symbol_info_tick(currency_pair).bid
        trade_type = mt5.ORDER_TYPE_SELL
    else:
        pass
    #print(currency_pair, "price:", price)

    # How to send Orders to the Market | Trading with Python #3
    # https://www.youtube.com/watch?v=65Dc5KSGKhw
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": currency_pair,
        "volume": lot_size,
        "type": trade_type,
        "price": price,
        "sl": 0.0,
        "tp": 0.0,
        "deviation": 20,
        "magic": 12345,
        "comment": "python script open",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    print(" Comment:",result.comment, ", retcode", result.retcode)


mt5.shutdown()
