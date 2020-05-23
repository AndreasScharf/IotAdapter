#from gpiozero import MCP3008
from datetime import datetime
#import RPi.GPIO as GPIO
import subprocess
import socketio
import time
import json
import os


#Snap7
import snap7
from snap7.util import *
from snap7.snap7types import *

sio = socketio.Client()
s7 = snap7.client.Client()
cur_ip = ''
config_path = '/home/pi/Documents/IotAdapter/config.json'
config_path = './config.json'
router = '192.168.10.1'
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
  socket_connected = False
  @sio.event
  def connect():
    print("I'm connected!")
    global socket_connected
    socket_connected = True
    print('socket,', socket_connected)
    sio.emit('alive', {'mad': 'lel'})

  @sio.event
  def connect_error():
    print("The connection failed!")
    global socket_connected
    socket_connected = False

  @sio.event
  def disconnect():
    print("I'm disconnected!")
    global socket_connected
    socket_connected = False

  @sio.on('set_value')
  def set_value(data):
    for row in config['data']:
      if 'output' in row and data['valuename'] == row['name']:
        output = row['output']
        if 'min' in output and output['min'] > float(data['value']):
          #Value out of range
          error_code = 0x0F
          sio.emit('set_value_back', error_code)
          return
        elif 'max' in output and output['max'] < float(data['value']):
          #Value out of range
         error_code = 0x0F
         sio.emit('set_value_back', error_code)
         return
        else:
          pass
        ip = row['ip']
        db = row['db']
        offset = row['offset']
        datatype = row['datatype']



  while 1:
    if not has_network(config):
      print('no network')
      time.sleep(300) # damit ich 5 min zeit habe falls da a fehler ist
      os.system('sudo reboot')
      return

    if not socket_connected:
      try:
        sio.connect('http://' + config['ip'] + ':' + str(config['port']))
        socket_connected = True
      except KeyboardInterrupt:
        raise
      except:
        print('socket not connected')
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

      unit = ''
      if 'unit' in row:
        unit = row['unit']

      message.append({'name':row['name'], 'unit': unit, 'value': value})


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

def set_s7_db(ip, db, offset, length,datatype, value):
  if not cur_ip == ip:
    if s7.get_connected():
      s7.close()
    try:
      s7.connect(ip, 0, 1)
      cur_ip = ip
    except:
      error_code = 0x50
      sio.emit('set_value_back', error_code)
      print('CPU not avalible')
      return

  data = _bytearray(length)
  byte_index = int((offset - int(offset)) * 10)
  if datatype == 'bit':
      set_bool(data, byte_index, value, value)


  s7.db_write(db, offset, data)


def get_from_analog(channel, multi):
  return 0


if __name__ == '__main__':
    main()
