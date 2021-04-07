#from gpiozero import MCP3008
from datetime import datetime
from gpiozero import MCP3008
import RPi.GPIO as GPIO
import subprocess
import socketio
import time
import json
import os

import grundfossensor as gfs
import sys

import andiDB
import rs485 from modbus
#Snap7
import snap7
from snap7.util import *
from snap7.snap7types import *

current_milli_time = lambda: int(round(time.time() * 1000))
last_send_time = 0


sio = socketio.Client()
s7 = snap7.client.Client()
cur_ip = ''
config_path = '/home/pi/Documents/IotAdapter/config.json'
#config_path = './config.json'

offline_data_path = '/home/pi/Documents/IotAdapter/offlinedata.json'
#offline_data_path = './offlinedata.json'
router = '192.168.10.1'
grundfossensors = []

andidb_objects = {}
has_andidb_requests = False

sending_intervall = 300

req_name_intervall = 'recv_data'
req_name_realtime = 'recv_data_mon3'

sending_realtime = False
debug = ('-d' in sys.argv or '-debug' in sys.argv)

def main():
  f = open(config_path, 'r')
  config = f.read()
  f.close()
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
    mad = ''
    for line in config['data']:
        if(line['name'] == 'mad' or line['name'] == 'MAD'):
            mad = line['value']
            break

    sio.emit('alive', {'mad': mad})

    inputs = []

    for line in config['data']:
        if line['type'] == 's7set' and line['from'] == 'cloud':
            inputs.append(line)


    sio.emit('setup_inputs', {'inputs':inputs})
  @sio.event
  def connect_error(self):
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

    ip = data['ip']
    db = data['db']
    offset = data['offset']
    datatype = data['datatype']
    length = data['length']
    if debug:
        print('set_s7_db', ip, db, offset, length, datatype, float(data['value']) )

    set_s7_db(ip, db, offset, length, datatype, float(data['value']))
    if data['remote_source'] == 'control_button' and float(data['value']):
      time.sleep(0.3)#set 300 miliseconds
      set_s7_db(ip, db, offset, length, datatype, 0.0)
      message = [
        {"name":"mad", "unit":"", "value":data['remote_mad']},
        {"name": "time", "unit":"", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
        {"name": data['remote_VN'], "unit": data['remote_unit'], "value":"0"}
      ]
      sio.emit('recv_data_mon3', message)


  @sio.on('alive_realtime')
  def alive_realtime(data):
      global sending_realtime
      global sending_intervall

      sending_realtime = data['send_realtime']
      if sending_realtime :
        sending_intervall = 0.03
      else:
        sending_intervall = 300


  @sio.on('reboot_rpi')
  def reboot_rpi():
      os.system('sudo reboot')

  #setup
  #grunfossensor/andidb setup
  global grundfossensors
  for row in config['data']:
      if row['type'] == 'gfs':
          sensor = gfs.grundfossensor(
            barcode=row['barcode'],
            sensor_id=int(row['sensor_id']),
            type=row['sensor_type']
          )
          grundfossensors.append(sensor)
      elif row['type'] == 'andidb':
        if not 'client ' in andidb_objects:
          if not 'ip' in row:
            row['ip'] = '127.0.0.1'
          if not 'port' in row:
            row['port'] = 1337

          andidb_objects['client'] = andiDB.client(row['ip'], row['port']) 
          andidb_objects['values'] = []

        andidb_objects[row['table'] + ' ' +  row['name']].append(
            andiDB.value(andidb_objects['client'],  row['table'], row['name'], ))


  while 1:
    if not has_network(config):
      print('no network')
      time.sleep(300) # damit ich 5 min zeit habe falls da a fehler ist
      os.system('sudo reboot')
      return

    message = []
    if not socket_connected:
      try:
        if('ip' in config and 'port' in config):
            sio.connect('http://' + config['ip'] + ':' + str(config['port']))
            socket_connected = True
        elif 'domain' in config:
            sio.connect(config['domain'])
            socket_connected = True

      except KeyboardInterrupt:
        raise
      except Exception as e:

        print('socket not connected', e)
        global last_send_time
        if (current_milli_time() - last_send_time) < sending_intervall * 1000:
            continue
    else:
      pass

    global last_send_time
    if (current_milli_time() - last_send_time) < (sending_intervall * 1000):
        continue
    last_send_time = current_milli_time()

#    print('has Network, has socket', socket_connected, ', is realtime', sending_realtime)

    for row in config['data']:
      if 'not_active' in row:
          continue

      if row['type'] == 'static':
        value = row['value']
      elif row['type'] == 'time':
        value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      elif row['type'] == 's7' or row['type'] == 'S7' or row['type'] == 's7get':
        value = get_from_s7_db(row['ip'], row['db'], row['offset'], row['length'], row['datatype'])
      elif row['type'] == 'analog':
        value = get_from_analog(row['channel'], row['multi'], row['offset'])
      elif row['type'] == 'gfs':
        value = get_from_gfs(row['sensor_id'], row['value_type'])
      elif row['type'] == 's7set':
        continue
      elif row['type'] == 'andiDB':
        if row['table'] + ' ' +  row['name'] in andidb_objects:
          value = andidb_objects[row['table'] + ' ' +  row['name']].get()
        else:
          print('Error', row['table'], row['name'])
      elif row['type'] == 'rs485get':
        value = rs485.get() #hier musst du noch deine parameter mit "row['parametername']" übergeben
      
      unit = ''

      if 'unit' in row:
        unit = row['unit']

      if not (row['type'] == 'static' or row['type'] == 'time'):
        if 'lastdata' in row and row['lastdata'] == value:
          continue
        else:
          row['lastdata'] = value
          if debug:
            print(value)

      if not value == 'Error':
        message.append({'name':row['name'], 'unit': unit, 'value': value})

   

    if socket_connected:
      if(len(message) <= 2): #nicht sendend net genug daten
          if debug:
            print('not sending')
          continue
      if debug:
        print(message)
      global sending_realtime
      if sending_realtime:
          sio.emit('recv_data_mon3', message)
      else:
          sio.emit('recv_data', message)
    else:
      f = open(offline_data_path, 'a')
      for row in message:
        f.write(json.dumps(row) + '\n')
      f.close()

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
  global cur_ip

  if not cur_ip == ip:
    try:
      s7.connect(ip, 0, 1)
      cur_ip = ip
    except:
      error_code = 0x50
      sio.emit('set_value_back', error_code)
      print('CPU not avalible')
      return 'Error'
  try:
      data = s7.db_read(int(db), int(offset), int(length))
  except Exception as e:
      print('DB Error, Offset Error, Security Error', e)
      return 'Error'
  byte_index = int((float(offset) - int(offset)) * 10)
  value = 0.0

  if datatype=='bit':
    return get_bool(data, byte_index, 0)
  elif datatype=='word' or datatype=='byte':
    return get_int(data, 0)
  elif datatype=='dint':
    return get_dint(data, 0)
  elif datatype=='real':
    return get_real(data, 0)
  else:
    return -1
def set_s7_db(ip, db, offset, length, datatype, value):
  global cur_ip

  if not cur_ip or not cur_ip == ip:
    try:
      s7.connect(ip, 0, 1)
      cur_ip = ip
    except:
      error_code = 0x50
      sio.emit('set_value_back', error_code)
      print('CPU not avalible')
      return


  data = bytearray(int(length) + 1)

  if datatype == 'bit':
      byte_index = int((offset - int(offset)) * 10)
      set_bool(data, byte_index, value, value)
      data = data[:-1]
  elif datatype == 'real':
      set_real(data, 0, float(value))
      data = (data[:-1])

  s7.db_write(int(db), int(offset), data)

def get_from_analog(channel, multi, offset):
    adc = MCP3008(channel=channel)
    vol = adc.value * 3.3 * multi
    return  vol + offset
def get_from_mysql(id):
    pass
def get_from_gfs(sensor_id, value_type):
    global grundfossensors
    sensor = [elem for elem in grundfossensors if elem.sensor_id == int(sensor_id)][0]

    if value_type=='temp':
        return sensor.get_tempratur()
    elif value_type=='press':
        return sensor.get_pessure()
    elif value_type=='flow':
        return sensor.get_flow()


def get_dint(_bytearray, byte_index):
    data = _bytearray[byte_index:byte_index + 4]
    dint = struct.unpack('>i', struct.pack('4B', *data))[0]
    return dint
if __name__ == '__main__':
    main()
