import datetime
import time
import requests
import math
import classes as classes
from binance.spot import Spot as Client
import os
from decimal import Decimal


def readFile(env_file):
    env_vars =  {}
    with open(env_file) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            key, value = line.strip().split(':', 1)
            if value[1:].isdigit():
                env_vars[key] = float(value[1:])
            else:
                env_vars[key] = value[1:]  
    return(env_vars)


def checkValues(env_vars: dict):
    message = ""
    if not "precentProfit" in env_vars:
        message += "do not have precentProfit\n"
    if not "percentStopLoss" in env_vars:
        message += "do not have percentStopLoss\n"
    if not "tradeSumm" in env_vars:
        message += "do not have tradeSumm\n"
    if not "delimeter" in env_vars:
        message += "do not have delimeter\n"
    if not "minimunQuoteVolume" in env_vars:
        message += "do not have minimunQuoteVolume\n"
    if not "minimunTradesCount" in env_vars:
        message += "do not have minimunTradesCount\n"
    if not "minimunTradesCount" in env_vars:
        message += "do not have minimunTradesCount\n"
    if not "filaName" in env_vars:
        message += "do not have filaName\n"
    if not "api_key" in env_vars:
        message += "do not have api_key\n"
    if not "api_secret" in env_vars:
        message += "do not have api_secret\n"
    if not "url" in env_vars:
        message += "do not have url\n"
    if not "port" in env_vars:
        message += "do not have port\n"
    if not "telegram_token" in env_vars:
        message += "do not have telegram_token\n"
    if not "chat_id" in env_vars:
        message += "do not have chat_id\n"
    if not "logFile" in env_vars:
        message += "do not have logFile\n"
    if not "lossCounter" in env_vars:
        message += "do not have lossCounter\n"
    return(message)


def calcPersent(currentValue: float, lastValue: float):
    return(round(float(currentValue  / lastValue - 1) * 100, 3))


def sendMessage(message: str):
    try:
        r = requests.post(f"http://127.0.0.1:5000/sendMessage", json={'message': f"{message}\n"})
    except:
        pass
    


def waitSomeTime(seconds = 0, minutes = 0):
    if seconds != 0:
        while (int(datetime.datetime.now().second) % seconds != 0):
            time.sleep(1)
    elif minutes != 0:
        while (int(datetime.datetime.now().minute) % minutes != 0):
            time.sleep(1)

# TEST
def writeToFile(filaName ,message):
    with open(filaName, "a") as file:
        file.write(f"{message}\n")

# TEST
def cleanFile(filaName):
    with open(filaName, "w") as file:
        file.write(f"")





def round_down(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier

def getSize(size):
    log = math.log10(float(size))
    if log < 0 : 
        log *= -1 
    return(int(log))

def checkIfEnoughtCoinsForTrade(depositCoins, tradeSumm):
    return(True if float(depositCoins) > float(tradeSumm) else False)


def zeroTmpVariables(pairInfo: classes.TradeInfo):
    pairInfo.orederID = 0
    pairInfo.openPrice = 0
    pairInfo.stopLossPrice = 0
    pairInfo.quantity = 0
    pairInfo.profitPrice = 0
    pairInfo.tradeSumm = 0
    return(pairInfo)


def currentPrice(client: Client, pairInfo: classes.TradeInfo):
    price = client.ticker_price(pairInfo.pairName)
    price = float(price["price"])
    return(price)


def initTradeInfo(pairName: str, pairPrice: float):
    pairInfo = classes.TradeInfo(pairName, pairPrice, 0, 0, {time.time(): pairPrice}, 0, 0, 0, 0, "", "", 0, 0, False, -1, -1, 0)
    return(pairInfo)



def getProfit(pairInfo: classes.TradeInfo):

    profit = (float(pairInfo.profitPrice) - float(pairInfo.openPrice)) * float(pairInfo.quantity)
    print(f"profitPrice - {pairInfo.profitPrice}, quantity - {pairInfo.quantity}, openPrice - {pairInfo.openPrice}, profit - {profit}")
    return(profit)


def getPairAndPrice(client: Client, commonInfo: classes.CommonInfo):
    info = client.ticker_24hr(type="MINI")
    dictWithInfo = {}
    for i in info:
        pairName = i["symbol"]
        if float(i["lastPrice"]) != 0 and ("USDT" in pairName) and (float(i["quoteVolume"]) > commonInfo.minimunQuoteVolume or float(i["count"]) < commonInfo.minimunTradesCount):
            dictWithInfo[pairName] = float(i["lastPrice"])
    return(dictWithInfo)


def orderDone(client: Client, pairInfo: classes.TradeInfo, timestamp):
    # info = client.get_orders(symbol=pairInfo.pairName)
    # currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    # for i in info:
    #     if int(i["orderId"]) == pairInfo.orederID:
    #         if i["status"] == "FILLED":
    #             message = f"{currentTime}\torder {pairInfo.orederID} of {pairInfo.pairName} done"
    #             writeToFile(filaName ,message)
    #             return(True)
    # return(False)
    info = client.get_orders(symbol=pairInfo.pairName, orderId=pairInfo.orederID, limit=1)
    return(info)
    

# def checkOrder(client: Client, pairName, timestamp):
#     info = client.get_open_orders(symbol=pairName, timestamp=timestamp)
#     if len(info)  > 0:
#         return(True)
#     return(False)


def buyOrSellMarket(client: Client, pairInfo: classes.TradeInfo, timestamp, command):
    info = client.new_order(symbol=pairInfo.pairName, quantity=pairInfo.quantity, side=command, type="MARKET", timestamp=timestamp)
    return(info)




# TODO
def getValueOfCoin(client: Client, tradeCoin, timestamp):
    info = client.user_asset(imestamp=timestamp)
    for i in info:
        if i["asset"] == tradeCoin:
            return(float(i["free"]))
    # TODO
    # обработать, если нет пары такой
    return(0)



# def correctValuesForTrade(pairInfo: classes.TradeInfo, precentProfit, percentStopLoss, tradeSumm, currentPrice, moneyLimit):
#     sizeQ = pairInfo.sizeQ
#     sizeP = pairInfo.sizeP
    
#     quantity = round_down(tradeSumm / currentPrice, sizeQ)
#     profitPrice = round_down(currentPrice * (100 + precentProfit) / 100, sizeP)
#     precentProfitValue = round(tradeSumm * precentProfit / 100, sizeP)


#     while round_down(round_down(profitPrice * quantity, 2) - tradeSumm, 2) < precentProfitValue and round_down(quantity * profitPrice * 0.9999, sizeP) <= tradeSumm:
#         precentProfit += 0.1
#         profitPrice = round_down(currentPrice * (100 + precentProfit) / 100, sizeP)

#     pairInfo.quantity = round_down(quantity, sizeQ)
#     if quantity * currentPrice > tradeSumm:
#         tradeSumm = quantity * currentPrice
#     pairInfo.profitPrice = float(profitPrice)
#     pairInfo.stopLossPrice = round_down(currentPrice * (100 - percentStopLoss) / 100, sizeP)
#     pairInfo.tradeSumm = round_down(tradeSumm, sizeP)

#     print(f"correctValuesForTrade\t{pairInfo.pairName}\ttradeSumm = {pairInfo.tradeSumm}\tprofitPrice = {pairInfo.profitPrice}\tquantity = {pairInfo.quantity}")
#     print(f"\t\t\tprobably profit = {round_down(pairInfo.quantity * (pairInfo.profitPrice - currentPrice), 2)}")

#     return(pairInfo)



def correctValuesForTrade(pairInfo: classes.TradeInfo, precentProfit, percentStopLoss, tradeSumm, currentPrice):
    
    profitPrice = round_down(currentPrice * (100 + precentProfit) / 100, pairInfo.sizeP)

    while round_down(round_down(profitPrice * pairInfo.quantity, 2) - tradeSumm, 2) < round(tradeSumm * precentProfit / 100, pairInfo.sizeP) and round_down(pairInfo.quantity * profitPrice * 0.9999, pairInfo.sizeP) <= tradeSumm:
        precentProfit += 0.1
        profitPrice = round_down(currentPrice * (100 + precentProfit) / 100, pairInfo.sizeP)

    pairInfo.profitPrice = profitPrice
    pairInfo.stopLossPrice = round_down(currentPrice * (100 - percentStopLoss) / 100, pairInfo.sizeP)
    pairInfo.tradeSumm = round_down(tradeSumm, pairInfo.sizeP)

    print(f"correctValuesForTrade\t{pairInfo.pairName}\ttradeSumm = {pairInfo.tradeSumm}\tprofitPrice = {pairInfo.profitPrice}\tquantity = {pairInfo.quantity}")
    print(f"\t\t\tprobably profit = {round_down(pairInfo.quantity * (pairInfo.profitPrice - currentPrice), 2)}")

    return(pairInfo)



def getAdditionInfoAboutPair(client: Client, pairInfo: classes.TradeInfo):
    info = client.exchange_info(pairInfo.pairName)
    for i in info["symbols"]:
        sizeP = i["filters"][0]["minPrice"]
        sizeQ = i["filters"][1]["minQty"]
        baseAsset = info["symbols"][0]["baseAsset"]
        quoteAsset = info["symbols"][0]["quoteAsset"]
    pairInfo.sizeP = getSize(sizeP)
    pairInfo.sizeQ = getSize(sizeQ)
    pairInfo.baseAsset = baseAsset
    pairInfo.quoteAsset = quoteAsset
    return(pairInfo)


def makeOrder(client: Client, pairInfo: classes.TradeInfo, commonInfo: classes.CommonInfo, accauntInfo: classes.AccountInfo, pairPrice: float, precentProfit: float, percentStopLoss: float, tradeSumm: float, timestamp):
    print(f"{pairInfo.pairName} start making order")
    if pairInfo.sizeP == -1 or pairInfo.sizeQ == -1:
        pairInfo = getAdditionInfoAboutPair(client, pairInfo)

    pairInfo.quantity = round_down(tradeSumm / pairPrice, pairInfo.sizeQ)
    timestamp = client.time()
    accauntInfo.mainCoinBalance -= pairInfo.tradeSumm

    print(f"start buying\nbuy {pairInfo.quantity} coins")
    info = buyOrSellMarket(client, pairInfo, timestamp, "BUY")
    print(f"BUY\t{info}")
    # qty': '15.00000000', 'commission'
    time.sleep(0.5)

    timestamp = client.time()
    pairInfo.openPrice = currentPrice(client, pairInfo)
    pairInfo.quantity = round_down(getValueOfCoin(client, pairInfo.baseAsset, timestamp), pairInfo.sizeQ)
    pairInfo = correctValuesForTrade(pairInfo, precentProfit, percentStopLoss, tradeSumm, pairInfo.openPrice)

    print(f"makeOrder {pairInfo.pairName} value for sale {pairInfo.quantity}")
    order = client.new_order(symbol=pairInfo.pairName, price=pairInfo.profitPrice, quantity=pairInfo.quantity, side="SELL", type="LIMIT", timeInForce="GTC", timestamp=timestamp)
    print(f"new_order\t{order}\n")
    pairInfo.orederID = int(order["orderId"])

    return(pairInfo, accauntInfo)


def stopLossOrder(client: Client, pairInfo: classes.TradeInfo, timestamp):
    
    info = client.cancel_order(symbol=pairInfo.pairName, timestamp=timestamp, orderId=pairInfo.orederID)
    time.sleep(0.8)
    print(f"cancel_order\t{info}")

    order = buyOrSellMarket(client, pairInfo, timestamp, "SELL")
    print(f"SELL\t{order}")
    return(order)


    
def makeFinalCalculations(pairInfo: classes.TradeInfo, info):

    print(info)
    # summ = round(float(info["origQty"]) * float(info["price"]), 2)
    summ = round(float(info["cummulativeQuoteQty"]), 2)
    print(f"summ\t{summ}")

    profit = round(summ - pairInfo.tradeSumm, 2)
    print(f"pairInfo.tradeSumm\t{pairInfo.tradeSumm}\nprofit\t{round(summ - pairInfo.tradeSumm, 2)}")

    pairInfo.profit += round(profit, 2)
    pairInfo = zeroTmpVariables(pairInfo)
    return(pairInfo, profit) # summ, profit - удалить, для тестов


def ignorePairs(excludeFile, pairName):
    if not os.path.exists(excludeFile):
        return(False)
    with open(excludeFile) as f:
        lines = [line.rstrip() for line in f]
        if pairName in lines:
            return(True)
    return(False)

