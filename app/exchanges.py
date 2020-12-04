import requests

from app         import app
from app.models  import Price

import app.constants as constants

def sync_binance_prices():
    app.logger.debug("Getting Binance Prices ...")

    exchange = "BINANCE"
    currency = "USD"
    stable_cryptocurrency = 'USDT'

    url      = 'https://api.binance.com/api/v3/ticker/price'
    response = requests.get(url)

    counter  = 0
    for item in response.json():
        symbol = item['symbol']
        current_price = float(item['price'])

        #only process currency based trades
        if not symbol.endswith(stable_cryptocurrency): continue

        counter = counter + 1
        cryptocurrency = symbol.replace(stable_cryptocurrency, "")

        update_price(exchange, currency, cryptocurrency, current_price)

    app.logger.debug("Done: {} cryptocurrencies proceseed".format(counter))

def sync_bitso_prices():
    app.logger.debug("Getting Bitso Prices ...")

    exchange = "BITSO"
    currency = "MXN"

    url      = 'https://api.bitso.com/v3/ticker'
    response = requests.get(url)

    counter  = 0
    for item in response.json()['payload']:
        symbol = item['book']
        current_price = float(item['last'])

        #only process currency based trades
        if not symbol.endswith("_" + currency.lower()): continue

        counter = counter + 1
        cryptocurrency = symbol.replace("_" + currency.lower(), "").upper()

        update_price(exchange, currency, cryptocurrency, current_price)

    app.logger.debug("Done: {} cryptocurrencies proceseed".format(counter))

def update_price(exchange, currency, cryptocurrency, current_price):
    price = Price.objects(exchange=exchange, currency=currency, cryptocurrency=cryptocurrency).first()

    if price:
        price.current_price = current_price
        price.save()
    else:
        price = Price(
            exchange       = exchange,
            currency       = currency,
            cryptocurrency = cryptocurrency,
            current_price  = current_price,
        ).save()

def get_current_price(exchange, currency, cryptocurrency):
    price = Price.objects(exchange=exchange, currency=currency, cryptocurrency=cryptocurrency).first()
    return price.current_price

def supported_cryptocurrencies(exchange=None):
    if exchange:
        cryptocurrencies = Price.objects(exchange=exchange).distinct(field="cryptocurrency")
    else:
        cryptocurrencies = Price.objects().distinct(field="cryptocurrency")

    if not cryptocurrencies:
        cryptocurrencies = [cryptocurrency for cryptocurrency in constants.CRYPTOCURRENCIES]

    return sorted(cryptocurrencies)

def supported_currencies(exchange=None):
    if exchange:
        currencies = Price.objects(exchange=exchange).distinct(field="currency")
    else:
        currencies = Price.objects().distinct(field="currency")

    if not currencies:
        currencies = [currency for currency in constants.CURRENCIES]

    return sorted(currencies)

def supported_cryptocurrencies_dict():
    cryptocurrencies = {}
    for exchange in constants.EXCHANGES:
        cryptocurrencies[exchange] = supported_cryptocurrencies(exchange=exchange)

    return cryptocurrencies

def supported_currencies_dict():
    currencies = {}
    for exchange in constants.EXCHANGES:
        currencies[exchange] = supported_currencies(exchange=exchange)

    return currencies
