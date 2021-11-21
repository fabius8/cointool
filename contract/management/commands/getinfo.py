from django.core.management.base import BaseCommand, CommandError
from contract.models import Tradepair
import ccxt
import json
import time
import requests

config = json.load(open('config_funding.json'))
binance_future = ccxt.binance(config["binance_future"])
binance_future.load_markets()
binance_spot = ccxt.binance(config["binance_spot"])
binance_spot.load_markets()

okex_future = ccxt.okex(config["okex_future"])
okex_spot = ccxt.okex(config["okex_spot"])
okex_future.load_markets()
okex_spot.load_markets()

huobi_spot = ccxt.huobipro()
huobi_spot.load_markets()

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
        count = 0
        while True:
            count = count + 1
            update_huobi_info()
            update_okex_info()
            update_binance_info()
            time.sleep(5)
            if count/300 == 0:
                print("load....")
                binance_future.load_markets()
                binance_spot.load_markets()
                okex_future.load_markets()
                okex_spot.load_markets()
                huobi_spot.load_markets()





def get_okex_spread_close(symbol, future, spot):
    try:
        if "USDT-SWAP" in symbol:
            spot_symbol = symbol.replace('-USDT-SWAP', '/USDT')
        else:
            spot_symbol = symbol.replace('-USD-SWAP', '/USDT')
        bid0_A = 0
        ask0_A = 0
        bid0_B = 0
        ask0_B = 0
        order_book_A = future.fetch_order_book(symbol)
        bid0_A = order_book_A['bids'][0][0]
        ask0_A = order_book_A['asks'][0][0]
        order_book_B = spot.fetch_order_book(spot_symbol)
        bid0_B = order_book_B['bids'][0][0]
        ask0_B = order_book_B['asks'][0][0]
    except Exception as err:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), symbol, err)
        return (0, 0, bid0_A, bid0_B)
        pass

    return (((bid0_A - ask0_B)/ask0_B*100), ((bid0_B - ask0_A)/ask0_A*100), bid0_A, bid0_B)


def get_binance_spread_close(symbol, future, spot):
    try:
        bid0_A = 0
        ask0_A = 0
        bid0_B = 0
        ask0_B = 0
        order_book_A = future.fetch_order_book(symbol)
        bid0_A = order_book_A['bids'][0][0]
        ask0_A = order_book_A['asks'][0][0]
        if "SHIB" in symbol:
            bid0_A = bid0_A/1000
            ask0_A = ask0_A/1000
            order_book_B = spot.fetch_order_book("SHIB/USDT")
        else:
            order_book_B = spot.fetch_order_book(symbol)
        bid0_B = order_book_B['bids'][0][0]
        ask0_B = order_book_B['asks'][0][0]
    except Exception as err:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), symbol, err)
        return (0, 0, bid0_A, bid0_B)
        pass
    return (((bid0_A - ask0_B)/ask0_B*100), ((bid0_B - ask0_A)/ask0_A*100), bid0_A, bid0_B)



def update_okex_info():
    try:
        for i in swap:
            print(i, "start")
            fundingRate = okex_future.publicGetPublicFundingRate({'instId': i})
            spread = get_okex_spread_close(i, okex_future, okex_spot)
            result = Tradepair.objects.filter(symbol=i, exchange="okex")
            if result.exists():
                tradepair = Tradepair.objects.get(symbol=i, exchange="okex")
            else:
                tradepair = Tradepair()
            tradepair.symbol = i
            tradepair.futureprice = spread[2]
            tradepair.spotprice = spread[3]
            tradepair.exchange = "okex"
            tradepair.fundRate = float("%.2f" % (float(fundingRate['data'][0]['nextFundingRate']) * 100))
            tradepair.LastRate = float("%.2f" % (float(fundingRate['data'][0]['fundingRate']) * 100))
            tradepair.sellSpread = float('%.2f' % spread[0])
            tradepair.buySpread = float('%.2f' % spread[1])
            tradepair.save()
            print("OKEX:", i, "OK")

    except Exception as err:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "update okex fail", err)
        pass


def update_binance_info():
    try:
        fundingRate = binance_future.fapiPublicGetPremiumIndex()
        for i in fundingRate:
            print(i['symbol'], "start")
            result = Tradepair.objects.filter(symbol=i['symbol'], exchange="binance")
            if result.exists():
                tradepair = Tradepair.objects.get(symbol=i['symbol'], exchange="binance")
            else:
                tradepair = Tradepair()
            spread = get_binance_spread_close(i['symbol'].replace('USDT', '/USDT'), binance_future, binance_spot)
            tradepair.symbol = i['symbol']
            tradepair.futureprice = spread[2]
            tradepair.spotprice = spread[3]
            tradepair.exchange = "binance"
            tradepair.fundRate = float("%.2f" % (float(i['lastFundingRate']) * 100))
            tradepair.LastRate = 0
            tradepair.sellSpread = float('%.2f' % spread[0])
            tradepair.buySpread = float('%.2f' % spread[1])
            tradepair.save()
            print("binance:", i['symbol'], "OK")

    except Exception as err:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), err)
        pass


def get_huobi_spread_close(future_symbol, spot_symbol, spot):
    try:
        bid0_A = 0
        ask0_A = 0
        bid0_B = 0
        ask0_B = 0
        r = requests.get("https://api.hbdm.com/swap-ex/market/depth?contract_code=" + future_symbol + "&type=step0")
        bid0_A = r.json()['tick']['bids'][0][0]
        ask0_A = r.json()['tick']['asks'][0][0]
        order_book_B = spot.fetch_order_book(spot_symbol)
        bid0_B = order_book_B['bids'][0][0]
        ask0_B = order_book_B['asks'][0][0]
    except Exception as err:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), symbol, err)
        return (0, 0, bid0_A, bid0_B)
        pass

    return (((bid0_A - ask0_B)/ask0_B*100), ((bid0_B - ask0_A)/ask0_A*100), bid0_A, bid0_B)

def get_huobi_spread_close_linear(future_symbol, spot_symbol, spot):
    try:
        bid0_A = 0
        ask0_A = 0
        bid0_B = 0
        ask0_B = 0
        r = requests.get("https://api.hbdm.com/linear-swap-ex/market/depth?contract_code=" + future_symbol + "&type=step0")
        bid0_A = r.json()['tick']['bids'][0][0]
        ask0_A = r.json()['tick']['asks'][0][0]
        order_book_B = spot.fetch_order_book(spot_symbol)
        bid0_B = order_book_B['bids'][0][0]
        ask0_B = order_book_B['asks'][0][0]
    except Exception as err:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), symbol, err)
        return (0, 0, bid0_A, bid0_B)
        pass

    return (((bid0_A - ask0_B)/ask0_B*100), ((bid0_B - ask0_A)/ask0_A*100), bid0_A, bid0_B)




def update_huobi_info():
    try:
        r = requests.get("https://api.hbdm.com/swap-api/v1/swap_contract_info")
        for i in r.json()['data']:
            print(i['symbol'], "start")
            result = Tradepair.objects.filter(symbol=i['contract_code'], exchange="huobi")
            if result.exists():
                tradepair = Tradepair.objects.get(symbol=i['contract_code'], exchange="huobi")
            else:
                tradepair = Tradepair()
            j = requests.get("https://api.hbdm.com/swap-api/v1/swap_funding_rate?contract_code=" + i['contract_code'])
            spread = get_huobi_spread_close(i['contract_code'], i['contract_code'].replace('-USD', '/USDT'), huobi_spot)
            tradepair.symbol = i['contract_code']
            tradepair.futureprice = spread[2]
            tradepair.spotprice = spread[3]
            tradepair.exchange = "huobi"
            tradepair.fundRate = float("%.2f" % (float(j.json()['data']['estimated_rate']) * 100))
            tradepair.LastRate = float("%.2f" % (float(j.json()['data']['funding_rate']) * 100))
            tradepair.sellSpread = float('%.2f' % spread[0])
            tradepair.buySpread = float('%.2f' % spread[1])
            tradepair.save()
            print("huobi:", i['symbol'], "OK")

        r = requests.get("https://api.hbdm.com/linear-swap-api/v1/swap_contract_info")
        for i in r.json()['data']:
            print(i['symbol'], "start")
            result = Tradepair.objects.filter(symbol=i['contract_code'], exchange="huobi")
            if result.exists():
                tradepair = Tradepair.objects.get(symbol=i['contract_code'], exchange="huobi")
            else:
                tradepair = Tradepair()
            j = requests.get("https://api.hbdm.com/linear-swap-api/v1/swap_funding_rate?contract_code=" + i['contract_code'])
            spread = get_huobi_spread_close_linear(i['contract_code'], i['contract_code'].replace('-USDT', '/USDT'), huobi_spot)
            tradepair.symbol = i['contract_code']
            tradepair.futureprice = spread[2]
            tradepair.spotprice = spread[3]
            tradepair.exchange = "huobi"
            tradepair.fundRate = float("%.2f" % (float(j.json()['data']['estimated_rate']) * 100))
            tradepair.LastRate = float("%.2f" % (float(j.json()['data']['funding_rate']) * 100))
            tradepair.sellSpread = float('%.2f' % spread[0])
            tradepair.buySpread = float('%.2f' % spread[1])
            tradepair.save()
            print("huobi:", i['symbol'], "OK")


    except Exception as err:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), err)
        pass

        
