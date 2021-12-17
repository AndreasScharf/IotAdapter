import platform
import struct

import snap7
from snap7.util import *

if platform.python_version() <= '3.5':
  from snap7.snap7types import *


class s7(object):
    def __init__(self):
        self.current_ip = ''
        self.client = snap7.client.Client()
        self.reconnecting = False 
        self.debug = False

    def get(self, ip, db, offset, length, type, channel=1):

        if self.reconnecting or not self.current_ip == ip :
            try:
                if self.client:
                    self.client.destroy()
                    self.client = snap7.client.Client()

                if self.debug:
                    print('connecting to', ip, channel)
                    
                self.client.connect(ip, 0, channel)
                self.current_ip = ip
                self.reconnecting = False
            except Exception as e:
                error_code = 0x50
                self.reconnecting = True
                if self.debug:
                    print('CPU not avalible', ip)
                    print(e)
                
                return 'Error'
        try:
            
            data = self.client.db_read(int(db), int(float(offset)), int(length) if not type == 'bit' else 8)
        except Exception as e:
            if self.debug:
                print('DB Error, Offset Error, Security Error', e)
            #s7 in error mode 
            self.reconnecting = True
            return 'Error'
        byte_index = 0
        if '.' in offset:
            byte_index = int(offset.split('.')[1])
        value = 0.0
        #print(offset, byte_index, len(data))

        if type=='bit':
            return get_bool(data, byte_index, 0)
        elif type=='word' or type=='byte':
            return get_int(data, 0)
        elif type=='dint':
            return self.get_dint(data, 0)
        elif type=='real':
            return get_real(data, 0)
        else:
            return -1

    def set(self, ip, db, offset, length, datatype, value, channel=1):
        pass

    def get_dint(self, _bytearray, byte_index):
        data = _bytearray[byte_index:byte_index + 4]
        dint = struct.unpack('>i', struct.pack('4B', *data))[0]
        return dint

    