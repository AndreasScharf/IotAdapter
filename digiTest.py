import time
import serial


ser = serial.Serial(

   port='/dev/ttyUSB0',
   baudrate = 9600,
   timeout=None
)

print('Port Avaliable')
print(ser.isOpen())

bytes_to_setup = [ 0x72, 0x10, 0xEE, 0x01, 0x09, 0x99, 0x45, 0x60, 0x13, 0x01, 0x94, 0x60, 0x00, 0x79, 0x01]
bytes_to_request = [ 0x72, 0x07, 0x01, 0x00, 0x01, 0x00 ]

def checksum(bytes_to_send):

  sum = 0
  for b in bytes_to_send:
    sum = sum + b

  while sum >= 0x100:
    sum = sum - 0x100
  return sum

bytes_to_setup.append(checksum(bytes_to_setup))
ser.write(bytes_to_setup)
print(bytes_to_setup)

while 1:
  if ser.inWaiting() > 0:
    data = ser.read(size=12)
    data = data.encode("hex")
    print('Respond ', data)

    bytes_to_check = []
    index = 0
    bytes_to_check = data[:-1].split(2)
    print(bytes_to_check)
    print(type(bytes_to_check))
