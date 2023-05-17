#import os
from logging import debug
from ina219 import INA219
from ina219 import DeviceRangeError
import time



class current_sensor(object):
    def __init__(self, min = 4, max = 20, offset = 0, cutoff = False ):
        ohm_shunt = 0.5 #standardwert für den eingebauten Shunt, später dann 0.5 Ohm
        max_current = 0.1
        self.offset = offset        
        self.min = float(min)
        self.max = float(max)
        self.cutoff = cutoff

        self.m = (max - min) / 16
        self.t = min - self.m * 4

        try:
            if offset >= 2:
                offset = offset + 2
            self.ina2 = INA219(ohm_shunt, max_current, 1, address=(0x40 + offset))
            self.ina2.configure(self.ina2.RANGE_32V, self.ina2.GAIN_AUTO)

        except Exception as e:
            if hasattr(self, 'debug'):
                print("Unbekannter Fehler" + str(e))

        self.address = (0x40 + offset)

    def get(self, messurement='mA'):

        try:
            if(messurement == 'V'):
                value = self.ina2.voltage() #Spannung des Busses (nicht versorgungsspannung des Raspi)
            else:
                value = self.ina2.current() #gemessner Strom
                
            power = self.ina2.power()  #Leistung
            if hasattr(self, 'debug') and self.debug and not messurement == 'V':
                print("Bus Current: %.3f mA" % self.ina2.current(), format(self.address, '#04x'))
            elif hasattr(self, 'debug') and self.debug and messurement == 'V':
                print("Bus Voltage: %.3f V" % self.ina2.voltage(), format(self.address, '#04x'))
            
            value = round(value, 3)
            if value < self.min:
                if hasattr(self, 'debug') and self.debug:
                    print("Verbindung unterbrochen")
                return "Error"
            else:
                scaledValue = self.m * value + self.t
                
                #Cut off Function if neccsesary
                if scaledValue > self.max and self.cutoff:
                    scaledValue = self.max
                elif scaledValue < self.min and self.cutoff:
                    scaledValue = self.min
                    
                return scaledValue

           # return current,voltage, power

        except Exception as e:
            if hasattr(self, 'debug') and self.debug:
                print("Unbekannter Fehler" + str(e))

            return "Error"

    def getDigital(self, spliter):

        try:
            # Spannung des Busses (nicht versorgungsspannung des Raspi)
            voltage = self.ina2.voltage()  # gemessner Strom
            
           
            return voltage > spliter

           # return current,voltage, power

        except Exception as e:
            if hasattr(self, 'debug') and self.debug:
                print("Unbekannter Fehler" + str(e))

            return "Error"
