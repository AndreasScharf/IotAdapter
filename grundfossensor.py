import serial

class grundfossensor(object):
    """docstring for grundfossensor."""

    def __init__(self, barcode, sensor_id, type):
        self.ports = ['/dev/ttyUSB0']

        self.barcode = barcode
        self.sensor_id = int(sensor_id)
        self.type = type
        self.error = True

        self.fullscale_tempratur = 0
        self.fullscale_pressure = 0
        self.fullscale_flow = 0

        self.init(barcode, sensor_id)

    def init(self, barcode, sensor_id):
        self.try_again = False

        for port in self.ports:
            self.ser = serial.Serial(
               port=port,
               baudrate = 9600,
               timeout=None
            )
            code = []
            temp_code = ''
            for c in barcode:
                if c == '-':
                    continue
                elif temp_code == '':
                    temp_code = c
                else:
                    temp_code = temp_code + c
                    code.append(int(temp_code, 16))
                    temp_code = ''


            self.message = [ 0x72, 0x10 , 0xEE, 0x01, 0x09 ]
            for c in code:
                self.message.append(c)

            self.message.append(self.sensor_id)
            self.message.append(self.checksum(self.message))
            self.ser.write(self.message)
            anwser = self.listen()
            if anwser == 'Error':
                continue
            else:
                self.error = False
                break

        self.try_again = True

    def ieee_bin_to_float(self, zahl):
      v = zahl >> 31
      exp = (zahl & 0x7F800000) >> 23
      man = (zahl & 0x007FFFFF)

      e = float(exp) - float(2 ** (8 - 1) - 1)
      m = 1 + float(man) / float(2 ** 23)

      return (-1) ** v * m * 2 ** e
    def checksum(self, bytes_to_send):
      sum = 0
      for b in bytes_to_send:
        sum = sum + b

      while sum >= 0x100:
        sum = sum - 0x100
      return sum
    def calculate(self, fullscale, value):
         if value > 0x8000 :
           x = float( float(value) - 2 ** 16)  / (2 ** 14) * fullscale
           return x
         elif value < 0x8000 :
           x = float( value ) / (2 ** 14) * fullscale
           return x
         else:
           return 'Error'
    def listen(self):
        timeouts = 10 # Error modus
        isHeader = False
        buffer = []
        trys = 0
        while 1:
            trys = trys + 1
            bytes_in_Waiting = self.ser.inWaiting()
            if bytes_in_Waiting > 0:
                if not isHeader:
                    buffer = []

                data = self.ser.read(size=bytes_in_Waiting)
                for c in data:
                   if isinstance(c, int):
                       buffer.append(c)
                   else:
                       buffer.append(ord(c))

                if isHeader and not data[0] == 0x72:
                   if not buffer[-1] == self.checksum(buffer[:-1]):
                        self.ser.write(self.message)
                        return self.listen()

                   trys = 0
                   return buffer
                else:
                  isHeader = buffer[0] == 0x72
            if trys >= 8000:
               if self.try_again:
                   self.ser.write(self.message)
                   trys = 0
                   timeouts = timeouts - 1
                   if timeouts < 0:
                       return 'Error'
               else:
                   return 'Error'



    def request_fullscale(self, data_id):
        self.message = [ 0x72, 0x06, self.sensor_id, 0x02, data_id ]
        self.message.append(self.checksum(self.message))
        self.ser.write(self.message)

        data = self.listen()
        x = (data[-2] << 24) + (data[-3] << 16) + (data[-4] << 8) + data[-5]

        return self.ieee_bin_to_float(x)

    def get_tempratur(self):
      if self.error :
        self.init(self.barcode, self.sensor_id)
        if self.error: # ist nach initiasierung immer noch error hat init nicbt geklappt
            return 'Error'

      if self.fullscale_tempratur == 0:
        self.fullscale_tempratur = self.request_fullscale(0x03)

      self.message = [0x72, 0x07, self.sensor_id, 0x00, 0x04, 0x00]
      self.message.append(self.checksum(self.message))

      self.ser.write(self.message)

      data = self.listen()

      if data == 'Error':
          self.error = True
          return 'Error'

      value = (data[-3] << 8) + data[-2]

      return self.calculate(self.fullscale_tempratur, value)

    def get_pessure(self):
      if self.type == 'VFS': #VFS kann keinen Druck
        return 'Error'

      if self.error :
        self.init(self.barcode, self.sensor_id)
        if self.error: # ist nach initiasierung immer noch error hat init nicbt geklappt
            return 'Error'

      if self.fullscale_pressure == 0:
        self.fullscale_pressure = self.request_fullscale(0x04)

      self.message = [0x72, 0x07, self.sensor_id, 0x00, 0x01, 0x00]
      self.message.append(self.checksum(self.message))

      self.ser.write(self.message)

      data = self.listen()

      if data == 'Error':
         self.error = True
         return 'Error'

      value = (data[-3] << 8) + data[-2]

      return self.calculate(self.fullscale_pressure, value)
    def get_flow(self):
        if self.type == 'RPS': #VFS kann keinen Druck
            return 'Error'

        if self.error :
            self.init(self.barcode, self.sensor_id)
            if self.error: # ist nach initiasierung immer noch error hat init nicbt geklappt
                return 'Error'

        if self.fullscale_flow == 0:
            self.fullscale_flow = self.request_fullscale(0x08)

        self.message = [0x72, 0x07, self.sensor_id, 0x00, 0x10, 0x00]
        self.message.append(self.checksum(self.message))

        self.ser.write(self.message)#senden

        data = self.listen()#empfangen

        if data == 'Error':
          self.error = True
          return 'Error'

        value = (data[-3] << 8) + data[-2]

        return self.calculate(self.fullscale_pressure, value)
