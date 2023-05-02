from flask import Flask, request, jsonify
import telebot
# from twilio import twiml
import sys
import os
import subprocess
import common as common


app = Flask(__name__)
global telegram_token
global chat_id


@app.route('/sendMessage', methods=['POST']) 
def sendMessage():
    data = request.json
    message = data["message"]
    bot = telebot.TeleBot(telegram_token)
    bot.send_message(chat_id, message)
    return jsonify(data)


@app.route('/startTradeBot', methods=['POST']) 
def startTradeBot():
    data = request.json
    pairName = data["pairName"]

    subprocess.Popen([sys.executable, "test.py", pairName])

    return jsonify(data)


if __name__ == "__main__":
    
    if len (sys.argv) > 1:
        # telegram_token, chat_id = getDataFromFile(str(sys.argv[1]))
        data = common.readFile(str(sys.argv[1]))
        if not "telegram_token" in data:
            print(f"no telegram_token")
            exit(2)
        elif not "chat_id" in data:
            print(f"no chat_id")
            exit(2)
        telegram_token = data["telegram_token"]
        chat_id = data["chat_id"]
        app.run()
    else:
        print("\ngive values file\n")

# http://127.0.0.1:5000/sendMessage