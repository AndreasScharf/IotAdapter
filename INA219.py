#import os
from logging import debug
from ina219 import INA219
from ina219 import DeviceRangeError
import time



class current_sensor(object):
    def __init__(self, min = 4, max = 20, offset = 0 ):
        ohm_shunt = 0.5 #standardwert für den eingebauten Shunt, später dann 0.5 Ohm
        max_current = 0.1
        self.offset = offset        
        self.min = float(min)
        self.max = float(max)

        self.m = (max - min) / 16
        self.t = min - self.m * 4

        try:
            if offset >= 2:
                offset = offset + 2

            self.ina = INA219(ohm_shunt, max_current, None, address=(0x40 + offset))
            self.ina.configure(self.ina.RANGE_32V, self.ina.GAIN_AUTO)

        except Exception as e:
            print("Unbekannter Fehler" + str(e))
            return "Error"


    def get(self):

        try:
            voltage = self.ina.voltage() #Spannung des Busses (nicht versorgungsspannung des Raspi)
            current = self.ina.current() #gemessner Strom
            power = self.ina.power()  #Leistung

            #print("Bus Current: %.3f mA" % self.ina2.current()
            current = round(current, 3)
            if current < 1:
                if debug:
                    print("Verbindung unterbrochen")
                return "Error"
            else:
                return self.m * current + self.t

           # return current,voltage, power

        except Exception as e:
            print("Unbekannter Fehler" + str(e))
            return "Error"
            