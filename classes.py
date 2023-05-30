

class CommonInfo:
    def __init__(self, api_key, api_secret, growPercent: float, precentProfit: float, percentStopLoss: float, 
                tradeSumm: float, delimeter: int, tradeCoin: str, filaName: str, lossCounter: int, excludeFile: str, moneyLimit: float, pathToEnvFile: str, 
                changingTime, minTradeSum: float, minimumQuoteVolume: float, searchingLen: int, deltaTime: int, maxTimeOfTrading: int, tradeCounter: int) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.growPercent = growPercent
        self.precentProfit = precentProfit
        self.percentStopLoss = percentStopLoss
        self.tradeSumm = tradeSumm
        self.delimeter = delimeter
        self.tradeCoin = tradeCoin # ?
        self.filaName = filaName
        self.lossCounter = lossCounter
        self.excludeFile = excludeFile
        self.moneyLimit = moneyLimit
        self.pathToEnvFile = pathToEnvFile
        self.changingTime = changingTime
        self.minTradeSum = minTradeSum
        self.minimumQuoteVolume = minimumQuoteVolume
        self.searchingLen = searchingLen
        self.deltaTime = deltaTime
        self.maxTimeOfTrading = maxTimeOfTrading
        self.tradeCounter = tradeCounter
    


class AccountInfo:
    def __init__(self, mainCoinBalance) -> None:
        self.mainCoinBalance = mainCoinBalance

       

class TradeInfo:
    def __init__(self, pairName, minPrice: float, pairPrice: float, orederID: int, priceTimeDict: dict, openPrice: float, 
                profitPrice: float, stopLossPrice: float, quantity: float, baseAsset, quoteAsset, lossCounter: int,
                profitCounter: int, stopTrade, sizeP: int, sizeQ: int, tradeSumm: float) -> None:
        self.pairName = pairName
        self.minPrice = minPrice
        self.pairPrice = pairPrice
        self.orederID = orederID # обнулять
        self.priceTimeDict = priceTimeDict
        self.openPrice = openPrice # цена открытия # обнулять
        self.profitPrice = profitPrice # обнулять
        self.stopLossPrice = stopLossPrice # цена, при которой закрывать # обнулять
        self.quantity = quantity # обнулять
        self.baseAsset = baseAsset # возможно не используется
        self.quoteAsset = quoteAsset # возможно не используется
        self.lossCounter = lossCounter # обнулять
        self.profitCounter = profitCounter # обнулять
        self.stopTrade = stopTrade
        self.sizeP = sizeP # количество знаков после запятой для цены
        self.sizeQ = sizeQ # количество знаков после запятой для объема
        self.tradeSumm = tradeSumm # обнулять
        self.startTradeTime = 0
        self.tradeCounter = 0
        self.goodTrand = False
    

    def addProfit(self, profit):
        self.profit += profit

    def trimPriceTimeDict(self, delimeter):
        tmpArr = list(self.priceTimeDict)
        first = tmpArr[0]
        last = tmpArr[-1]
        deletedItems = int(last) - int(first)
        if deletedItems > delimeter:
            deletedItems -= delimeter
            for item in list(self.priceTimeDict.keys()):
                if deletedItems == 0:
                    break
                deletedItems -= 1
                self.priceTimeDict.pop(item)


    def findMinPrice(self):
        if len(self.priceTimeDict.values()) == 0:
            return(1)
        self.minPrice = min(self.priceTimeDict.values())
        return(0)
    
    def findMax(self):
        if len(self.priceTimeDict.values()) == 0:
            return(0)
        return(max(self.priceTimeDict.values()))

    def cleanPriceTimeDict(self):
        self.priceTimeDict.clear()

