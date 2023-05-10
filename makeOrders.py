from binance.spot import Spot as Client
import time
import sys
import common_new as common
import classes_new as classes
import os



def continueToWork(commonInfo: classes.CommonInfo, pairInfo: classes.TradeInfo, pairsDict: dict):
    if common.ignorePairs(commonInfo.excludeFile, pairInfo.pairName):
        return(pairsDict, False)
    if pairInfo.lossCounter == commonInfo.lossCounter and not pairInfo.stopTrade:
        pairInfo.stopTrade = True
        common.sendMessage(f"{pairInfo.pairName}\tstop trading because of many stoplosses")
    if pairInfo.stopTrade:
        # обращение
        pairInfo.profitPrice = common.round_down(pairInfo.pairPrice * (100 + commonInfo.precentProfit) / 100, pairInfo.sizeP)
        if float(pairInfo.profitPrice) >= pairInfo.findMax():
            pairInfo.lossCounter -= 1
        elif float(pairInfo.profitPrice) <= pairInfo.minPrice:
            pairInfo.lossCounter += 1
        pairsDict[pairInfo.pairName] = pairInfo
        if pairInfo.lossCounter == 0:
            pairInfo.stopTrade = False
        else:
            return(pairsDict, False)
    return(pairsDict, True)


def getTradeSumm(commonInfo: classes.CommonInfo, accauntInfo: classes.AccountInfo, pairInfo: classes.TradeInfo):
    tradeSumm = commonInfo.tradeSumm
    if accauntInfo.mainCoinBalance < commonInfo.tradeSumm and accauntInfo.mainCoinBalance > commonInfo.minTradeSum:
        tradeSumm = accauntInfo.mainCoinBalance
        tradeSumm = common.round_down(tradeSumm, pairInfo.sizeP)
    return(tradeSumm)


def profitOrStopLossEnding(pairInfo: classes.TradeInfo, accauntInfo: classes.AccountInfo, info):
    pairInfo, profit, getBack = common.makeFinalCalculations(pairInfo, info)
    accauntInfo.mainCoinBalance += getBack
    print(f"valid to trade {accauntInfo.mainCoinBalance}")
    return(pairInfo, accauntInfo, profit)


def trade(commonInfo: classes.CommonInfo):

    client = Client(commonInfo.api_key, commonInfo.api_secret)
    timestamp = client.time()
    currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    tradeCoin, _ = common.getValueOfCoin(client, commonInfo.tradeCoin, timestamp)
    accauntInfo = classes.AccountInfo(tradeCoin)
    message = f"{currentTime}\t{commonInfo.tradeCoin} on account {accauntInfo.mainCoinBalance}"
    print(message)

    totalProfit = 0
    pairsDict = {}
    
    pairsDict, err = common.getPairInfo(client, pairsDict, commonInfo.tradeCoin)
    if err == 2:
        print("could not get info from server")
        exit(2)


     # получаем свободное количество монет
    moneyOnAccaunt = common.round_down(accauntInfo.mainCoinBalance, 2)
    accauntInfo.mainCoinBalance = moneyOnAccaunt if moneyOnAccaunt < commonInfo.moneyLimit else commonInfo.moneyLimit
    print(f"valid to trade {accauntInfo.mainCoinBalance}")

    common.cleanFile(commonInfo.filaName)

    while True:
        # получаем количество торгуемой монеты
        tradeCoinSumm, err = common.getValueOfCoin(client, commonInfo.tradeCoin, timestamp)
        if err:
            print("could not get money on account")
            time.sleep(3)
            continue
        
        # # проверяем изменения энв файла
        changingTime = os.stat(commonInfo.pathToEnvFile).st_mtime
        if changingTime != commonInfo.changingTime:
            commonInfo.changingTime = changingTime
            try:
                data = common.readFile(commonInfo.pathToEnvFile)
            except:
                continue
            oldMoneyLimit = commonInfo.moneyLimit
            commonInfo = common.checkDiffInEnvFile(commonInfo, data)
            if commonInfo.moneyLimit > oldMoneyLimit:
                accauntInfo.mainCoinBalance += commonInfo.moneyLimit - oldMoneyLimit 
        # проверяем, что сумма, которая используется для торгов не вышла за пределы лимита торгов
        if accauntInfo.mainCoinBalance > commonInfo.moneyLimit:
            accauntInfo.mainCoinBalance = commonInfo.moneyLimit



        client = Client(commonInfo.api_key, commonInfo.api_secret)
        pairsDict, err = common.getAllPairsPrice(client, commonInfo, pairsDict)
        if err:
            time.sleep(3)
            continue
            
        timestamp = client.time()
        for pairName in pairsDict.keys():
            pairInfo: classes.TradeInfo = pairsDict[pairName]
            pairsDict, couldWork = continueToWork(commonInfo, pairInfo, pairsDict)
            if not couldWork:
                continue

            pairInfo.priceTimeDict[time.time()] = pairInfo.pairPrice
            pairInfo.trimPriceTimeDict(commonInfo.delimeter)
            isEmpty = pairInfo.findMinPrice()
            if isEmpty:
                continue
            
            percent, zero = common.calcPersent(pairInfo.pairPrice, pairInfo.minPrice)
            if zero:
                pairsDict[pairInfo.pairName] = pairInfo
                continue

            if pairInfo.orederID != 0:
                # проверяем существующие ордера
                info, err = common.orderDone(client, pairInfo)
                if err:
                    pairsDict[pairInfo.pairName] = pairInfo
                    continue
                info = info[0]
                #  если ордер выполнен, считаем прибыль
                if info["status"] == "FILLED":
                    if pairInfo.lossCounter > 0:
                        pairInfo.lossCounter -= 1
                    print("\nPROFIT")
                    print(info)
                    pairInfo, accauntInfo, profit = profitOrStopLossEnding(pairInfo, accauntInfo, info)
                    totalProfit += profit
                    common.sendMessage(f"{'PROFIT': <15}{pairInfo.pairName}\ncurrent profit\t=\t{profit}$\ntotal profit\t=\t{totalProfit}")
                else:
                    # или, если цена ниже заданного лимита - продаем
                    currentPrice = common.currentPrice(client, pairInfo.pairName)
                    print(f"{pairInfo.pairName: <15}\tto stoploss = {round(pairInfo.quantity * (currentPrice - pairInfo.stopLossPrice), 2)}\t|\tto goal = {round(pairInfo.quantity * (pairInfo.profitPrice - currentPrice), 2)}\t\t|\tto zero = {round(pairInfo.quantity * (currentPrice - pairInfo.openPrice),2)}")
                    if currentPrice <= pairInfo.stopLossPrice:
                        pairInfo.lossCounter += 1
                        info, err = common.stopLossOrder(client, pairInfo, timestamp)
                        if err:
                            print(f"could not make stopploss operation {pairInfo.pairName}")
                            pairsDict[pairInfo.pairName] = pairInfo
                            continue
                        print(f"\nSTOPLOSS")
                        print(info)
                        pairInfo, accauntInfo, loss = profitOrStopLossEnding(pairInfo, accauntInfo, info)
                        totalProfit += loss
                        common.sendMessage(f"{'STOPLOSS': <15}{pairInfo.pairName}\ncurrent profit\t=\t{loss}$\ntotal profit\t=\t{totalProfit}")

            if pairInfo.orederID == 0 and percent > commonInfo.growPercent:
                # регулируем сумму торгов (если не хватает для установленного лимита, понижаем до разрешенного минимума)
                tradeSumm = getTradeSumm(commonInfo, accauntInfo, pairInfo)
                if common.checkIfEnoughtCoinsForTrade(tradeCoinSumm, accauntInfo.mainCoinBalance):
                    if common.checkIfEnoughtCoinsForTrade(accauntInfo.mainCoinBalance, tradeSumm):
                        localTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        print(f"{localTime}\n{pairInfo.pairName} start making order")
                        pairInfo, err = common.makeOrder(client, pairInfo, commonInfo, tradeSumm, timestamp)
                        if err == 1:
                            print(f"could not buy to make order")
                            continue
                        elif err == 2 or err == 3:
                            _, err = common.buyOrSellMarket(client, pairInfo, timestamp, "SELL", "MARKET")
                            if err:
                                print("could not sell")
                                continue
                        accauntInfo.mainCoinBalance -= pairInfo.tradeSumm
                        print(f"valid to trade {accauntInfo.mainCoinBalance}")
                else:
                    print(f"Do not enough {commonInfo.tradeCoin} coins on account")

            pairsDict[pairInfo.pairName] = pairInfo
        time.sleep(3)




if __name__ == "__main__":
    if len (sys.argv) > 1:
        pathToEnvFile = str(sys.argv[1])
        data = common.readFile(pathToEnvFile)
        errMessage = common.checkValues(data)
        if len(errMessage) > 0:
            print(errMessage)
            exit(2)
        changingTime = os.stat(pathToEnvFile).st_mtime
        commonInfo = classes.CommonInfo(data["api_key"], data["api_secret"], data["growPercent"],
                                        data["precentProfit"], 
                                        data["percentStopLoss"], data["tradeSumm"], data["delimeter"], 
                                        data["tradeCoin"], data["filaName"],
                                        data["lossCounter"], data["excludeFile"],
                                        data["moneyLimit"], pathToEnvFile, changingTime, data["minTradeSum"])
        common.cleanFile(commonInfo.filaName)
        trade(commonInfo)
    else:
        print("\ngive values file\n")


# client = Client(commonInfo.api_key, commonInfo.api_secret)

# pair = "KMDUSDT"
# timestamp = client.time()


# # info = client.exchange_info(pair)
# info = client.get_orders(symbol=pair, orderId=192104152, limit=1)
# # print(info)
# for i in info:
#     sum = float(i["cummulativeQuoteQty"])
#     print(i)
#     # print(i["status"])
# # 'FILLED orderId
# print(sum)





