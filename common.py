import datetime
import time
import requests
import math
import classes_new as classes
from binance.spot import Spot as Client
import os
import decimal


def readFile(env_file):
    env_vars =  {}
    with open(env_file, encoding="utf8") as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            key, value = line.strip().split(':', 1)
            try:
                env_vars[key] = float(value[1:])
            except:
                if " " in value[1:]:
                    env_vars[key] = value[1:].split(" ")
                else:
                    env_vars[key] = value[1:]
    return(env_vars)


def checkValues(env_vars: dict):
    message = ""
    if not "growPercent" in env_vars:
        message += "do not have growPercent\n"
    if not "precentProfit" in env_vars:
        message += "do not have precentProfit\n"
    if not "percentStopLoss" in env_vars:
        message += "do not have percentStopLoss\n"
    if not "tradeSumm" in env_vars:
        message += "do not have tradeSumm\n"
    if not "delimeter" in env_vars:
        message += "do not have delimeter\n"
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
    if not "moneyLimit" in env_vars:
        message += "do not have moneyLimit\n"
    return(message)


def checkDiffInEnvFile(commonInfo: classes.CommonInfo, data):
    if data["growPercent"] != commonInfo.growPercent:
        before = commonInfo.growPercent
        commonInfo.growPercent = data["growPercent"]
        print(f"growPercent has changed from {before} to {commonInfo.growPercent}")
    if data["precentProfit"] != commonInfo.precentProfit:
        before = commonInfo.precentProfit
        commonInfo.precentProfit = data["precentProfit"]
        print(f"precentProfit has changed from {before} to {commonInfo.precentProfit}")
    if data["percentStopLoss"] != commonInfo.percentStopLoss:
        before = commonInfo.percentStopLoss
        commonInfo.percentStopLoss = data["percentStopLoss"]
        print(f"percentStopLoss has changed from {before} to {commonInfo.percentStopLoss}")
    if data["tradeSumm"] != commonInfo.tradeSumm:
        before = commonInfo.tradeSumm
        commonInfo.tradeSumm = data["tradeSumm"]
        print(f"tradeSumm has changed from {before} to {commonInfo.tradeSumm}")
    if data["delimeter"] != commonInfo.delimeter:
        before = commonInfo.delimeter
        commonInfo.delimeter = data["delimeter"]
        print(f"delimeter has changed from {before} to {commonInfo.delimeter}")
    if data["lossCounter"] != commonInfo.lossCounter:
        before = commonInfo.lossCounter
        commonInfo.lossCounter = data["lossCounter"]
        print(f"lossCounter has changed from {before} to {commonInfo.lossCounter}")
    if data["moneyLimit"] != commonInfo.moneyLimit:
        before = commonInfo.moneyLimit
        commonInfo.moneyLimit = data["moneyLimit"]
        print(f"moneyLimit has changed from {before} to {commonInfo.moneyLimit}")
    return(commonInfo)


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

# # TEST
# def writeToFile(filaName ,message):
#     with open(filaName, "a") as file:
#         file.write(f"{message}\n")

# TEST
def cleanFile(filaName):
    with open(filaName, "w") as file:
        file.write(f"")

# TEST
def writeToFile(filaName ,message):
    os.system(f"echo {message} >> {filaName}")
    os.system(f"echo '\n' >> {filaName}")

def calcPersent(currentValue: float, lastValue: float):
    if lastValue == 0:
        return(0, 1)
    return(round(float(currentValue  / lastValue - 1) * 100, 2), 0)


def round_down(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier


def getSize(size):
    log = math.log10(float(size))
    if log < 0 : 
        log *= -1 
    return(int(log))


def checkIfEnoughtCoinsForTrade(depositCoins, tradeSumm):
    return(True if float(depositCoins) >= float(tradeSumm) else False)


def zeroTmpVariables(pairInfo: classes.TradeInfo):
    pairInfo.orederID = 0
    pairInfo.openPrice = 0
    pairInfo.stopLossPrice = 0
    pairInfo.quantity = 0
    pairInfo.profitPrice = 0
    pairInfo.tradeSumm = 0
    return(pairInfo)


def currentPrice(client: Client, pairName):
    price = client.ticker_price(pairName)
    price = float(price["price"])
    return(price)


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

            pricePrecision = getSize(i["filters"][0]["minPrice"])
            qtyPrecision = getSize(i["filters"][1]["minQty"])
            pairPrice = currentPrice(client, name)
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


def correctValuesForTrade(pairInfo: classes.TradeInfo, commonInfo: classes.CommonInfo, tradeSumm):
    

    precentProfit = commonInfo.precentProfit
    profitPrice = round_down(pairInfo.openPrice * (100 + precentProfit) / 100, pairInfo.sizeP)
    while round_down(profitPrice * pairInfo.quantity * 0.9999 - tradeSumm * (1 + commonInfo.precentProfit / 100), pairInfo.sizeP) < 0:
        precentProfit += 1
        profitPrice = round_down(pairInfo.openPrice * (100 + precentProfit) / 100, pairInfo.sizeP)
        print(f"new sum = {precentProfit * pairInfo.quantity * 0.9999}, tradeSumm = {tradeSumm}, percent = {(1 + commonInfo.precentProfit / 100)} , tradeSumm with percent = {tradeSumm * (1 + commonInfo.precentProfit / 100)}")

    pairInfo.profitPrice = profitPrice
    pairInfo.stopLossPrice = round_down(pairInfo.openPrice * (100 - commonInfo.percentStopLoss) / 100, pairInfo.sizeP)
    pairInfo.tradeSumm = round_down(tradeSumm, pairInfo.sizeP)

    print(f"correctValuesForTrade\t{pairInfo.pairName}\ttradeSumm = {pairInfo.tradeSumm}\tprofitPrice = {pairInfo.profitPrice}\tquantity = {pairInfo.quantity}")
    print(f"\t\t\tprobably profit = {round_down(pairInfo.quantity * pairInfo.profitPrice - tradeSumm, 2)}")

    return(pairInfo)


def makeOrder(client: Client, pairInfo: classes.TradeInfo, commonInfo: classes.CommonInfo, tradeSumm: float, timestamp):
    pairInfo.pairPrice = currentPrice(client, pairInfo.pairName)
    pairInfo.quantity = round_down(tradeSumm / pairInfo.pairPrice, pairInfo.sizeQ)
    pairInfo.openPrice = pairInfo.pairPrice
    info, err = buyOrSellMarket(client, pairInfo, timestamp, "BUY", "MARKET")
    if err:
        print("could not buy")
        return(None, 1)
    print("BUY")
    print(info)
    time.sleep(0.8)

    baseAssetOnAccaunt, err = getValueOfCoin(client, pairInfo.baseAsset, timestamp)
    if err == 2:
        print("uncnown error with getting value")
        return(None, 3)
    pairInfo.quantity = round_down(baseAssetOnAccaunt, pairInfo.sizeQ)
    pairInfo = correctValuesForTrade(pairInfo, commonInfo, tradeSumm)
    
    order, err = buyOrSellMarket(client, pairInfo, timestamp, "SELL", "LIMIT", pairInfo.profitPrice, "GTC")
    if err:
        print("could not make order to sell")
        return(None, 2)
    
    print("MAKE ORDER")
    print(order)
    pairInfo.orederID = int(order["orderId"])
    
    return(pairInfo, 0)


def stopLossOrder(client: Client, pairInfo: classes.TradeInfo, timestamp):
    try:
        info = client.cancel_order(symbol=pairInfo.pairName, timestamp=timestamp, orderId=pairInfo.orederID)
    except:
        print(f"could not cancel order {pairInfo.pairName}")
        return(None, 1)
    time.sleep(0.8)
    print(f"cancel_order\t{info}")

    order, err = buyOrSellMarket(client, pairInfo, timestamp, "SELL", "MARKET")
    if err:
        print("could not sell")
        return(None, 1)
    print(f"SELL\t{order}")
    return(order, 0)


    
def makeFinalCalculations(pairInfo: classes.TradeInfo, info):
    print("makeFinalCalculations")
    summ = round(float(info["cummulativeQuoteQty"]), 2)
    profit = round(summ - pairInfo.tradeSumm, 2)
    print(f"summ\t\t=\t{summ}\ntradeSumm\t\t=\t{pairInfo.tradeSumm}\nprofit\t\t=\t{profit}")
    pairInfo = zeroTmpVariables(pairInfo)
    return(pairInfo, profit, summ)


def ignorePairs(excludeFile, pairName):
    if not os.path.exists(excludeFile):
        return(False)
    with open(excludeFile) as f:
        lines = [line.rstrip() for line in f]
        if pairName in lines:
            return(True)
    return(False)

