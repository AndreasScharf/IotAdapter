#from gpiozero import MCP3008
from datetime import datetime
#import RPi.GPIO as GPIO
import subprocess
import socketio
import time
import json
import os


#Snap7
#import snap7
#from snap7.util import *
#from snap7.snap7types import *

sio = socketio.Client()
config_path = '/home/pi/Documents/IotAdapter/config.json'
config_path = './config.json'
router = '192.168.10.1'
socket_connected = False
def main():
  with open(config_path, 'r') as myfile:
    config = myfile.read()
  try:
    config = json.loads(config)
    print('File correct')
  except:
    print('File not correct')
    return
#
#  Connections aufbauen
#
  @sio.event
  def connect():
    print("I'm connected!")
    socket_connected = True

  @sio.event
  def connect_error():
    print("The connection failed!")
    socket_connected = False

  @sio.event
  def disconnect():
    print("I'm disconnected!")
    socket_connected = False

  while 1:
    if not has_network(config):
      print('no network')
      time.sleep(300) # damit ich 5 min zeit habe falls da a fehler ist
      os.system('sudo reboot')
      return

    if not socket_connected:
      try:
        sio.connect('http://localhost:5000')
        sio.emit('alive', {'mad': 'lel'})
      except:
        pass

    message = []
    for row in config['data']:
      if row['type'] == 'static':
        value = row['value']
      elif row['type'] == 'time':
        value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      elif row['type'] == 'S7':
        value = get_from_s7_db(row['ip'], row['db'], row['offset'], row['length'], row['datatype'])
      elif row['type'] == 'analog':
        value = get_from_analog(row['channel'], row['multi'])


      message.append({'name':row['name'], 'unit': row['unit'], 'value': value})


def has_network(config):
  return True

  myip = subprocess.getoutput('hostname -I').split('.')
  next_test_ip = config.split('.')
  if int(next_test_ip[3]) == 0xFF:
    return False
  elif (next_test_ip[:-1] == myip[:-1]).all():
    next_test_ip[3] = str(int(next_test_ip[3]) + 1)
    if (next_test_ip == myip).all():
        has_network({'ip': ''.join(next_test_ip, '.') })
  else:
    next_test_ip = myip[:-1].append('1')

  hostname = config['ip']
  response = os.system("ping -c 1 " + hostname)
  if response == 0:
    has_network({'ip': ''.join(next_test_ip, '.')[:-1] })
  else:
    return True

def get_from_s7_db(ip, db, offset, length, datatype):
  pass

def get_from_analog(channel, multi):
  return 0


if __name__ == '__main__':
    main()
