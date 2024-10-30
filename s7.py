import platform
import struct
import math
import time 

import snap7
from snap7.util import *

if platform.python_version() <= '3.5':
  from snap7.snap7types import *


class PLCClient(snap7.client.Client):
    def __init__(self):
        super().__init__()
        self.ip_address = ''
        self.reconnecting = False
        self.debug = False

    def establish_connection(self, ip, channel):
        if self.reconnecting or not self.ip_address == ip:
            try:
                if self.debug:
                    print('connecting to', ip, channel)
                if self.get_connected():
                    super().destroy()
                    super().__init__()
                
                self.connect(ip, 0, channel)
                self.ip_address = ip
                self.reconnecting = False

                return 0
            except Exception as e:
                error_code = 0x50
                self.reconnecting = True

                if self.debug:
                    print('CPU not avalible', ip)
                    print(e)
                return f'Unreachable peer {ip}'
                


class s7(object):
    def __init__(self):
        self.current_ip = ''
        self.read_client = PLCClient()
        self.write_client = PLCClient()
        
        self.debug = False


    def get(self, ip, db, offset, length, type, channel=1):

        result = self.read_client.establish_connection(ip, channel)
        if result:
            return None, result
        
        try:
            data = self.read_client.db_read(int(db), int(float(offset)), int(length) if not type == 'bit' else 1)
        except Exception as e:
            # if e == b' ISO : An error occurred during recv TCP : Connection timed out':
            
            #s7 in error mode and do a restart
            self.read_client.reconnecting = True

            #print('DB Error, Offset Error, Security Error', e)
            return None, ip + str(e )
        
        byte_index = 0
        bool_index = 0
        if '.' in offset:
            byte_index, bool_index = str(offset).split('.')
        else:
            byte_index = int(offset)
            
            #byte_index = int(offset.split('.')[1])
        value = 0.0
        #if self.debug:
          

        if type=='bit':
            return self.get_bool(data, 0, int(bool_index)), None
        elif type == 'byte':
            # converts byte array to one uint
            return int.from_bytes(data, "big"), None
        elif type=='word':
            return get_int(data, 0), None
        elif type=='dint':
            return self.get_dint(data, 0), None
        elif type=='real':
            value = get_real(data, 0)
            if (math.isnan(float(value)) or value == math.inf):
                return None, 'S7 Reading Error'

            return value, None
        else:
            return -1, None

    def set(self, ip, db, offset, length, datatype, value, channel=1):
        
        self.read_client.establish_connection(ip, channel)

        read_successful = False
        data = None
        while not read_successful:
            try:
                data = self.read_client.db_read(int(db), int(float(offset)), int(length) if not datatype == 'bit' else 1)
                read_successful = True
            except:
                print('cannot read db', ip, int(db), int(float(offset)), int(length) if not datatype == 'bit' else 1)
            time.sleep(0.3)

        if datatype == 'bit':
            offset = float(offset)
            bit_index = int(offset % 1 * 10)
            if value:
                data[0] = (1 << bit_index) | data[0]
            else:
                data[0] = (~(1 << bit_index)) & data[0]
        elif datatype == 'byte':
            #convert the integer into bytes
            data = int(value).to_bytes(1, 'big', signed=False)
            
        elif datatype == 'real':
            data = bytearray(int(length) + 1)
            set_real(data, 0, float(value))
            data = (data[:-1])
            

        """
            Start writing Job
        """
        self.read_client.establish_connection(ip, channel)
        write_successful = False
        while not write_successful:
            try:
                self.read_client.db_write(int(db), int(float(offset)), data)
                write_successful = True
            except:
                if self.debug:
                    print('no successful write')
            time.sleep(0.3)
        if self.debug:
            print('write', db, offset, value, ' success')

    def get_dint(self, _bytearray, byte_index):
        data = _bytearray[byte_index:byte_index + 4]
        dint = struct.unpack('>i', struct.pack('4B', *data))[0]
        return dint

        
    
    def get_bool(self, _bytearray, byte_index, bool_index):
        """
        Get the boolean value from location in bytearray
        """
        index_value = 1 << bool_index

        byte_value = _bytearray[byte_index]
        current_value = byte_value & index_value
        return current_value == index_value


