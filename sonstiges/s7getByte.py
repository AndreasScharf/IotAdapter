import snap7
from snap7.util import *
#from snap7.snap7types import *
s7 = snap7.client.Client()
s7.connect('192.168.10.100', 0, 1)

DB = 200

def read(OFFSET):
    data = s7.db_read(DB, OFFSET, 1)
    int_val = int.from_bytes(data, "big")
    print(hex(int_val))

def write(OFFSET):
    value = 0xa0
    
    byte = value.to_bytes(1, 'big', signed=False)
    s7.db_write(DB, OFFSET, byte)
    
    
    
    
#write()
read(0)
read(2)
