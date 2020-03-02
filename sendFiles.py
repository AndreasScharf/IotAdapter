from xml.dom import minidom
from gpiozero import MCP3008
import RPi.GPIO as GPIO
import socket
import time
from datetime import datetime
import json
import os
#Snap7
import snap7
from snap7.util import *
from snap7.snap7types import *
#Eigene Klassen
import Value
konpath = ''

class Hardware:
    def read(self, channelNumber=0, typ='analog', multiplier=1.0, val=''):
        read(channelNumber, typ, multiplier, val, None, None, None, None, None)

    def read(self, channelNumber, typ, multiplier, val, plc, dbblock, start, length, datatype):
        self.typ = typ
        if typ == 'analog':
            adc = MCP3008(channel=channelNumber)
            vol = 3.3 * adc.value * multiplier
            return  vol
        elif typ == 'time':
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elif typ == 'static':
            return val
        elif typ == 'counter':
            mydoc = minidom.parse(konpath)
            values = mydoc.getElementsByTagName('value')
            for elem in values:
                if(elem.attributes['typ'].value == 'counter' and int(elem.attributes['channel'].value) == channelNumber):
                    return elem.attributes['counter'].value
        elif typ == 'S7':
            return self.readFromDB(plc, dbblock, start, length, datatype)
        else:
            return 0

    def get_dint(_bytearray, byte_index):
        data = _bytearray[byte_index:byte_index + 4]
        dint = struct.unpack('>i', struct.pack('4B', *data))[0]
        return dint

    def readFromDB(self, plc, dbblock, start, length, datatype):
        if not plc.get_connected():
            return 0

        print('DB' + dbblock + ' Offset' + start + ' lenge' + length)
        result = plc.db_read(int(dbblock), int(start), int(length))

        if datatype=='bit':
            return get_bool(result, 0, 0)
        elif datatype=='word' or datatype=='byte':
            return get_int(result, 0)
        elif datatype=='dint':
            return get_dint(result, 0)
        elif datatype=='real':
            return get_real(result, 0)
        else:
            return 0

class Konfiguration:
    def __init__(self, path):
        self.read(path)

    def read(self, path):
        self.path = path
        print('set konpath')
        global konpath
        konpath = path

        mydoc = minidom.parse(path)
        connection = mydoc.getElementsByTagName('connection')
        extra = mydoc.getElementsByTagName('extra')
        #Connectionproberties
        self.IPAdress = connection[0].attributes['ipAdress'].value
        self.Port = int(connection[0].attributes['port'].value)
        self.Intervall = int(extra[0].attributes['intervall'].value) -1
        #Checking Values
        values = mydoc.getElementsByTagName('value')
        self.Values = []
        GPIO.setmode(GPIO.BCM)

        lastIP = ''
        for elem in values:
            multiplier = 1.0
            name = elem.attributes['name'].value
            typ = elem.attributes['typ'].value
            channel = int(elem.attributes['channel'].value)

            unit = elem.attributes['unit'].value
            val = ''
            #For Siemnes SPS
            dbblock = None
            start = None
            length = None
            datatype = None

            if typ == 'static':
                val = elem.attributes['values'].value
            elif typ == 'analog':
                multiplier = float(elem.attributes['multi'].value)
            elif typ == 'counter':
                increase = elem.attributes['increase'].value

                GPIO.setup(channel, GPIO.IN, GPIO.PUD_DOWN)
                GPIO.add_event_detect(channel, GPIO.RISING, lambda x: setcounter(channel, increase), 300)
            elif typ=='S7':


                s7 = snap7.client.Client()
                ip = str(elem.attributes['IP'].value)
                zahl = 0
                if ip==lastIP:
                    pass
                else:
                    s7.connect(ip, 0, 1)
                    plc = s7
                    lastIP = ip
                dbblock = elem.attributes['DB'].value
                start = elem.attributes['start'].value
                length = elem.attributes['length'].value
                datatype = elem.attributes['datatype'].value

            if typ=='S7':
                wert = Value.Value(name, typ, channel, multiplier, unit, val, plc, dbblock, start, length, datatype)
                self.Values.append(wert)
            else:
                wert = Value.Value(name, typ, channel, multiplier, unit, val)
                self.Values.append(wert)

        def setcounter(channel, increase):
            mydoc = minidom.parse(konpath)
            values = mydoc.getElementsByTagName('value')

            for elem in values:
                if(elem.attributes['typ'].value == 'counter' and int(elem.attributes['channel'].value) == channel):
                    counter = int(elem.attributes['counter'].value)
                    elem.setAttribute('counter1', str(counter + int(increase)))
                    with open(konpath, "w") as xml_file:
                        mydoc.writexml(xml_file)



#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#Main Script
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

konfig = Konfiguration('/home/pi/Documents/IotAdapter/konfig.xml')
hw = Hardware()

def builddata():
    data = []
    for item in konfig.Values:
        data.append({"name": item.name, "unit" :item.unit, "value": str(hw.read(int(item.channel), item.typ, item.multiplier, item.val, item.plc, item.dbblock, item.start, item.length, item.datatype))})

    #remove the last dot
    #builds commandString
    return data

time.sleep(3)
while 1:
    gesendet = False
    while not gesendet:
        print('sending...')
        try:
            tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp.connect((konfig.IPAdress, konfig.Port))
            tcp.send(bytes(json.dumps(builddata(), 'utf-8')))
            gesendet = True

        except Exception as e:
            print(e)
            tcp.close()
        finally:
            tcp.close()

    print('idle')
    time.sleep(konfig.Intervall)

f = open('/home/pi/Documents/IotAdapter/ichBeendeIrgenwiedieSchleife', 'w')
f.write('bin dumm')
