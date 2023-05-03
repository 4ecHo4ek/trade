from binance.spot import Spot as Client
import time
import sys
import common as common
import classes as classes
import os


def trade(commonInfo: classes.CommonInfo):

    client = Client(commonInfo.api_key, commonInfo.api_secret)
        # обращение
    timestamp = client.time()
    currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    accauntInfo = classes.AccountInfo(common.getValueOfCoin(client, commonInfo.tradeCoin, timestamp))
    message = f"{currentTime}\t{commonInfo.tradeCoin} on account {accauntInfo.mainCoinBalance}"
    print(message)

    totalProfit = 0
    pairTradeInfo = {}
    client = None
    while True:
        # проверяем изменения энв файла
        changingTime = os.stat(commonInfo.pathToEnvFile).st_mtime
        if changingTime != commonInfo.changingTime:
            commonInfo.changingTime = changingTime
            data = common.readFile(commonInfo.pathToEnvFile)
            commonInfo = common.checkDiffInEnvFile(commonInfo, data)


        client = Client(commonInfo.api_key, commonInfo.api_secret)
        pairsDict = common.getPairAndPrice(client, commonInfo)

        for pairName in pairsDict:
            pairPrice = pairsDict[pairName]
            if not pairName in pairTradeInfo:
                pairTradeInfo[pairName] = common.initTradeInfo(pairName, pairPrice)
                continue
            pairInfo: classes.TradeInfo = pairTradeInfo[pairName]

            # блок обработки постоянного падения цены
            if common.ignorePairs(commonInfo.excludeFile, pairName):
                continue
            if pairInfo.lossCounter == commonInfo.lossCounter and not pairInfo.stopTrade:
                pairInfo.stopTrade = True
            if pairInfo.stopTrade:
                # обращение
                pairInfo.profitPrice = common.round_down(pairPrice * (100 + commonInfo.precentProfit) / 100, pairInfo.sizeP)
                # pairInfo, _, _ = common.calculations(client, pairInfo, pairPrice, commonInfo.precentProfit, commonInfo.percentStopLoss, commonInfo.tradeSumm)
                if float(pairInfo.profitPrice) >= pairInfo.findMax():
                    pairInfo.lossCounter -= 1
                elif float(pairInfo.profitPrice) <= pairInfo.minPrice:
                    pairInfo.lossCounter += 1
                pairTradeInfo[pairInfo.pairName] = pairInfo
                if pairInfo.lossCounter == 0:
                    pairInfo.stopTrade = False
                else:
                    continue


            pairInfo.priceTimeDict[time.time()] = pairPrice
            pairInfo.trimPriceTimeDict(commonInfo.delimeter)
            isEmpty = pairInfo.findMinPrice()

            if isEmpty:
                continue
            percent = common.calcPersent(pairPrice, pairInfo.minPrice)

            if percent > commonInfo.growPercent:
                # обращение
                # получаем свободное количество монет
                moneyOnAccaunt = common.round_down(common.getValueOfCoin(client, commonInfo.tradeCoin, timestamp), 2)
                accauntInfo.mainCoinBalance = moneyOnAccaunt if moneyOnAccaunt < commonInfo.moneyLimit else commonInfo.moneyLimit
                if pairInfo.orederID == 0 and common.checkIfEnoughtCoinsForTrade(accauntInfo.mainCoinBalance, commonInfo.tradeSumm):
                    try:
                        # обращение
                        pairInfo, accauntInfo = common.makeOrder(client, pairInfo, commonInfo, accauntInfo, pairPrice, commonInfo.precentProfit, commonInfo.percentStopLoss, commonInfo.tradeSumm, timestamp)
                        time.sleep(0.5)
                    except:
                        print(f"{pairInfo.pairName}, could not make order")
                        pairTradeInfo[pairInfo.pairName] = pairInfo
                        continue
                    # pairInfo, accauntInfo = common.makeOrder(client, pairInfo, commonInfo, accauntInfo, pairPrice, commonInfo.precentProfit, commonInfo.percentStopLoss, commonInfo.tradeSumm, timestamp)

            if pairInfo.orederID != 0:
                # обращение
                info = common.orderDone(client, pairInfo, timestamp)
                info = info[0]
                if info["status"] == "FILLED":
                    if pairInfo.lossCounter > 0:
                        pairInfo.lossCounter -= 1
                    print("\nPROFIT")
                    pairInfo, profit = common.makeFinalCalculations(pairInfo, info)
                    totalProfit += profit
                    common.sendMessage(f"{pairInfo.pairName}\ncurrent profit =\t{profit}$\npair profit =\t{round(pairInfo.profit, 2)}$")
                else:
                    print(f"{pairInfo.pairName: <15}\tto stoploss = {round(float(pairInfo.quantity) * (pairPrice - float(pairInfo.stopLossPrice)), 2)}\t|\tto goal = {round(float(pairInfo.quantity) * (float(pairInfo.profitPrice) - pairPrice), 2)}\t\t|\tto zero = {round(pairPrice - pairInfo.openPrice,2)}")
                    if pairPrice <= pairInfo.stopLossPrice:
                        pairInfo.lossCounter += 1
                        # обращение
                        info = common.stopLossOrder(client, pairInfo, timestamp)
                        time.sleep(0.5)
                        pairInfo, loss = common.makeFinalCalculations(pairInfo, info)
                        totalProfit += loss
                        moneyOnAccaunt = common.round_down(common.getValueOfCoin(client, commonInfo.tradeCoin, timestamp), 2)
                        accauntInfo.mainCoinBalance = moneyOnAccaunt if moneyOnAccaunt < commonInfo.moneyLimit else commonInfo.moneyLimit
                        common.sendMessage(f"{pairInfo.pairName}\ncurrent loss =\t{loss}$pair profit =\t{round(pairInfo.profit, 2)}$")

            pairTradeInfo[pairInfo.pairName] = pairInfo
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
                                        data["tradeCoin"], data["filaName"], data["minimunQuoteVolume"], 
                                        data["minimunTradesCount"], data["lossCounter"], data["excludeFile"],
                                        data["moneyLimit"], pathToEnvFile, changingTime)
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





