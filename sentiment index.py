import websocket,pprint,json
import talib,math
from binance.client import Client
from binance.enums import *
import numpy as np
import config

SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"

API_KEY = config.API_KEY
API_SECRET = config.API_SECRET

TRADE_SYMBOL = 'ETHUSDT'

closes = []
Flag = 50
volumes = []
taker_buy_ratios = []

client = Client(API_KEY, API_SECRET)

def percentile(value,values = []):
  min_value = min(values)
  max_value = max(values)
  if value > max_value:
    return 100
  elif value < min_value:
    return 0
  else:
    return float((value - min_value) *100/(max_value - min_value))

def rearrange(value,values =[]):
  values.pop(0)
  values.append(float(value))
  return values

def weight_volume(volume):
    weight = 100/(1+math.exp(0.04*(volume-50)))
    return weight

def sentiment_model(close_idx,volume_idx,taker_buy_ratio_idx,Flag):
  calc_now = (close_idx+weight_volume(volume_idx)+taker_buy_ratio_idx)/(2.85)
  if volume_idx < 20:
    print("Extreme low volume!")
    return Flag + (calc_now-Flag)*0.5
  elif volume_idx > 80:
    print("Extreme high volume!")
    return Flag + (calc_now-Flag)*0.95
  else:
    return Flag + (calc_now-Flag)*0.7

def logistic_reg(num):
  return 100/(1+math.exp(-0.05*(num-50)))

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global closes, Flag, volumes, taker_buy_ratios

    json_message = json.loads(message)
    candle = json_message['k']

    is_candle_closed = candle['x']
    close = float(candle['c'])
    volume = float(candle['v'])
    taker_buy_ratio = float(candle['V'])/float(candle['v'])
    if is_candle_closed:
      print("The close price is {}".format(close))
      print("The volume is {} eth".format(volume))
      print("The taker buy ratio is {}".format(taker_buy_ratio))
      if len(closes) < 50:
        closes.append(float(close))
        volumes.append(float(volume))
        taker_buy_ratios.append(float(taker_buy_ratio))
      else:
        close_idx,volume_idx,taker_buy_ratio_idx = percentile(close,closes),percentile(volume,volumes),percentile(taker_buy_ratio,taker_buy_ratios)
        Flag = sentiment_model(close_idx,volume_idx,taker_buy_ratio_idx,Flag)
        closes = rearrange(close,closes)
        volumes = rearrange(volume,volumes)
        taker_buy_ratio_idx = rearrange(taker_buy_ratio,taker_buy_ratios)
        Flag_re = logistic_reg(Flag)
        print("The Market Sentiment index is {}".format(Flag_re))

def on_error(ws,error):
    print('error',error)

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close,
                            on_message=on_message, on_error=on_error)
ws.run_forever()
