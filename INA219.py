#import os
from ina219 import INA219
from ina219 import DeviceRangeError
import time



class current_sensor(object):
    def __init__(self, min = 4, max = 20, offset = 0 ):
        ohm_shunt = 0.5 #standardwert für den eingebauten Shunt, später dann 0.5 Ohm
        max_current = 0.1
        self.min = float(min)
        self.max = float(max)

        self.m = (max - min) / 16
        self.t = min - self.m * 4

        try:
            #self.ina = INA219(ohm_shunt, max_current)
            #self.ina.configure(self.ina.RANGE_32V, self.ina.GAIN_AUTO)
            if offset >= 2:
                offset = offset + 2

            self.ina2 = INA219(ohm_shunt, max_current, None, address=(0x40 + offset))
            self.ina2.configure(self.ina2.RANGE_32V, self.ina2.GAIN_AUTO)

            #schon mal für später
            #self.ina3 = INA219(ohm_shunt, max_current, None, address=0x44)
            #self.ina3.configure(self.ina3.RANGE_32V, self.ina3.GAIN_AUTO)
            #self.ina4 = INA219(ohm_shunt, max_current, None, address=0x45)
            #self.ina4.configure(self.ina4.RANGE_32V, self.ina4.GAIN_AUTO)
        except Exception as e:
            print("Unbekannter Fehler" + str(e))
            return "Error"


    def get(self):

        try:
            voltage = self.ina2.voltage() #Spannung des Busses (nicht versorgungsspannung des Raspi)
            current = self.ina2.current() #gemessner Strom
            power = self.ina2.power()  #Leistung

            #print("Bus Current: %.3f mA" % self.ina2.current()
            current = round(current, 3)
            return self.m * current + self.t

           # return current,voltage, power

        except Exception as e:
            print("Unbekannter Fehler" + str(e))
            return "Error"
            