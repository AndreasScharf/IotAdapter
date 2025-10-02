"""This is the example module.
This module does stuff.
"""
__all__ = []
__version__ = '1.0.3'
__author__ = 'Andreas Scharf'

import socket
import time
import RPi.GPIO as GPIO
import serial
import os
import ifaddr
import usb.core
import socket
import sys

debug = ('-d' in sys.argv or '-debug' in sys.argv)


interrupted = False
def current_milli_time(): return int(round(time.time() * 1000))


serialCom = 0
currentSerialCom = 0
usbcomerror = 0


#
# Do not restart telit module if internet wwan0 is up
#
'''
if not internet():
    # hard restart if the telit module
    # and call connect to serial com
    restartTelitModule()
# but need to find and establish serial com
else:
    connectSerialCom()

'''
#
## Entry Point for Mobile COM Script
#
PIN = 26
class MobilCom(object):
    def __init__(self, apn):

        #
        ## Init Telit Module Hardware
        #

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # turn on mobil
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN, GPIO.OUT)
        if debug: print('Mobil Module Activation...')

        self.check_internet_timer = timer(float(60.0 * 0.5), 1000)
        # timer for 1 hours
        # only if mobil apn is lost due to too much traffic 
        self.reconfigure_modem_timer = timer(float(1), 3600 * 1000)

        # start init wwan0
        # set apn to module
        self.apn = apn


        self.usbcomerror = 0
        
        self.connection = 0

        if not self.internet():
            self.initWWAN0()
        else:
            self.state = 5
            self.mobil_setup_done = True

            if debug: print("Initializing WWAN setup...")
            while not self.telitModuleActived():
                pass
            
            # get new usb coms after initialization
            self.usbcoms = []
            self.connectSerialCom()

    


    def internet(self, host="8.8.8.8", port=53, timeout=3):
        """
        Host: 8.8.8.8 (google-public-dns-a.google.com)
        OpenPort: 53/tcp
        Service: domain (DNS/TCP)
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            self.connection = 1
            return True
        except socket.error as ex:
            if debug: print(ex)
            self.connection = 0
            return False

    def getUsbComs(self):
        self.usbcoms = []
        for item in os.listdir("/dev/"):
            if 'USB' in item:
                self.usbcoms.append('/dev/' + item)

    # 
    # Send AT Command to Telit Module
    #
    def sendMessage(self, m):

        m = m + '\r'
        writesuccessful = False
        while not writesuccessful:
            try:
                self.serialCom.reset_input_buffer()
                self.serialCom.write(m.encode())
                writesuccessful = True
                self.usbcomerror = 0
            except KeyboardInterrupt:
                if debug: print('KeyboardInterrupt exception is caught')
                return ''
            except Exception as e:
                
                #closeSerialCom()
                
                if debug: print('write unsuccessful', e, m)
                self.usbcomerror = self.usbcomerror + 1
                if self.usbcomerror > 10:
                    self.usbcomerror = 0
                    self.restartTelitModule()
                elif usbcomerror > 5:
                    # connect no next larger
                    self.connectSerialCom()

                time.sleep(1)

        time.sleep(0.51)
        wd_for_timeout = current_milli_time()
        response = ''
        while 1:
            biw = self.serialCom.inWaiting()
            if biw:
                word = self.serialCom.read(biw)
                try:
                    response += word.decode('utf-8')
                except Exception as e:
                    if debug: print(word, e)
                    
                if '\r' in response:
                    return (response, None)

            if current_milli_time() - wd_for_timeout > 30 * 1000:
                if debug: print('Timeout', m)
                return (None, 'Timeout')

    def initWWAN0(self):
        self.state = 0  # Initialize the state
        self.timer_start = None
        self.mobil_setup_done = False

    def update(self):
        current_time = time.time()  # Use the system timer or a microcontroller-specific timer
        
        if self.state == 0:
            # Initializing
            if debug: print("Initializing WWAN setup...")
            if not self.telitModuleActived():
                return
            
            # get new usb coms after initialization
            self.usbcoms = []
            
            self.connectSerialCom()
            self.mobil_setup_done = False

            self.timer_start = current_time
            self.state = 1  # Transition to the next state (Step 1)

        elif self.state == 1:
            # Set APN to the module
            a, e = self.sendMessage(f'AT+CGDCONT=1,"IPV4V6","{self.apn}"')
            if debug: print(a)
            self.timer_start = current_time
            self.state = 2  # Move to the next state (Step 2)

        elif self.state == 2:
            # Wait 5 seconds before the next step
            if current_time - self.timer_start >= 5:
                # Bring the module into ECM mode
                a, e = self.sendMessage('AT#USBCFG=4')
                if debug: print(a)
                self.timer_start = current_time
                self.state = 3  # Move to the next state (Step 3)

        elif self.state == 3:
            # Wait 90 seconds before the next step
            if current_time - self.timer_start >= 90:
                # Reboot necessary for ECM start
                a, e = self.sendMessage('AT#REBOOT')
                if debug: print(a)
                self.timer_start = current_time
                self.state = 4  # Move to the next state (Step 4)

        elif self.state == 4:
            # Wait 90 seconds before starting ECM
            if current_time - self.timer_start >= 90:
                if debug: print('Start ECM')
                a, e = self.sendMessage('AT#ECM=1,0')
                if debug: print(a)
                
                # connection check
                self.internet()

                self.mobil_setup_done = True
                self.state = 5  # Move to the final state


        elif self.state == 5:
            # WWAN setup is complete
            # print('WWAN initialization complete.')
            pass
    
    def set_apn(self, apn):
        self.apn = apn
        self.initWWAN0()
    #
    # Hardware Restart of the Telit Module
    #
    def restartTelitModule(self):
        if debug: print('restart module by hard reset')
        GPIO.output(PIN, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(PIN, GPIO.LOW)
        if debug: print('restarted')
        while not self.telitModuleActived():
            time.sleep(1)
        if debug: print('Module Found')
        
        if debug: print('Waiting For serial com')
        time.sleep(1)

        # get new usb coms after initialization
        self.getUsbComs()

        self.connectSerialCom()

    def connectSerialCom(self):
        com_index = 0
        
        # set the timeout counter 
        timeouter = current_milli_time()
        com_open_success = False
        
        # first update usbcoms Array
        self.getUsbComs()
        
        while not com_open_success:
            try:
                if debug: print('Try open COM on', self.usbcoms[com_index])
                timeouter = current_milli_time()
                self.serialCom = serial.Serial(
                    port=self.usbcoms[com_index],
                    baudrate=115200,
                    timeout=None)

                self.serialCom.reset_input_buffer()
                self.serialCom.write('AT\r'.encode())

                unknownPortCom = True
                while unknownPortCom:
                    b_in_waiting = self.serialCom.inWaiting()
                    if b_in_waiting:
                        a = self.serialCom.read(b_in_waiting)
                        if debug: print(a)
                        # line from mobile module should be AT in bytes
                        if a == b'AT\r': 
                            if debug: print('Found Telit on {} {}'.format(self.usbcoms[com_index], a))
                            com_open_success = True
                            
                    if (current_milli_time() - timeouter) > 1000:
                        if debug: print('Timeout for {}'.format(self.usbcoms[com_index]))
                        com_index += 1
                        unknownPortCom = False

            except:
                if debug: print('OS Error on {}'.format(self.usbcoms[com_index - 1]))
                com_index += 1
                if com_index > len(self.usbcoms):
                    com_index = 0
                    time.sleep(60)

    def telitModuleActived(self):
        # Find all USB devices connected to the system
        dev = usb.core.find(find_all=1)
        
        # Iterate through each device configuration
        for cfg in dev:
            # Check if the device matches the specific vendor and product ID pattern
            if cfg.idVendor == 0x1bc7 and (cfg.idProduct & 0x1200) == 0x1200:
                # If a matching device is found, print a message and return True
                if debug: print('Mobil Module Attached')
                return True

    def AT_CSQ(self):
        if self.state != 5:
            return (0, 0)

        a, e = self.sendMessage('AT+CSQ')
        if not e:
            a = a.split('\n')
            value = [x for x in a if '+CSQ:' in x]
            if len(value):
                value = value[0].split(' ')
                if len(value) >= 2:
                    value = value[1]
                    return (float(value.split(',')[0]), float(value.split(',')[1]))
                
        return (0, 0)

    def loop(self, time_passed):


        # mobile init done
        #if self.state == 5:
            # get connection quality
            #(rssi, ber) = self.AT_CSQ()


        
        
        # update the state of the module
        self.update()
        
        check_internet_timer_e = self.check_internet_timer.elapsed(time_passed)
        reconfigure_modem_timer_e = self.reconfigure_modem_timer.elapsed(time_passed)

        # set check_internet_counter global varialbe to local varialbe
        if check_internet_timer_e:
            # reset check_internet_counter to 10
            self.check_internet_timer.reset()

            # get if system is connected to network
            internet_value = self.internet()
            
            # if system is not connected to network to network and mobile setup is done a restart is nesseary
            if self.mobil_setup_done and not internet_value:
                a = self.sendMessage('AT#ECM=1,0')
                # restart ECM
                if reconfigure_modem_timer_e:
                    if debug: print("Reconfigure Modem")
                    
                    # init wwan0 again after apn lost
                    self.initWWAN0()

            elif internet_value:
                self.reconfigure_modem_timer.reset()


class timer(object):
  def __init__(self, timer, time_unit, absolut_time=False):
    self.timer_value = timer
    self.time_unit = time_unit
    self.absolut_time = absolut_time


    if not isinstance(timer, float):
      self.timer = timer.get() * time_unit
    else:
      self.timer = timer * time_unit


  def elapsed(self, time_passed):
    self.timer = self.timer - time_passed

    # if the timer_value instance is a float that means it is no andiDB value
    if not isinstance(self.timer_value, float):
      return int(self.timer < 0 and self.timer_value.get() and True)
    else:
      return int(self.timer < 0 and self.timer_value and True)

  def reset(self):
    if not isinstance(self.timer_value, float):
      self.timer = self.timer_value.get() * self.time_unit
    else:
      self.timer = self.timer_value * self.time_unit




