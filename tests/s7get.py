from s7 import s7  
import time
s7 = s7()

while 1:
    value = s7.get('192.168.14.1', 300, 16, 4, 'real')
    print(value)
    time.sleep(1)