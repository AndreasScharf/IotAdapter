import serial

port = '/dev/ttyS0'
ser = serial.Serial(
    port=port,
    baudrate = 9600,
    timeout=None
)


ser.write([0x72, 0x06, 0xEE, 0x02, 0x02, 0x6B])
print('message send..')
#while 1:
#    bytes_in_Waiting = ser.inWaiting()
#    if bytes_in_Waiting > 0:
data = ser.read(size=20)
print(data)

#        buffer = []
#        for c in data:
#            if isinstance(c, int):
#                buffer.append(c)
#            else:
#                buffer.append(ord(c))

#        print(buffer)
