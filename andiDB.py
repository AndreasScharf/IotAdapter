import socket
import sys

class client(object):
  """docstring for grundfossensor."""

  def __init__(self, host, port):
    # Create a TCP/IP socket
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server_address = (host, port)

    self.connect()
  def connect(self):
    self.sock.connect(self.server_address)
  def pull(self, table, index):
    msg = 'PULL;' + str(table) + ';' + str(index) + '\n'
    self.sock.sendall(bytes(msg,'utf-8'))
    chunks = []
    line = ''
    while 1:
      byte = self.sock.recv(1)
      if byte == b';':
        chunks.append(line)
        line = ''
      elif byte == b'\n':
        chunks.append(line)
        break
      else:
        line = line + str(byte.decode("utf-8"))

    if table == chunks[1] and index == int(chunks[2]):
      return chunks[3]
    else :
      return 'Error Value'

  def push(self, table, index, value):
    msg = 'PUSH;' + str(table) + ';' + str(index) + ';' + str(value) + '\n'
    self.sock.sendall(bytes(msg, 'utf-8'))
  
  def index(self, table, name):
    msg = 'INDEX;' + str(table) + ';' + str(name) + '\n'
    self.sock.sendall(bytes(msg, 'utf-8'))
    chunks = []
    line = ''
    while 1:
      byte = self.sock.recv(1)
      if byte == b';':
        chunks.append(line)
        line = ''
      elif byte == b'\n':
        chunks.append(line)
        break
      else:
        line = line + str(byte.decode("utf-8"))

    if table == chunks[1] and name == chunks[2]:
      return int(chunks[3])
    else:
      return 'Error'

class value(object):
  def __init__(self, client, table, name):
    self.client = client
    self.table = table
    self.name = name
    self.index = -1
    self.index = client.index(table, name)
    if self.index == -1:
      print('Table, Name : Error')
    
  def get(self):
    if self.index == -1:
      return 'Error'
    else:
      return self.client.pull(self.table, self.index)
  def set(self, value):
    if self.index == -1:
      return 'Error'
    else:
      return self.client.push(self.table, self.index, value)
