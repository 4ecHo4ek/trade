from binance.spot import Spot as Client
import time
import sys
import common as common
import classes as classes
import fileWorking as fileWorking
import requestsFile as requestsFile
import os
import datetime



def continueToWork(commonInfo: classes.CommonInfo, pairInfo: classes.TradeInfo, pairsDict: dict):
    if fileWorking.ignorePairs(commonInfo.excludeFile, pairInfo.pairName):
        return(pairsDict, False)
    if pairInfo.lossCounter == commonInfo.lossCounter and not pairInfo.stopTrade:
        pairInfo.stopTrade = True
        requestsFile.sendMessage(f"{pairInfo.pairName}\tstop trading because of many stoplosses")
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



def trade(commonInfo: classes.CommonInfo):

    client = Client(commonInfo.api_key, commonInfo.api_secret)
    timestamp, err = requestsFile.getTimestamp(client)
    if err:
        exit(2)
    currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    tradeCoin, _ = requestsFile.getValueOfCoin(client, commonInfo.tradeCoin, timestamp)
    accauntInfo = classes.AccountInfo(tradeCoin)
    message = f"{currentTime}\t{commonInfo.tradeCoin} on account {accauntInfo.mainCoinBalance}"
    print(message)

    totalProfit = 0
    pairsDict = {}
    
    pairsDict, err = requestsFile.getPairInfo(client, pairsDict, commonInfo.tradeCoin)
    if err == 2:
        print("could not get info from server")
        exit(2)

    # dictPairAndPercent = {}
    listWithTradings = []


     # получаем свободное количество монет
    moneyOnAccaunt = common.round_down(accauntInfo.mainCoinBalance, 2)
    accauntInfo.mainCoinBalance = moneyOnAccaunt if moneyOnAccaunt < commonInfo.moneyLimit else commonInfo.moneyLimit
    print(f"valid to trade {accauntInfo.mainCoinBalance}")

    fileWorking.cleanFile(commonInfo.filaName)

    while True:

        dictPairAndPercent = {}

        if totalProfit < -10:
            print("\n\nTOO BAD")
            exit(2)

        # получаем количество торгуемой монеты
        tradeCoinSumm, err = requestsFile.getValueOfCoin(client, commonInfo.tradeCoin, timestamp)
        if err:
            print("could not get money on account")
            time.sleep(3)
            continue  
        # # проверяем изменения энв файла
        changingTime = os.stat(commonInfo.pathToEnvFile).st_mtime
        if changingTime != commonInfo.changingTime:
            commonInfo.changingTime = changingTime
            try:
                data = fileWorking.readFile(commonInfo.pathToEnvFile)
            except:
                continue
            oldMoneyLimit = commonInfo.moneyLimit
            commonInfo = fileWorking.checkDiffInEnvFile(commonInfo, data)
            if commonInfo.moneyLimit > oldMoneyLimit:
                accauntInfo.mainCoinBalance += commonInfo.moneyLimit - oldMoneyLimit 
        # проверяем, что сумма, которая используется для торгов не вышла за пределы лимита торгов
        if accauntInfo.mainCoinBalance > commonInfo.moneyLimit:
            accauntInfo.mainCoinBalance = commonInfo.moneyLimit
        client = Client(commonInfo.api_key, commonInfo.api_secret)
        pairsDict, err = requestsFile.getAllPairsPrice(client, commonInfo, pairsDict)
        if err:
            time.sleep(3)
            continue


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

            if percent > 0:
                dictPairAndPercent[pairInfo.pairName] = percent
                pairInfo.cleanPriceTimeDict()
                pairInfo.priceTimeDict[time.time()] = pairInfo.openPrice

            pairsDict[pairInfo.pairName] = pairInfo
        

        # print(listWithTradings)
        for pair in listWithTradings:
            pairInfo = pairsDict[pair]
            if pairInfo.orederID != 0:
                # проверяем существующие ордера
                info, err = requestsFile.orderDone(client, pairInfo)
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
                    pairInfo, accauntInfo, profit = common.profitOrStopLossEnding(pairInfo, accauntInfo, info)
                    totalProfit += profit

                    listWithTradings.remove(pairInfo.pairName)

                    requestsFile.sendMessage(f"{'PROFIT': <15}{pairInfo.pairName}\ncurrent profit\t=\t{profit}$\ntotal profit\t=\t{totalProfit}")
                else:
                    # или, если цена ниже заданного лимита - продаем
                    currentPrice, err = requestsFile.currentPrice(client, pairInfo.pairName)
                    if err:
                        print(f"could not get price before stopploss operation {pairInfo.pairName}")
                        pairsDict[pairInfo.pairName] = pairInfo
                        continue

                    if common.isLongTimeTrade(pairInfo, commonInfo) or currentPrice <= pairInfo.stopLossPrice:
                        pairInfo.goodTrand = False
                        if currentPrice <= pairInfo.stopLossPrice:
                            pairInfo.lossCounter += 1
                            reasonOfClosing = "STOPLOSS"
                        else:
                            reasonOfClosing = "TIME OUT"
                        print(f"\n{reasonOfClosing}")
                        timestamp, err = requestsFile.getTimestamp(client)
                        if err:
                            exit(2)
                        info, err = common.stopLossOrder(client, pairInfo, timestamp)
                        if err:
                            print(f"could not make stopploss operation {pairInfo.pairName}")
                            pairsDict[pairInfo.pairName] = pairInfo
                            continue
                        print(info)
                        pairInfo, accauntInfo, loss = common.profitOrStopLossEnding(pairInfo, accauntInfo, info)
                        totalProfit += loss

                        listWithTradings.remove(pairInfo.pairName)

                        requestsFile.sendMessage(f"{reasonOfClosing: <15}{pairInfo.pairName}\ncurrent profit\t=\t{loss}$\ntotal profit\t=\t{totalProfit}")
                pairsDict[pairInfo.pairName] = pairInfo

        if bool(dictPairAndPercent):
            sortedDictPairAndPercent = {k: v for k, v in sorted(dictPairAndPercent.items(), key=lambda item: item[1], reverse=True)}


            for pair in sortedDictPairAndPercent:
                pairInfo = pairsDict[pair]
                percent = sortedDictPairAndPercent[pairInfo.pairName]


                if pairInfo.orederID == 0 and percent > commonInfo.growPercent:
                    reachMinTradingSumm, err = requestsFile.getInfoFromTicker24h(client, commonInfo, pairInfo.pairName)
                    if err:
                        pairsDict[pairInfo.pairName] = pairInfo
                        continue
                    validFrequency, err = common.getPermitForTradingAcordingFrequency(client, pairInfo, commonInfo)
                    if err:
                        pairsDict[pairInfo.pairName] = pairInfo
                        continue
                    
                    # регулируем сумму торгов (если не хватает для установленного лимита, понижаем до разрешенного минимума)
                    tradeSumm = common.getTradeSumm(commonInfo, accauntInfo, pairInfo)
                    if common.checkIfEnoughtCoinsForTrade(tradeCoinSumm, accauntInfo.mainCoinBalance) and reachMinTradingSumm and validFrequency:
                        if common.checkIfEnoughtCoinsForTrade(accauntInfo.mainCoinBalance, tradeSumm):
                            if pairInfo.goodTrand:
                                pairInfo.tradeCounter = commonInfo.tradeCounter
                            else:
                                pairInfo.tradeCounter += 1
                            if pairInfo.tradeCounter == commonInfo.tradeCounter:
                                pairInfo.tradeCounter = 0
                                pairInfo.goodTrand = True
                                # вычисляем сумму профита
                                # если сумма профита достигнута - добавляем в счетчик
                                # если счетчик набирает нужное число - совершаем сделку, счетчик обнуляем

                                localTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                                print(f"{localTime}\n{pairInfo.pairName} start making order")
                                timestamp, err = requestsFile.getTimestamp(client)
                                if err:
                                    exit(2)
                                pairInfo, err = common.makeOrder(client, pairInfo, commonInfo, tradeSumm, timestamp)
                                if err == 1:
                                    print(f"could not buy to make order")
                                    continue
                                elif err == 2 or err == 3:
                                    _, err = requestsFile.buyOrSellMarket(client, pairInfo, timestamp, "SELL", "MARKET")
                                    if err:
                                        print("could not sell")
                                        continue
                                pairInfo.startTradeTime = datetime.datetime.strptime(localTime, '%Y-%m-%d %H:%M:%S')   
                                accauntInfo.mainCoinBalance -= pairInfo.tradeSumm
                                print(f"valid to trade {accauntInfo.mainCoinBalance}")

                                listWithTradings.append(pairInfo.pairName)

                    pairsDict[pairInfo.pairName] = pairInfo


        time.sleep(3)




if __name__ == "__main__":
    if len (sys.argv) > 1:
        pathToEnvFile = str(sys.argv[1])
        data = fileWorking.readFile(pathToEnvFile)
        errMessage = fileWorking.checkValues(data)
        if len(errMessage) > 0:
            print(errMessage)
            exit(2)
        changingTime = os.stat(pathToEnvFile).st_mtime
        commonInfo = classes.CommonInfo(data["api_key"], data["api_secret"], data["growPercent"],
                                        data["precentProfit"], 
                                        data["percentStopLoss"], data["tradeSumm"], data["delimeter"], 
                                        data["tradeCoin"], data["filaName"],
                                        data["lossCounter"], data["excludeFile"],
                                        data["moneyLimit"], pathToEnvFile, changingTime, data["minTradeSum"],
                                        data["minimumQuoteVolume"], data["searchingLen"], data["deltaTime"],
                                        data["maxTimeOfTrading"], data["tradeCounter"])
        fileWorking.cleanFile(commonInfo.filaName)
        trade(commonInfo)
    else:
        print("\ngive values file\n")
