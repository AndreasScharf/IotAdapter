import serial
import time
import socket
import json
from datetime import datetime

ser = serial.Serial('/dev/ttyACM0', 9600, timeout = 1.0, rtscts = 0)

true = 1
time_to_send = 5 * 60
timer = 0;

ipAdress = '85.214.215.187'
port = 12000
first = ''
sec = ''
def builddata():
    data.append({"name": "MAD", "unit" : "", "value": "pflanze"})
    data.append({"name": "time", "unit" : "", "value": str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))})
    data.append({"name": "humidity", "unit" : "%", "value": str(first) })
    data.append({"name": "brightness", "unit" : "%", "value": str(sec) })
    return data

while  1:
  timer += 1
  ser.write("hello")
  read = ser.read(15)

  first = read[0: read.find(',')]
  sec = read[read.find(',')+1: len(read)]

  print first
  print sec
  time.sleep(1000);
  if(timer > time_to_send):
      gesendet = False
      while not gesendet:
          print('sending...')
          try:
              tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              tcp.connect((ipAdress, port))
              print(json.dumps(builddata()))
              tcp.send(bytes(json.dumps(builddata()), 'utf-8'))
              gesendet = True

          except:
              print('error')
              tcp.close()
          finally:
          	tcp.close()

      print('idle')
