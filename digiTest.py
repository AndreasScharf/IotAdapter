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
inReading = False
while 1:
  if inReading and ser.inWaiting() <= 0:
    org_checksum = buffer[-1]
    new_checksum = checksum(buffer[:-1])
    print(org_checksum, new_checksum)
    buffer = []


  inReading = False
  if ser.inWaiting() > 0:
    inReading = True
    data = ser.read(size=2)
    buffer.append(hex(ord(data)))
    data = data.encode("hex")
    print('Respondline ', data)
