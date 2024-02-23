"""
GENERAL INFORMATION about Module
"""
__all__ = []
__version__ = '1.1.1'
__author__ = 'Andreas Scharf'

#from gpiozero import MCP3008
from datetime import datetime
import uuid
#from gpiozero import MCP3008
import RPi.GPIO as GPIO
from gpiozero import CPUTemperature
import subprocess
#import socketio
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

from rpi_system.network import get_mobil_usage

import sys
import math
import psutil
import platform
import andiDB

from s7 import s7  

current_milli_time = lambda: int(round(time.time() * 1000))

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

# debug flag 
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
  
  # check if offline folder exists
  # if not create one
  if not os.path.isdir(offline_data_path):
    os.makedirs(offline_data_path)


  if len(totalizers):
    f = open(totalizers_path, 'w+')
    f.write(json.dumps(totalizers))
    f.close()

  last_round = current_milli_time()
  try:
    # extract mqtt connection parameters and establish connection 
    if 'domain' in config and 'mqtt' in config['domain']:
        temp_str = config['domain'].replace('mqtt://', '')
        domain = temp_str.split(':')[0]
        port = temp_str.split(':')[1]
        mqtt_con.connect(domain, int(port))
        # give mqtt client time to connect to server
        time.sleep(5)
        
  except KeyboardInterrupt:
    raise

  if debug:
    print('Start Reading Loop')
    
  last_send_time = 0
  while 1:
    message = []
    
    its_time_to_send = (current_milli_time() - last_send_time) > (sending_intervall * 1000)

    #read inputs
    
    for index, row in enumerate(config['data']):
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
        name_index = row['table'] + ' ' + row['name']
        if name_index in andidb_objects:
              
          try:
            value = andidb_objects[name_index].get()
          except AttributeError:
            # remove failed andiDB Object to prevent trouble
            del config['data'][index]
            del andidb_objects[name_index]
            
            if debug:
              print('Error With', name_index)
            continue
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
      
      # get mobil usage      
      elif row['type'] == 'mobil_usage':
        (rx_bytes, tx_bytes, sum_bytes) = get_mobil_usage()
        value = sum_bytes
        
     
      unit = ''
      if 'unit' in row:
        unit = row['unit']

      if not (row['type'] == 'static' or row['type'] == 'time'):
        # messurement is discarded if lastdata is undefined and equal
        # or if it is not sending_time and this value isnt on_tigger  
        discard_messurement = ('lastdata' in row and row['lastdata'] == value) or ((not its_time_to_send) and (not 'on_trigger' in row))
        if discard_messurement: 
          continue
        else:
          row['lastdata'] = value

      
      if not value == 'Error':
        message.append({'name':row['name'], 'unit': unit, 'value': value})
        row['value'] = value

    
    #set outputs in sync with the s7 read part
    for item in outputs:
        if item['type'] == 's7set' and 'value' in item and 'execute' in item and item['execute']:
          if debug:
            print('execute', item)
            
          s7.set(item['ip'], item['db'], item['offset'], item['length'], item['datatype'], item['value'], item['channel'] if 'channel' in item else 1)#write value with valueset     
          item['execute'] = False
          
          mqtt_con.confirminputs([item['key']])
          time.sleep(1)

   
    last_round = current_milli_time()
    
    if len(message) <= 2:
        continue


    # system is connected to mqtt server
    if mqtt_con.connected:
      if(len(message) <= 2): #nicht sendend net genug daten
        continue 

      # print mqtt message in debug mode
      if debug:
        data = json.dumps(message).strip()
        print('Message Size {} MB'.format(len(data) / 1000000))
      
      
      # call the send data block
      mqtt_con.senddata(message)

      # sending time set to current timestemp
      if its_time_to_send:
        last_send_time = current_milli_time()
    
    # system has no connection to mqtt server
    else: 
      # do not send / save
      # message only contains out of two values
      if(len(message) <= 2):  
          continue
        
      # open offline data space
      f = open(offline_data_path + '/' + datetime.today().strftime('%Y-%m-%d').replace('-', '_') + '.json', 'a')
      for row in message:
        f.write(json.dumps(row) + '\n')

      f.close()
      if its_time_to_send:
        last_send_time = current_milli_time()
        
      if debug:
        print('save file')
    
    if len(totalizers):
      f = open(totalizers_path, 'w+')
      f.write(json.dumps(totalizers))
      f.close()



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
        if not ('key' in row and 'value' in row):
          if debug:
            print('Invalid msg', msg)
          return
            
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


    success_sending_data = True

    messages = []
    message = []

    f = open(offline_data_path + '/' + file, 'r')
    
    error_in_message_block = False
    
    # go throung all lines in one file
    for line in f.readlines():
      
      # check if line starts like a json would start
      if not line.startswith('{'):
        continue
      
      try:
        conv_line = json.loads(line)

        # if new line is mad start new message block
        if (conv_line['name'] == 'mad' or conv_line['name'] == 'MAD'):
          # only add if message block has entrys
          if len(message):
            messages.append(message)
            
          # then clear message block
          message = []
          
          # also there can be no errors in the message block 
          error_in_message_block = False
          
          
        if not error_in_message_block:
          message.append(conv_line)
        
      except Exception as e:
        print(e)
        # this means one line in the message block is not a vaild JSON
        error_in_message_block = True
        
        # prevent deleting this file
        success_sending_data = False

      # end of loop
    
    # close file to prevent crossing
    f.close()
    
    # append last message block to the whole message
    messages.append(message)
    
    
    # send to the message to the cloud
    if mqtt_con.connected:
        success_sending_data = mqtt_con.sendofflinedata(messages) and success_sending_data
    
    
    if success_sending_data:
      try:
        # Failes in some cases
        os.remove(offline_data_path + '/' + file)
      except:
        pass

if __name__ == '__main__':
    main()
