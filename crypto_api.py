import json
import requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

INVALID_SYMBOL = 'Invalid value for "symbol"'

"""
@brief:     Class for getting news and price about the cryptocurrency
"""
class IEX:
    def __init__(self, token):
        """
        @brief:     Initialize class with base URL and token
        @param:     token - Token key for IEX Cloud API
        """
        self.BASE_URL = 'https://cloud.iexapis.com/stable'
        self.token = token

    def getCoinNews(self, coin, last=10):
        """
        @brief:     Request news of the cryptocurrency
        @param:     coin - coin to request information
        @param:     last - past x days to get news from
        @return:    JSON data with the cryptocurrency news on success,
                    Else None
        """
        url = f'{self.BASE_URL}/stock/{coin}/news/last/{last}?token={self.token}'
        resp = requests.get(url)
        if resp.status_code != 200:
            return None

        return resp.json()

    def getCryptoPrice(self, coin):
        """
        @brief:     Request price of the cryptocurrency.
        @param:     coin - coin to request information
        @return:    JSON data with the cryptocurrency price on success,
                    Else None
        """
        url = f'{self.BASE_URL}/crypto/{coin}/price?token={self.token}'
        resp = requests.get(url)
        if resp.status_code != 200:
            return None

        return resp.json()

"""
@brief:     Class for getting information about the cryptocurrency
"""
class CoinMarketCap:
    def __init__(self, token):
        """
        @brief:     Initialize class with base URL and
                    header (contains token)
        @param:     token - Token key for CoinMarketCap API
        """
        self.BASE_URL = 'https://pro-api.coinmarketcap.com/v1'
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': token,
        }

    def getCoinInfo(self, coin):
        """
        @brief:     Request general information of the cryptocurrency.
                    Information includes logo, description, and name
        @param:     coin - coin to request information
        @return:    True on success with cryptocurrency information,
                    Else false with error message
        """
        url = f'{self.BASE_URL}/cryptocurrency/info'
        parameters = {
            'symbol': coin,
            'aux': "logo,description"
        }

        session = requests.Session()
        session.headers.update(self.headers)

        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
            if data['status']['error_code'] == 0:
                return data, True

            msg = data['status']['error_message']
            if INVALID_SYMBOL == msg[:len(INVALID_SYMBOL)]:
               return f'{str.upper(coin)} not found... ' \
                      f'Check [coinmarketcap.com](https://coinmarketcap.com/coins/) '\
                      f'to see if coin spelled correct', False
            else:
                return 'Seems like we have ran into an error...', False
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            return e, False
