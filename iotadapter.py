#from gpiozero import MCP3008
from datetime import datetime
#from gpiozero import MCP3008
import RPi.GPIO as GPIO
import subprocess
import socketio
import time
import json
import os
import socket
import struct
from pythonping import ping

import grundfossensor as gfs

#Hannes
from modbus import rs485 
from INA219 import current_sensor


import sys
import platform
import andiDB
#Snap7
import snap7
from snap7.util import *

if platform.python_version() <= '3.5':
  from snap7.snap7types import *



current_milli_time = lambda: int(round(time.time() * 1000))


sio = socketio.Client()
s7 = snap7.client.Client()


vpn_client = None
GPIO.setmode(GPIO.BCM)

#Arbeiten Hannes (Modbus, INA219)
myrs485 = rs485()
#mycurrentsensor = current_sensor()

current_sensors = []

reconnectingS7 = False
cur_ip = ''
config_path = '/home/pi/Documents/IotAdapter/config.json'
totalizers_path = '/home/pi/Documents/IotAdapter/totalizers.json'
#config_path = './config.json'

offline_data_path = '/home/pi/Documents/IotAdapter/offlinedata'
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

totalizers = {}
new_totalizers = True
try:
  f = open(totalizers_path, 'r')
  totalizers = json.loads(f.read())
  new_totalizers = False
  f.close()
except:
  f = open(totalizers_path, 'w+')
  f.write(json.dumps(totalizers))
  f.close()

def main():
  global last_send_time
  last_send_time = 0

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
  sio.socket_connected = False
  @sio.event
  def connect():
    print("I'm connected!")
    
    sio.socket_connected = True
    print('socket,', sio.socket_connected)
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
    
    if debug:
      print('start interpreting offline data')
    interprete_offline_data()


    sio.emit('setup_inputs', {'inputs':inputs})
  @sio.event
  def connect_error(self):
    print("The connection failed!")
    sio.socket_connected = False

    global sending_intervall
    sending_intervall = 300

  @sio.event
  def disconnect():
    
    print("I'm disconnected!")
    sio.socket_connected = False

    global sending_intervall
    sending_intervall = 300

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


  @sio.on('start_vpn')
  def start_vpn(data):
    port = data['port'] if 'port' in data else -1
    root_ca = data['root_ca']
    client_ca = data['client_ca']
    client_crt = data['client_crt']
    ta_key = data['ta_key']
    if (not vpn_client) or port == -1 or not vpn_client.registerd:
      return
    
    print('start vpn on Port: ', port)
    try:
      vpn_client.start(port, root_ca, client_ca, client_crt, ta_key)
      print('success')
    except:
      print('vpn failed')


  @sio.on('stop_vpn')
  def stop_vpn(data):
    try:
      vpn_client.stop()
    except:
      pass

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
      elif row['type'] == 'andiDB':
        if not 'client' in andidb_objects:
          if not 'ip' in row:
            row['ip'] = '127.0.0.1'
          if not 'port' in row:
            row['port'] = 1337

          print('connect client')
          andidb_objects['client'] = andiDB.client(row['ip'], int(row['port']))

        andidb_objects[row['table'] + ' ' +  row['name']] = andiDB.value(andidb_objects['client'],  row['table'], row['name'] )
        
      elif row['type'] == 'gpio_in':
        GPIO.setup(int(row['out']), GPIO.IN)
      elif row['type'] == 'totalizer':
        if not row['name'] in totalizers:
          totalizers[row['name']] = 0
          print('new: ', row['name'])
      elif row['type'] == 'rotator':
        if not row['name'] in totalizers:
          totalizers[row['name']] = float(row['start'])
      elif row['type'] == 'current_sensor':
        current_sensors.append(current_sensor(
          min=float(row['min']) if 'min' in row else 4, 
          max=float(row['max']) if 'max' in row else 20, 
          offset=int(row['offset']) if 'offset' in row else 0 ))
          
  if 'router' in config:
    
    from monvpn import vpnclient
    vpn_client = vpnclient()

    router = config['router']
    print('try register router')
    if 'vpn_allowed' in router and router['vpn_allowed'] and 'ip' in router and 'user' in router and 'pw' in router:
      vpn_client.register(router['ip'], router['user'], router['pw'])

  if not os.path.isdir(offline_data_path):
    os.makedirs(offline_data_path)


  if len(totalizers):
    f = open(totalizers_path, 'w+')
    f.write(json.dumps(totalizers))
    f.close()

  last_round = current_milli_time()
  while 1:
      
    message = []
    
    if not sio.socket_connected:
      try:
        if('ip' in config and 'port' in config):
            sio.connect('http://' + config['ip'] + ':' + str(config['port']))
            sio.socket_connected = True
        elif 'domain' in config:
            sio.connect(config['domain'])
            sio.socket_connected = True

      except KeyboardInterrupt:
        raise
      except Exception as e:
        sio.socket_connected = False

        print('socket not connected', e)
    else:
      pass
    
    its_time_to_send = (current_milli_time() - last_send_time) > (sending_intervall * 1000)
    #if debug and its_time_to_send:
    #  print('time to send [s] ', sending_intervall)

    for row in config['data']:
      if 'not_active' in row:
          continue

      if row['type'] == 'static':
        value = row['value']
      elif row['type'] == 'time':
        value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      elif row['type'] == 's7' or row['type'] == 'S7' or row['type'] == 's7get':
        if 'channels' in config:
          value = get_from_s7_db(row['ip'], row['db'], row['offset'], row['length'], row['datatype'], config['channels'][row['ip']])
        else:
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
        value = myrs485.get(port=row['port'], adress=row['adress'], baudrate=row['baudrate'], register=row['register'], code=row['code'],more=0) 
      elif row['type'] == 'gpio_in':
        value = GPIO.input(int(row['offset']))
      elif row['type'] == 'totalizer':
        my_value = next((x for x in config['data'] if x['name'] == row['source_name']), None)
        if my_value and 'value' in my_value:
          totalizers[row['name']] = float(totalizers[row['name']]) +  ( float(my_value['value']) * (current_milli_time() - last_round) / (float(row['time_offset']) if 'time_offset' in row else 1))
          value = totalizers[row['name']]
      elif row['type'] == 'current_sensor':
          sensor = [x for x in current_sensors if x.offset==row['offset']]
          if(len(sensor)):
            value = sensor[0].get()
          else:
            print('no sensor with offset', int(row['offset']))
          if debug:
              print('read ina value', value)
      
      unit = ''

      if 'unit' in row:
        unit = row['unit']

      if not (row['type'] == 'static' or row['type'] == 'time'):
        if 'lastdata' in row and (row['lastdata'] == value or not its_time_to_send): 
          continue
        else:
          row['lastdata'] = value
          if debug:
            print(value)

      if not value == 'Error':
        message.append({'name':row['name'], 'unit': unit, 'value': value})
        row['value'] = value

   
    last_round = current_milli_time()

    if (not its_time_to_send) and len(message) <= 2:
        continue

      

    if sio.socket_connected:
      if(len(message) <= 2): #nicht sendend net genug daten
          if debug:
            print('not sending')
          continue
      if debug:
        print(message)
      global sending_realtime
      if sending_realtime:
          sio.emit('recv_data_mon3', (message, 0))
      else:
          sio.emit('recv_data', (message, 0))
      last_send_time = current_milli_time()
      
    else:
      if debug:
        print('save data in', offline_data_path + '/' + datetime.today().strftime('%Y-%m-%d').replace('-', '_') + '.json')
      if(len(message) <= 2):  # nicht sendend net genug daten
          if debug:
            print('no need to save no relevace')
          continue
      f = open(offline_data_path + '/' + datetime.today().strftime('%Y-%m-%d').replace('-', '_') + '.json', 'a')
      for row in message:
        f.write(json.dumps(row) + '\n')

      f.close()
      last_send_time = current_milli_time()

    
    if len(totalizers):
      f = open(totalizers_path, 'w+')
      f.write(json.dumps(totalizers))
      f.close()


def check_network():
  gateway = get_default_gateway_linux()
  internet = False
  dns = False
  network = False
  try:
    for i in ping('cloud.enwatmon.de', verbose=False):
      internet = internet or i.success
      dns = dns or i.success

    for i in ping('8.8.8.8', verbose=False):
      internet = internet or i.success

    for i in ping(str(gateway), verbose=False):
      network = network or i.success  
      
  except:
    dns = False
    internet = False


  if not internet and network:
    restart_router(gateway)
  if not internet and not network:
    restart_rpi()
  
  return dns or internet and network
 

def get_default_gateway_linux():
    """Read the default gateway directly from /proc."""
    with open("/proc/net/route") as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                # If not default route or not RTF_GATEWAY, skip it
                continue

            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
def restart_router(router_ip):
  print('router not accessable', router_ip)

def restart_rpi():
   print('no network in 300s')
   time.sleep(300) # damit ich 5 min zeit habe falls da a fehler ist
   os.system('sudo reboot')



def get_from_s7_db(ip, db, offset, length, datatype, channel=1):
  global cur_ip
  global reconnectingS7
  global s7

  if reconnectingS7 or not cur_ip == ip :
    try:
      if s7:
        s7.destroy()

      s7 = snap7.client.Client()
      if debug:
        print('connecting to', ip, channel)
      s7.connect(ip, 0, channel)
      reconnectingS7 = False
      cur_ip = ip
    except:
      error_code = 0x50
      #sio.emit('set_value_back', error_code)
      
      reconnectingS7 = True
      print('CPU not avalible')
      return 'Error'
  try:
    data = s7.db_read(int(db), int(float(offset)), int(length) if not datatype=='bit' else 8)
  except Exception as e:
      print('DB Error, Offset Error, Security Error', e)
      #s7 in error mode 
      reconnectingS7 = True
      return 'Error'
  byte_index = 0
  if '.' in offset:
    byte_index = int(offset.split('.')[1])
  value = 0.0
  #print(offset, byte_index, len(data))

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


def interprete_offline_data():
  if not os.path.isdir(offline_data_path):
    return

  for file in os.listdir(offline_data_path):
    if debug:
      print('interpreting file:', file)

    messages = []
    message = []
    f = open(offline_data_path + '/' + file, 'r')
    for line in f.readlines():
      if not line.startswith('{'):
        continue
      conv_line = json.loads(line)
      if (conv_line['name'] == 'mad' or conv_line['name'] == 'MAD') and len(message):
        messages.append(message)
        message = []

      message.append(conv_line)

    messages.append(message)
    noError = True
    length_of_messages = len(messages)
    for i, message in enumerate(messages):
      if len(message) > 2:  
        try:
          sio.emit('recv_data_mon3', (message, length_of_messages - i))
          f.close()
          noError = noError and True
        except:
          noError = False
    if noError:
      os.remove(offline_data_path + '/' + file)


if __name__ == '__main__':
    main()
