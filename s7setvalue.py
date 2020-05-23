import snap7
from snap7.util import *
from snap7.snap7types import *
s7 = snap7.client.Client()
s7.connect('192.168.14.57', 0, 1)
data = []
s7.db_write(300, 96, set_bool(data, 0, 0, 1))
