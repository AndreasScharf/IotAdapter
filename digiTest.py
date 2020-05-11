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
buffer = []
isHeader = False
inReading = False
while 1:
  bytes_in_Waiting = ser.inWaiting()


  if bytes_in_Waiting > 0:
    if not isHeader:
        buffer = []

    data = ser.read(size=bytes_in_Waiting)

    for c in data:
      buffer.append(ord(c))

    if isHeader and not buffer[0] == 0x72:
      # Fertig
      print(res_bytes)
      print(res_bytes[-1])
      print(checksum(res_bytes[:-1]))

    isHeader = buffer[0] == 0x72
