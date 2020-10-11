from django.core.management.base import BaseCommand, CommandError
from contract.models import Tradepair
import ccxt
import json
import time

config = json.load(open('config_funding.json'))
binance_future = ccxt.binance(config["binance_future"])
binance_future.load_markets()
binance_spot = ccxt.binance(config["binance_spot"])
binance_spot.load_markets()

okex_future = ccxt.okex(config["okex_future"])
okex_spot = ccxt.okex(config["okex_spot"])
okex_future.load_markets()
okex_spot.load_markets()

swapusd = []
swapusdt = []
swap = []

for symbol in okex_future.markets:
    if "USD-SWAP" in symbol:
        swapusd.append(symbol)
    if "USDT-SWAP" in symbol:
        swapusdt.append(symbol)

swap = swapusd + swapusdt

class Command(BaseCommand):
    def handle(self, *args, **options):
        while True:
            update_okex_info()
            update_binance_info()
            time.sleep(60)


def get_okex_spread_close(symbol, future, spot):
    try:
        if "USDT-SWAP" in symbol:
            spot_symbol = symbol.replace('-USDT-SWAP', '/USDT')
        else:
            spot_symbol = symbol.replace('-USD-SWAP', '/USDT')
        order_book_A = future.fetch_order_book(symbol)
        bid0_A = order_book_A['bids'][0][0]
        ask0_A = order_book_A['asks'][0][0]
        order_book_B = spot.fetch_order_book(spot_symbol)
        bid0_B = order_book_B['bids'][0][0]
        ask0_B = order_book_B['asks'][0][0]
    except Exception as err:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), symbol, err)
        return (0,0,0,0)
        pass

    return (((bid0_A - ask0_B)/ask0_B*100), ((bid0_B - ask0_A)/ask0_A*100), bid0_A, bid0_B)


def get_spread_close(symbol, future, spot):
    try:
        order_book_A = future.fetch_order_book(symbol)
        bid0_A = order_book_A['bids'][0][0]
        ask0_A = order_book_A['asks'][0][0]
        order_book_B = spot.fetch_order_book(symbol)
        bid0_B = order_book_B['bids'][0][0]
        ask0_B = order_book_B['asks'][0][0]
    except Exception as err:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), symbol, err)
        return (0,0,0,0)
        pass
    return (((bid0_A - ask0_B)/ask0_B*100), ((bid0_B - ask0_A)/ask0_A*100), bid0_A, bid0_B)


def update_okex_info():
    try:
        for i in swap:
            fundingRate = okex_future.swapGetInstrumentsInstrumentIdFundingTime({'instrument_id': i})
            spread = get_okex_spread_close(i, okex_future, okex_spot)
            result = Tradepair.objects.filter(symbol=i, exchange="okex")
            if result.exists():
                print(i, "QuerySet has Data")
                tradepair = Tradepair.objects.get(symbol=i, exchange="okex")
            else:
                print(i, "QuerySet empty")
                tradepair = Tradepair()
            tradepair.symbol = i
            tradepair.futureprice = spread[2]
            tradepair.spotprice = spread[3]
            tradepair.exchange = "okex"
            tradepair.fundRate = float("%.2f" % (float(fundingRate['estimated_rate']) * 100))
            tradepair.sellSpread = float('%.3f' % spread[0])
            tradepair.buySpread = float('%.3f' % spread[1])
            if abs(tradepair.fundRate) <= 0.08 and tradepair.buySpread < 0.5 and tradepair.sellSpread < 0.5:
                if result.exists():
                    tradepair.delete()
                continue
            tradepair.save()
            print(i)

    except Exception as err:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "update okex fail", err)
        pass


def update_binance_info():
    try:
        fundingRate = binance_future.fapiPublicGetPremiumIndex()
        for i in fundingRate:
            result = Tradepair.objects.filter(symbol=i['symbol'], exchange="binance")
            if result.exists():
                #print("QuerySet has Data")
                tradepair = Tradepair.objects.get(symbol=i['symbol'], exchange="binance")
            else:
                #print("QuerySet empty")
                tradepair = Tradepair()
            spread = get_spread_close(i['symbol'].replace('USDT', '/USDT'), binance_future, binance_spot)
            tradepair.symbol = i['symbol']
            tradepair.futureprice = spread[2]
            tradepair.spotprice = spread[3]
            tradepair.exchange = "binance"
            tradepair.fundRate = float("%.2f" % (float(i['lastFundingRate']) * 100))
            tradepair.sellSpread = float('%.3f' % spread[0])
            tradepair.buySpread = float('%.3f' % spread[1])
            if abs(tradepair.fundRate) <= 0.01 and tradepair.buySpread < 0.3 and tradepair.sellSpread < 0.3:
                print(i['symbol'], "delete")
                if result.exists():
                    tradepair.delete()
                continue
            tradepair.save()
    except Exception as err:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), err)
        pass
        
