import config
import hodl
import json
import redis
import streamlit as st
import supported_coins
from datetime import datetime
from crypto_api import IEX, CoinMarketCap

# Set up IEX
iex = IEX(config.IEX_TOKEN)
marketcap = CoinMarketCap(config.CMCAP_KEY)

# Redis cache
cache = redis.Redis(host='localhost', port=6379, db=0)

# Streamlit
screen = st.sidebar.selectbox("View", ('HODL', 'Overview'), index=0)
st.title(screen)

# Display my portfolio of my cryptocurrency and order history.
# As well as have a location to submit new orders to the dataframe
if 'HODL' == screen:
    df = hodl.getHodl()
    portfolio_df = hodl.portfolio(df)
    hist_df = hodl.orderHistory(df)

    # Display my portfolio
    st.subheader('Crypto Portfolio')
    st.dataframe(portfolio_df)

    # Display order history with a filter to select which direction,
    # coins, and exchange to see on DataFrame
    st.subheader('Order History')
    all_coins = hist_df.Coin.tolist()
    unique_coins = list(dict.fromkeys(all_coins))
    coins = st.multiselect("Select which coins to see", unique_coins, default=unique_coins, help='Select a coin to look at')
    mask_coins = hist_df.Coin.isin(coins)
    st.dataframe(hist_df[mask_coins])

    # Sidebar to add a new order
    # New order requires all input:
    #   * Coin
    #   * Direction
    #   * Amount
    #   * Price
    #   * Exchange
    #   * Date
    # Order wil then be validated once submit button is pressed
    new_order = {}
    st.sidebar.subheader('New order')
    new_order['Coin'] = st.sidebar.selectbox('Coin', supported_coins.getCoins(), index=0)
    new_order['Direction'] = st.sidebar.radio('Direction', ['BUY', 'SELL'])
    new_order['Amount'] = st.sidebar.text_input('Amount')
    new_order['Price'] = st.sidebar.text_input('Executed Price')
    new_order['Exchange'] = st.sidebar.text_input('Exchange')
    new_order['Date'] = st.sidebar.radio('Use current date?', ['Yes', 'No'])
    if new_order['Date'] == 'No':
        now = datetime.now()
        _date = st.sidebar.date_input('Enter date', now).strftime('%Y-%m-%d')
        _hour = st.sidebar.slider('Hour', min_value=0, max_value=23, value=now.hour)
        _min = st.sidebar.slider('Min', min_value=0, max_value=59, value=now.minute)
        new_order['Date'] = f'{_date} {_hour}:{_min}'
    else:
        new_order['Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if st.sidebar.button('Submit order'):
        msg, ok = hodl.newOrder(df, new_order)
        if ok:
            st.sidebar.success(msg)
        else:
            st.sidebar.error(msg)

if 'Overview' == screen:
    # Get description about coin
    ok = True
    coin = str.lower(st.sidebar.text_input('Coin', value='BTC'))
    cached_info = cache.get(f'{coin}_info')
    if cached_info:
        info = json.loads(cached_info)
    else:
        info, ok = marketcap.getCoinInfo(coin)
        cache.setex(f'{str.lower(coin)}_info', 86400, json.dumps(info))

    if ok:
        data = info['data'][str.upper(coin)]
        name = data['name']
        desc = data['description']
        logo = data['logo']

        # Organize look by having logo on the left,
        # and description on the right
        col_1, col_2 = st.beta_columns([1, 4])
        with col_1:
            st.image(logo)
        with col_2:
            st.markdown(f'# {name}')
            st.subheader('Description:')
            st.write(desc)
    else:
        # Let user know that an error occured
        st.markdown('## Uh oh!')
        st.markdown('### ' + info)

    # Get latest news about coin
    st.markdown('## News')
    cached_news = cache.get(f'{coin}_news')
    if cached_news:
        news = json.loads(cached_news)
    else:
        news = iex.getCoinNews(coin + 'usdt')
        cache.setex(f'{str.lower(coin)}_news', 86400, json.dumps(news))

    if news:
        for article in news:
            if article['lang'] != 'en':
                continue

            dt = datetime.utcfromtimestamp(article['datetime']/1000).strftime('%d %b, %Y %H:%M %Z')
            st.markdown(f"### {article['headline']}")
            st.write(dt)
            st.write(f"{article['summary']}")
            st.markdown(f"Read more at [{article['source']}]({article['url']})")
            st.image(f"{article['image']}", width=300, use_column_width=True)
    else:
        st.markdown(f'### Sorry, looks like there is no news for {coin}')
