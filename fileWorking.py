import os
import classes as classes


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
    if not "deltaTime" in env_vars:
        message += "do not have deltaTime\n"
    if not "searchingLen" in env_vars:
        message += "do not have searchingLen\n"
    if not "minimumQuoteVolume" in env_vars:
        message += "do not have minimumQuoteVolume\n"
    if not "maxTimeOfTrading" in env_vars:
        message += "do not have maxTimeOfTrading\n"
    if not "tradeCounter" in env_vars:
        message += "do not have tradeCounter\n"
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
    if data["deltaTime"] != commonInfo.deltaTime:
        before = commonInfo.deltaTime
        commonInfo.deltaTime = data["deltaTime"]
        print(f"moneyLimit has changed from {before} to {commonInfo.moneyLimit}")
    if data["searchingLen"] != commonInfo.searchingLen:
        before = commonInfo.searchingLen
        commonInfo.searchingLen = data["searchingLen"]
        print(f"searchingLen has changed from {before} to {commonInfo.searchingLen}")
    if data["minimumQuoteVolume"] != commonInfo.minimumQuoteVolume:
        before = commonInfo.minimumQuoteVolume
        commonInfo.minimumQuoteVolume = data["minimumQuoteVolume"]
        print(f"minimumQuoteVolume has changed from {before} to {commonInfo.minimumQuoteVolume}")
    if data["maxTimeOfTrading"] != commonInfo.maxTimeOfTrading:
        before = commonInfo.maxTimeOfTrading
        commonInfo.maxTimeOfTrading = data["maxTimeOfTrading"]
        print(f"maxTimeOfTrading has changed from {before} to {commonInfo.maxTimeOfTrading}")
    if data["tradeCounter"] != commonInfo.tradeCounter:
        before = commonInfo.tradeCounter
        commonInfo.tradeCounter = data["tradeCounter"]
        print(f"tradeCounter has changed from {before} to {commonInfo.tradeCounter}")
    return(commonInfo)

  

# TEST
def cleanFile(filaName):
    with open(filaName, "w") as file:
        file.write(f"")

# TEST
def writeToFile(filaName ,message):
    os.system(f"echo {message} >> {filaName}")
    os.system(f"echo '\n' >> {filaName}")


def ignorePairs(excludeFile, pairName):
    if not os.path.exists(excludeFile):
        return(False)
    with open(excludeFile) as f:
        lines = [line.rstrip() for line in f]
        if pairName in lines:
            return(True)
    return(False)

