
import requests
import time
import classes as classes
from binance.spot import Spot as Client
import common as common

import time
def sendMessage(message: str):
    try:
        r = requests.post(f"http://127.0.0.1:5000/sendMessage", json={'message': f"{message}\n"})
    except:
        pass
    

def getTimestamp(client: Client):
    try:
        timestamp = client.time()
    except:
        print("could not get timestamp")
        return(None, 1)
    return(timestamp, 0)


def currentPrice(client: Client, pairName):
    try:
        price = client.ticker_price(pairName)
    except:
        return(None, 1)
    price = float(price["price"])
    return(price, 0)


def getPairInfo(client: Client, pairTradeInfo: dict, tradeCoin: list, pairName=None):
    """
    функция отвечает за получения базовых значений класса TradeInfo (без цены)
    если передана переменная pairName - поиск только для этой переменной
    """
    notValid = False
    if pairName == None:

        try:
            info = client.exchange_info()
        except:
            return(None, 2)
    else:
        try:
            info = client.exchange_info(pairName)
            notValid = True
        except:
            return(pairTradeInfo, 1)
    for i in info["symbols"]:  
        if i["status"] != "BREAK" and i["quoteAsset"] in tradeCoin and "SPOT" in i["permissions"]:
            name = i["symbol"]
            baseAsset = i["baseAsset"]
            quoteAsset = i["quoteAsset"]

            pricePrecision = common.getSize(i["filters"][0]["minPrice"])
            qtyPrecision = common.getSize(i["filters"][1]["minQty"])
            pairPrice,err = currentPrice(client, name)
            if err:
                continue
            pairTradeInfo[name] = classes.TradeInfo(name, 0, pairPrice, 0, {time.time(): pairPrice}, 0, 0, 0, 0, 
                                                    baseAsset, quoteAsset, 0, 0, False, 
                                                    pricePrecision, qtyPrecision, 0)
        elif notValid:
            return(pairTradeInfo, 1)
    return(pairTradeInfo, 0)


def getAllPairsPrice(client: Client, commonInfo: classes.CommonInfo, pairTradeInfo: dict):
    symbols = []
    for key in pairTradeInfo.keys():
        symbols.append(key)
    try:
        prices = client.ticker_price(symbols=symbols)
    except:
        print("could not get info about price of all coins")
        return(pairTradeInfo, 1)

    for i in range(len(prices)):

        price = prices[i]

        pairInfo = pairTradeInfo.get(price["symbol"])
        if pairInfo == None:
            pairInfo, err = getPairInfo(client, pairTradeInfo, commonInfo.tradeCoin, price["symbol"])
            if err:
                continue

        # else:
        pairInfo.priceTimeDict[time.time()] = float(price["price"])
        pairInfo.pairPrice = float(price["price"])
        pairTradeInfo[price["symbol"]] = pairInfo
        # print(price["symbol"])
    # exit(0)
    return(pairTradeInfo, 0)




def orderDone(client: Client, pairInfo: classes.TradeInfo):
    try:
        info = client.get_orders(symbol=pairInfo.pairName, orderId=pairInfo.orederID, limit=1)
    except:
        print(f"Could not get info adout order {pairInfo.pairName} id {pairInfo.orederID}")
        return (None, 1)
    return(info, 0)
    

def buyOrSellMarket(client: Client, pairInfo: classes.TradeInfo, timestamp, command, type, price=None, timeInForce=None):
    try:
    
        if price != None and timeInForce != None:
            comm = "{:." + f"{pairInfo.sizeP}" + "f}"
            formatedPrice = comm.format(price)
            info = client.new_order(symbol=pairInfo.pairName, price=formatedPrice, quantity=pairInfo.quantity, side=command, type=type, timeInForce=timeInForce, timestamp=timestamp)
        else:
            info = client.new_order(symbol=pairInfo.pairName, quantity=pairInfo.quantity, side=command, type=type, timestamp=timestamp)
    except:
        print(f"buyOrSellMarket\tcould not {command} {pairInfo.pairName} in quantity {pairInfo.quantity}")
        return(None, 1)
    return(info, 0)



def getValueOfCoin(client: Client, tradeCoin, timestamp):
    try:
        info = client.user_asset(imestamp=timestamp)
    except:
        print(f"\nCould not get amount {tradeCoin} coins on account\n")
        return(None, 2)
    for i in info:
        if i["asset"] == tradeCoin:
            return(float(i["free"]), 0)
    print(f"\nTher is no asset {tradeCoin} coin\n{info}")
    return(None, 2)



def getInfoFromTicker24h(client: Client, commonInfo: classes.CommonInfo, pairName):
    try:
        info = client.ticker_24hr(pairName)
    except:
        print(f"could not get previos trades")
        return(False, 2)
    if float(info["quoteVolume"]) > commonInfo.minimumQuoteVolume:
        return(True, 0)
    return(False, 0)


def getTrades(client: Client, pairName):
    try:
        info = client.trades(pairName)
    except:
        print(f"could not get previos trades")
        return(None, 2)
    return(info, 0)



def closeOrder(client: Client, pairInfo: classes.TradeInfo, timestamp):
    try:
        info = client.cancel_order(symbol=pairInfo.pairName, timestamp=timestamp, orderId=pairInfo.orederID)
    except:
        print(f"could not cancel order {pairInfo.pairName}")
        return(None, 1)
    return(info, 0)

