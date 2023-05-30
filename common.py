import datetime
import time
import math
import classes as classes
from binance.spot import Spot as Client
import requestsFile as requestsFile



def waitSomeTime(seconds = 0, minutes = 0):
    if seconds != 0:
        while (int(datetime.datetime.now().second) % seconds != 0):
            time.sleep(1)
    elif minutes != 0:
        while (int(datetime.datetime.now().minute) % minutes != 0):
            time.sleep(1)


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
    pairInfo.startTradeTime = 0
    return(pairInfo)


def correctValuesForTrade(pairInfo: classes.TradeInfo, commonInfo: classes.CommonInfo, tradeSumm):
    

    precentProfit = commonInfo.precentProfit
    profitPrice = round_down(pairInfo.openPrice * (100 + precentProfit) / 100, pairInfo.sizeP)
    while round_down(profitPrice * pairInfo.quantity - tradeSumm * (1 + commonInfo.precentProfit / 100), pairInfo.sizeP) < 0:
        precentProfit += 1
        profitPrice = round_down(pairInfo.openPrice * (100 + precentProfit) / 100, pairInfo.sizeP)
       
    pairInfo.profitPrice = profitPrice
    pairInfo.stopLossPrice = round_down(pairInfo.openPrice * (100 - commonInfo.percentStopLoss) / 100, pairInfo.sizeP)
    pairInfo.tradeSumm = round_down(tradeSumm, pairInfo.sizeP)

    print(f"correctValuesForTrade\t{pairInfo.pairName}\ttradeSumm = {pairInfo.tradeSumm}\tprofitPrice = {pairInfo.profitPrice}\tquantity = {pairInfo.quantity}, profit summ = {tradeSumm * (1 + commonInfo.precentProfit / 100)}")
    print(f"\t\t\tprobably profit = {round_down(pairInfo.quantity * pairInfo.profitPrice - tradeSumm, 2)}")

    return(pairInfo)



def getBuyingQuantityAndSum(pairInfo: classes.TradeInfo, info):
    quantity = 0
    sum = 0
    for i in info["fills"]:
        quantity += float(i["qty"]) - float(i["commission"])
        sum += float(i["price"]) * (float(i["qty"]) - float(i["commission"]))
    quantity = round_down(quantity, pairInfo.sizeQ)
    sum = round_down(sum, 2)
    return(quantity, sum)


def makeOrder(client: Client, pairInfo: classes.TradeInfo, commonInfo: classes.CommonInfo, tradeSumm: float, timestamp):
    pairInfo.pairPrice, err = requestsFile.currentPrice(client, pairInfo.pairName)
    if err:
        print("could get price before buying")
        return(None, 1)
    pairInfo.quantity = round_down(tradeSumm / pairInfo.pairPrice, pairInfo.sizeQ)
    pairInfo.openPrice = pairInfo.pairPrice
    info, err = requestsFile.buyOrSellMarket(client, pairInfo, timestamp, "BUY", "MARKET")
    if err:
        print("could not buy")
        return(None, 1)
    print("BUY")
    print(info)
    pairInfo.quantity, pairInfo.tradeSumm = getBuyingQuantityAndSum(pairInfo, info)
    print(f"\npairInfo.quantity = {pairInfo.quantity}, pairInfo.tradeSumm = {pairInfo.tradeSumm}\n")
    # time.sleep(0.8)

    # baseAssetOnAccaunt, err = requestsFile.getValueOfCoin(client, pairInfo.baseAsset, timestamp)
    # if err == 2:
    #     print("unknown error with getting value")
    #     return(None, 3)
    # pairInfo.quantity = round_down(baseAssetOnAccaunt, pairInfo.sizeQ)
    pairInfo = correctValuesForTrade(pairInfo, commonInfo, tradeSumm)
    
    order, err = requestsFile.buyOrSellMarket(client, pairInfo, timestamp, "SELL", "LIMIT", pairInfo.profitPrice, "GTC")
    if err:
        print("could not make order to sell")
        return(None, 2)
    
    print("MAKE ORDER")
    print(order)
    pairInfo.orederID = int(order["orderId"])
    
    return(pairInfo, 0)


def stopLossOrder(client: Client, pairInfo: classes.TradeInfo, timestamp):
  
    info, err = requestsFile.closeOrder(client, pairInfo, timestamp)
    if err:
        return(None, 1)

    time.sleep(0.8)
    print(f"cancel_order\t{info}")

    order, err = requestsFile.buyOrSellMarket(client, pairInfo, timestamp, "SELL", "MARKET")
    if err:
        print("could not sell")
        return(None, 1)
    print(f"SELL\t{order}")
    return(order, 0)


    
def makeFinalCalculations(pairInfo: classes.TradeInfo, info):
    print("makeFinalCalculations")
    summ = round(float(info["cummulativeQuoteQty"]), 2)
    profit = round(summ - pairInfo.tradeSumm, 2)
    print(f"summ\t\t=\t{summ}\ntradeSumm\t=\t{pairInfo.tradeSumm}\nprofit\t\t=\t{profit}")
    pairInfo = zeroTmpVariables(pairInfo)
    return(pairInfo, profit, summ)



def getPermitForTradingAcordingFrequency(client: Client, pairInfo: classes.TradeInfo, commonInfo: classes.CommonInfo):
    deltaTime = commonInfo.deltaTime
    searchingLen = commonInfo.searchingLen

    dictOfTimes = {}
    delta = datetime.timedelta(seconds=deltaTime)
    info, err = requestsFile.getTrades(client, pairInfo.pairName)
    if err:
        return(False, 1)
    
    for i in info:
        time = datetime.datetime.fromtimestamp(int(i["time"])/1000).strftime('%Y-%m-%d %H:%M:%S')
        if time in dictOfTimes:
            dictOfTimes[time] = dictOfTimes[time] + 1
        else:
            dictOfTimes[time] = 0
        # print(i["id"], i["price"], i["qty"], i["quoteQty"], time)

    k = len(dictOfTimes) - searchingLen
    for i in list(dictOfTimes.keys()):
        if k > 0:
            dictOfTimes.pop(i)
        else:
            break
        k -= 1
    beginTime = datetime.datetime.strptime(list(dictOfTimes.keys())[0], '%Y-%m-%d %H:%M:%S')
    for i in range(1, len(dictOfTimes)):
        endTime = datetime.datetime.strptime(list(dictOfTimes.keys())[i], '%Y-%m-%d %H:%M:%S')
        if endTime - beginTime > delta:
            return(False, 1)
        beginTime = datetime.datetime.strptime(list(dictOfTimes.keys())[i], '%Y-%m-%d %H:%M:%S')
    return(True, 0)


def isLongTimeTrade(pairInfo: classes.TradeInfo, commonInfo: classes.CommonInfo):
    currentTime = datetime.datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), '%Y-%m-%d %H:%M:%S')
    return(currentTime - pairInfo.startTradeTime >= datetime.timedelta(seconds=commonInfo.maxTimeOfTrading))



def getTradeSumm(commonInfo: classes.CommonInfo, accauntInfo: classes.AccountInfo, pairInfo: classes.TradeInfo):
    tradeSumm = commonInfo.tradeSumm
    if accauntInfo.mainCoinBalance < commonInfo.tradeSumm and accauntInfo.mainCoinBalance > commonInfo.minTradeSum:
        tradeSumm = accauntInfo.mainCoinBalance
        tradeSumm = round_down(tradeSumm, pairInfo.sizeP)
    return(tradeSumm)


def profitOrStopLossEnding(pairInfo: classes.TradeInfo, accauntInfo: classes.AccountInfo, info):
    pairInfo, profit, getBack = makeFinalCalculations(pairInfo, info)
    accauntInfo.mainCoinBalance += getBack
    print(f"valid to trade {accauntInfo.mainCoinBalance}")
    return(pairInfo, accauntInfo, profit)


