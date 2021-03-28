import config
import gspread
import json
import pandas as pd
import pickle
import redis
import streamlit as st
import validationNormalization as vnorm
import zlib
from crypto_api import IEX
from oauth2client.service_account import ServiceAccountCredentials

# Google Spreadsheets
scope =['https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive'
       ]
creds = ServiceAccountCredentials.from_json_keyfile_name("cred.json", scope)
client = gspread.authorize(creds)
sheet = client.open('crypto-hodl').sheet1

# Set up IEX
iex = IEX(config.IEX_TOKEN)

# Redis cache
cache = redis.Redis(host='localhost', port=6379, db=0)

def getHodl():
    """
    @brief:     Either get complete order history from
                Google Spreadsheets or from cache.
                If getting from Google Spreadsheets, save JSON
                to cache and set it to expire in 10 hours

    @return:    Dataframe of order history
    """

    hodl = cache.get('hodl')
    if hodl:
        # Decompress dataframe from cache
        df = pickle.loads(zlib.decompress(hodl))
    else:
        # Compress data to cache
        data = sheet.get_all_records()
        df = pd.read_json(json.dumps(data))
        cache.setex('hodl', 36000, zlib.compress(pickle.dumps(df)))

    return df

@st.cache
def portfolio(df):
    """
    @brief:     Calculate the profit/loss (P/L) of each cryptocurrency.
    @param:     df - complete order history dataframe
    @return:    Dataframe of cryptocurrency portfolio
    """

    coins = df.Coin.unique()
    stat = []
    for coin in coins:
        coin_df = df[df.Coin == coin]
        total = coin_df.Total.iloc[-1]
        avg = coin_df.Average.iloc[-1]
        if total == 0.0:
            continue

        ret_price = 'N/A'
        ret_precent = 'N/A'
        curr_price = cache.get(f'{coin}')
        if curr_price:
            curr_price = float(curr_price)
        else:
            curr_price = iex.getCryptoPrice(str.lower(coin))
            if curr_price:
                curr_price = float(curr_price['price'])
                cache.setex(f'{coin}', 86400, curr_price)

        if curr_price:
            avg_num = float(str(avg).replace('$', '').replace(',', ''))
            total_num = float(str(total).replace(',', ''))

            ret_price = total_num * (curr_price - avg_num)
            ret_price = '$' + str(round(ret_price, 5))
            ret_precent = ((curr_price / avg_num) - 1 ) * 100
            ret_precent = str(round(ret_precent, 5)) + '%'

            avg_num = round(avg_num, 5)
            total_num = round(total_num, 5)
            avg_num = '${:,}'.format(avg_num)
            total_num = '{:,}'.format(total_num)

        stat.append([coin, total_num, avg_num, ret_price, ret_precent])

    hodl_df = pd.DataFrame(stat, columns=['Coin', 'Total', 'Average', '$ P/L', '% P/L'])
    return hodl_df.set_index('Coin')

@st.cache
def orderHistory(df):
    """
    @brief:     Extract the columns for the order history.
    @param:     df - complete order history dataframe
    @return:    Dataframe of cryptocurrency order history.
    """

    hist_df = df[['Date', 'Direction', 'Amount', 'Coin', 'Price', 'Exchange']]
    return hist_df.set_index('Date')

@st.cache
def newOrder(df, new_order):
    """
    @brief:     Check if new submitted order was filled out properly.
                If value are invalid, send message back to user on error.
                On success, send new order to Google Spreadsheet.
    @param:     df - complete order history dataframe
    @param:     new_order - new order that was submitted
    @return:    message on submittion, and boolean value
                True on success, else False
    """

    complete_order = all(value != '' for value in new_order.values())
    if not complete_order:
        return 'All fields need to be filled', False

    order, msg = vnorm.validateNormalizeOrder(new_order)
    if order is None:
        return msg, False

    order_df = df[df['Coin'] == order['Coin']]
    order_df = order_df.append(order, ignore_index=True)

    order_df.Amount = order_df.Amount.astype(str)
    order_df.iloc[-1, order_df.columns.get_loc('Total')] = \
        order_df.Amount.apply(lambda x: x.replace(',', '')).astype(float).sum()

    _sum = 0
    for i in range(order_df.shape[0]):
        _amount = float(str(order_df.iloc[i]['Amount']).replace(',', ''))
        _price = float(order_df.iloc[i]['Price'].replace('$', '').replace(',', ''))
        _sum += (_amount * _price)

    order_df.iloc[-1, order_df.columns.get_loc('Average')] = \
        _sum / order_df.iloc[-1]['Total']
    order_df.iloc[-1, order_df.columns.get_loc('Average')] = '$' + \
        str(order_df.iloc[-1, order_df.columns.get_loc('Average')])

    sheet.insert_row(list(order_df.iloc[-1]), df.shape[0] + 2)
    df = df.append(order_df.iloc[-1])
    cache.setex('hodl', 36000, zlib.compress(pickle.dumps(df)))
    return f"Order #{df.shape[0] + 2}: {order['Direction']} {order['Amount']} {order['Coin']} has been added", True
