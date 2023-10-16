#from gpiozero import MCP3008
from datetime import datetime
import uuid
#from gpiozero import MCP3008
import RPi.GPIO as GPIO
from gpiozero import CPUTemperature
import subprocess
import socketio
from mqtt_cloud_connector import connector
import time
import json
import os
import socket
import struct

import _thread
from pythonping import ping

import grundfossensor as gfs

#Hannes
from modbus import rs485 
from INA219 import current_sensor

from rotators import rotator
from openvpn_handler import vpnclient as ovpnclient

import sys
import math
import psutil
import platform
import andiDB



from s7 import s7  
  


current_milli_time = lambda: int(round(time.time() * 1000))


sio = socketio.Client()
mqtt_con = connector()
s7 = s7()
cpu = CPUTemperature()

vpn_client = None
GPIO.setmode(GPIO.BCM)

#Arbeiten Hannes (Modbus, INA219)
myrs485 = rs485()

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
s7.debug = debug

totalizers = {}
new_totalizers = True

rotators = []
outputs = []

ov = 0


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
  socket_events(config)
  mqtt_events(config)

  global sending_intervall

  mad = ''
  for line in config['data']:
    if(line['name'] == 'mad' or line['name'] == 'MAD'):
      mad = line['value']
      break
    
  if 'sending_intervall' in config:
    sending_intervall = int(config['sending_intervall'])
  
  mqtt_con.mad = mad
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
      elif row['type'] == 'andiDB' or row['type'] == 'andiDBWrite':
        if not 'client' in andidb_objects:
          if not 'ip' in row:
            row['ip'] = '127.0.0.1'
          if not 'port' in row:
            row['port'] = 1337

          print('connect client')
        if row['type'] == 'andiDBWrite':#only go furthure if READ Object
          continue
        
        andidb_objects[row['table'] + ' ' +  row['name']] = andiDB.value( row['table'], row['name'] )
        
      elif row['type'] == 'gpio_in':
        GPIO.setup(int(row['offset']), GPIO.IN)
      elif row['type'] == 'totalizer':
        if not row['name'] in totalizers:
          totalizers[row['name']] = 0
          print('new: ', row['name'])
      elif row['type'] == 'rotator':
        if not row['name'] in totalizers:
          totalizers[row['name']] = float(row['start'])

        rotor = rotator( 
          pin=int(row['pin']),
          value=float(row['impulse']),
          start_totalizer=float(totalizers[row['name']]),
          zero_time=float(row['zero_time'] if 'zero_time' in row else 50000),
          name=row['name']
        )
        if debug:
          print('new rotator')
        rotators.append(rotor)
        if debug:
          print(rotators) 
      elif row['type'] == 'current_sensor':
        row['index'] = len(current_sensors)
        sensor = current_sensor(
            min=float(row['min']) if 'min' in row else 4,
            max=float(row['max']) if 'max' in row else 20,
            offset=int(row['offset']) if 'offset' in row else 0,
            cutoff=int(row['cutoff']) if 'cutoff' in row else 0)
        
        sensor.debug = debug
        current_sensors.append(sensor)
          
  if 'router' in config:
    
    from monvpn import vpnclient
    global vpn_client
    vpn_client = vpnclient()

    router = config['router']
    print('try register router')
    if 'vpn_allowed' in router and router['vpn_allowed'] and 'ip' in router and 'user' in router and 'pw' in router:
      vpn_client.register(router['ip'], router['user'], router['pw'])

  
  if 'openvpn' in config:
    global ov
    ov = ovpnclient(path='/home/pi/Documents/IotAdapter/openvpn_handler/config.ovpn')        
  
  if not os.path.isdir(offline_data_path):
    os.makedirs(offline_data_path)


  if len(totalizers):
    f = open(totalizers_path, 'w+')
    f.write(json.dumps(totalizers))
    f.close()

  last_round = current_milli_time()
  try:
    if('ip' in config and 'port' in config):
      sio.connect('http://' + config['ip'] + ':' + str(config['port']))
      sio.socket_connected = True
    elif 'domain' in config and 'https' in config['domain']:
      sio.connect(config['domain'])
      sio.socket_connected = True
    elif 'domain' in config and 'mqtt' in config['domain']:
      temp_str = config['domain'].replace('mqtt://', '')
      domain = temp_str.split(':')[0]
      port = temp_str.split(':')[1]
      mqtt_con.connect(domain, int(port))
      time.sleep(5)#give time to connect
  except KeyboardInterrupt:
    raise

  last_send_time = 0
  while 1:
    message = []
    
    its_time_to_send = (current_milli_time() - last_send_time) > (sending_intervall * 1000)

    #read inputs
    for row in config['data']:
      if 'not_active' in row:
          continue
      if 'active' in row and not row['active']:
        continue
          
      if row['type'] == 'static':
        value = row['value']
      elif row['type'] == 'time':
        value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      elif row['type'] == 's7' or row['type'] == 'S7' or row['type'] == 's7get':
        if 'channels' in config:
          value = s7.get(row['ip'], row['db'], row['offset'], row['length'], row['datatype'], config['channels'][row['ip']])
        else:
          value = s7.get(row['ip'], row['db'], row['offset'], row['length'], row['datatype'])
          
      elif row['type'] == 'analog':
        value = get_from_analog(row['channel'], row['multi'], row['offset'])
      elif row['type'] == 'gfs':
        value = get_from_gfs(row['sensor_id'], row['value_type'])
      elif row['type'] == 's7set' or row['type'] == 'andiDBWrite':
        continue
      elif row['type'] == 'andiDB':
        if row['table'] + ' ' +  row['name'] in andidb_objects:
          try:
            value = andidb_objects[row['table'] + ' ' +  row['name']].get()
          except:
            if debug:
              print('Error With', row['table'] + ' ' + row['name'])
        else:
          print('Error', row['table'], row['name'])
      elif row['type'] == 'rs485get':
        value = myrs485.get(port=row['port'], adress=row['adress'], baudrate=row['baudrate'], register=row['register'], code=row['code'],more=0) 
      elif row['type'] == 'gpio_in':
        if 'invert' in row and row['invert']:
          value = not GPIO.input(int(row['offset']))
        else:
          value = GPIO.input(int(row['offset']))
      elif row['type'] == 'totalizer':
        my_value = next((x for x in config['data'] if x['name'] == row['source_name']), None)
        if my_value and 'value' in my_value:
          totalizers[row['name']] = float(totalizers[row['name']]) +  ( float(my_value['value']) * (current_milli_time() - last_round) / (float(row['time_offset']) if 'time_offset' in row else 1))
          value = totalizers[row['name']]
      elif row['type'] == 'current_sensor':

          sensor = [x for x in current_sensors if x.offset==row['offset']]
          if(len(sensor)):
            messurement = row['messurement'] if 'messurement' in row else 'mA'
            value = sensor[0].get(messurement)
          elif len(sensor) and 'datatype' in sensor[0] and sensor['datatype'] == 'bool':
            value = int(sensor[0].getDigital(5))
          else:
            print('no sensor with offset', int(row['offset']))
          
          
          if debug:
            print('read ina value', value)
      
      elif row['type'] == 'cpu_temp':
        value = cpu.temperature
      elif row['type'] == 'cpu_usage':
        value = psutil.cpu_percent()
      elif row['type'] == 'memory_usage':
        value = psutil.virtual_memory()[2]
        
      elif row['type'] == 'rotator':
          r = [x for x in rotators if x.name == row['name']][0]
          if not r:
            print(r) 
            return
          value = r.get_flow(current_milli_time() - last_round)
          last_total = r.totalizer
          now_total = r.get_totalizer()
          if not last_total == now_total:
              message.append({'name':row['name'] + "_amount", 'unit': unit.split('/')[0] if '/' in unit else '', 'value': now_total})
          if debug:
            print(row['name'], value, now_total)
            
      unit = ''

      if 'unit' in row:
        unit = row['unit']

      if not (row['type'] == 'static' or row['type'] == 'time'):
        if 'lastdata' in row and (row['lastdata'] == value or not its_time_to_send): 
          #if debug:
          #  print(value, row['lastdata'], row['name'], 'sending_time', (last_round - last_send_time), sending_intervall)
          continue
        else:
          row['lastdata'] = value

      #if debug:
      #  print(row['name'] , value)
      
      if not value == 'Error':
        message.append({'name':row['name'], 'unit': unit, 'value': value})
        row['value'] = value

    
    #set outputs
    for item in outputs:
        if item['type'] == 's7set' and 'value' in item and 'execute' in item and item['execute']:
          if debug:
            print('execute', item)
            
          s7.set(item['ip'], item['db'], item['offset'], item['length'], item['datatype'], item['value'], item['channel'] if 'channel' in item else 1)#write value with valueset     
          item['execute'] = False
          
          mqtt_con.confirminputs([item['key']])
          time.sleep(1)

   
    last_round = current_milli_time()

    
    
    if (not its_time_to_send) and len(message) <= 2:
        continue


    if sio.socket_connected:
      if(len(message) <= 2): #nicht sendend net genug daten
          #if debug:
          #  print('not sending')
          continue
      if debug:
        print(message)
      global sending_realtime
      if sending_realtime:
          sio.emit('recv_data_mon3', (message, 0))
      else:
          sio.emit('recv_data', (message, 0))
      last_send_time = current_milli_time()
      if debug:
            print('send socket')

    elif mqtt_con.connected:
      if(len(message) <= 2): #nicht sendend net genug daten
        #if debug:
        #  print('not sending')
        continue 
      mqtt_con.senddata(message)
      last_send_time = current_milli_time()
      #if debug:
      #    print('send mqtt', message)
    else:
      #if debug:
      #  print('save data in', offline_data_path + '/' + datetime.today().strftime('%Y-%m-%d').replace('-', '_') + '.json')
      if(len(message) <= 2):  # nicht sendend net genug daten
          #if debug:
          #  print('no need to save no relevace')
          continue
      f = open(offline_data_path + '/' + datetime.today().strftime('%Y-%m-%d').replace('-', '_') + '.json', 'a')
      for row in message:
        f.write(json.dumps(row) + '\n')

      f.close()
      last_send_time = current_milli_time()
      if debug:
        print('save file')
    
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

def socket_events(config):
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


shellCMDTread = None


def executeShellCMD(cmd):
  editor = False
  filename = ''
  sudo = False
  if "nano" in cmd or 'sudo nano' in cmd:
    cmd = cmd.replace('nano', 'cat')
    sudo = 'sudo ' in cmd
    filename = cmd.replace('cat ', '').replace('sudo ', '')
    editor = True
  
  print(cmd)
  stream = os.popen(cmd)
  output = stream.read()

  mqtt_con.shell_response({ 'res' : output, 'editor': editor, 'filename': filename, 'sudo': sudo})


def mqtt_events(config):

    def connected_handler():
      outputs.clear()
         
      for row in config['data']:
        if (row['type'] == 's7set') and row['from'] == 'cloud':
            row['key'] = str(uuid.uuid4()).replace('-', '_')
            row['execute'] = True
            outputs.append(row)
        elif (row['type'] == 'andiDBWrite') and row['from'] == 'cloud':
            key = str(uuid.uuid4()).replace('-', '_')
            row['key'] = key
            row['execute'] = True
            
            andidb_objects[key] = andiDB.value(row['table'], row['name'])
            outputs.append(row)
        if len(outputs):
          if debug:
            print(outputs)
            
          mqtt_con.setupinputs(outputs)
          
      interprete_offline_data()

    mqtt_con.on_connected = connected_handler

    def recievedata_handler(payload):
      msg = json.loads(payload.decode('utf-8'))
      #go throug message
      
      print('recieve handler', msg)
      for row in msg:
        key = row['key']
        # find matching valueset to key
        matches = [x for x in outputs if x['key'] == key]
        if len(matches):
          match = matches[0]
          if debug:
            print(match)
          if match['type'] == 's7set':
            match['value'] = row['value']
            match['execute'] = True
          elif match['type'] == 'andiDBWrite':
            if key in andidb_objects:
              andidb_objects[key].set(float(row['value']))
            elif debug:
              print('no matching value')
              
    mqtt_con.on_recievedata = recievedata_handler


    def disconnect_handler():
      while not mqtt_con.connected:
        time.sleep(5)

        if debug:
          print('reconnecting, is connected: ', mqtt_con.connected)
        if not mqtt_con.connected:
          mqtt_con.connect(mqtt_con.host, mqtt_con.port, True)
          

    mqtt_con.on_disconnected = disconnect_handler
    
    global vpn_client
    def start_vpn(data):
      
      port = data['port'] if 'port' in data else -1
      root_ca = data['root_ca']
      client_ca = data['client_ca']
      client_crt = data['client_crt']
      ta_key = data['ta_key']
      
      if ((not vpn_client) or port == -1 or not vpn_client.registerd) and not ov:
        return
      print('start vpn on Port: ', port)

      if ov:
        ov.create_config(ca=root_ca, key=client_ca, cert=client_crt, tls=ta_key, port = port)
        ov.start_vpn()
        mqtt_con.vpnstarted(data['auth'])

        return

      try:
        vpn_client.start(port, root_ca, client_ca, client_crt, ta_key)
        print('success')
        mqtt_con.vpnstarted(data['auth'])
      except:
        print('vpn failed')
    mqtt_con.on_startvpn = start_vpn
    
    def stop_vpn():
      if ov:
        ov.stop_vpn()
        return
      
      try:
        vpn_client.stop()
      except:
        pass
    mqtt_con.on_stopvpn = stop_vpn
    
    def start_realtime():
      global sending_intervall
      sending_intervall = 1
    mqtt_con.on_start_realtime = start_realtime
        
    def stop_realtime():
      global sending_intervall
      if 'sending_intervall' in config:
        sending_intervall = int(config['sending_intervall'])
      else:
        sending_intervall = 300
        
    mqtt_con.on_stop_realtime = stop_realtime
    
    def reconfig(data):
      
      
      pass
        
    mqtt_con.on_reconfig_system = reconfig
    
    # handler for shell commands
    def on_shell_cmd(data):
      cmd =  data['cmd']
      
      
      _thread.start_new_thread(executeShellCMD, (cmd,))
      
      
      
    
    mqtt_con.on_shell_cmd = on_shell_cmd




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
def get_from_gfs(sensor_id, value_type):
    global grundfossensors
    sensor = [elem for elem in grundfossensors if elem.sensor_id == int(sensor_id)][0]

    if value_type=='temp':
        return sensor.get_tempratur()
    elif value_type=='press':
        return sensor.get_pessure()
    elif value_type=='flow':
        return sensor.get_flow()




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
    if sio.connected:
      length_of_messages = len(messages)
      for i, message in enumerate(messages):
        if len(message) > 2:  
          try:
            sio.emit('recv_data_mon3', (message, length_of_messages - i))
            f.close()
            noError = noError and True
          except:
            noError = False
    elif mqtt_con.connected:
        mqtt_con.sendofflinedata(messages)
    
    if noError:
      os.remove(offline_data_path + '/' + file)


if __name__ == '__main__':
    main()
