import snap7
from snap7.util import *
from snap7.snap7types import *
s7 = snap7.client.Client()
s7.connect('192.168.14.45', 0, 1)

data = s7.db_read(1, 0, 4)
value = get_real(data, 0)
print(value)
data = bytearray(5)
set_real(data,0, -0.0177002)
data = data[:-1]
print(data)

s7.db_write(1, 0, data)
