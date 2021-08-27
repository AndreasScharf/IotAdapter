import paramiko 
from scp import SCPClient
import os

class vpnclient(object):
    """docstring for openvpn control router."""
    def __init__(self):
      self.registerd = False
     
    def register(self, ip_router, name, pw):
      print('register router')
      self.registerd = True

      self.ip_router = ip_router
      self.name = name
      self.pw = pw

      self.client = paramiko.SSHClient()
      self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def start(self, port, ca_root, client_key, client_cer, ta_key):

      self.client.connect(self.ip_router, username=self.name, password=self.pw)
      temp_config_path = './openvpn.tmp'
      remote_config_path = '/etc/config/openvpn'

      scp = SCPClient(self.client.get_transport())
      scp.get(remote_config_path, temp_config_path)
      f = open(temp_config_path, 'r')
      config = {
        "enable": 1,
        "port": port,
      }

      frapp_vpn_config = False
      lines = f.readlines()
      i = 0
      for line in lines:
        if "config openvpn" in line:
          frapp_vpn_config = 'client_frapp' in line
        elif frapp_vpn_config:
          if 'option enable' in line:
            lines[i] = self.replace_option(line, config['enable'])
          elif 'option port' in line:
            lines[i] = self.replace_option(line, config['port']) 
          elif 'option ca' in line:
            self.replace_file(line.split("'")[1], ca_root, 'ca.crt')
          elif 'option key' in line:
            self.replace_file(line.split("'")[1], client_key, 'user2.key')
          elif 'option cert' in line:
            self.replace_file(line.split("'")[1], client_cer, 'user2.crt')
          elif 'option tls_crypt' in line:
            self.replace_file(line.split("'")[1], ta_key, 'ta.key')

        i = i + 1
      f.close()
      fw = open(temp_config_path, 'w')
      fw.write(''.join(lines))
      fw.close()

      scp.put(temp_config_path, remote_config_path)
      
      os.remove(temp_config_path)
      stdin, stdout, stderr = self.client.exec_command('/etc/init.d/openvpn restart')
      #self.send_command('stop')

    def stop(self):
      
      self.client.connect(self.ip_router, username=self.name, password=self.pw)
      temp_config_path = './openvpn.tmp'
      remote_config_path = '/etc/config/openvpn'

      scp = SCPClient(self.client.get_transport())
      scp.get(remote_config_path, temp_config_path)
      f = open(temp_config_path, 'r')
      config = {
        "enable": 0,
        
      }

      frapp_vpn_config = False
      lines = f.readlines()
      i = 0
      for line in lines:
        if "config openvpn" in line:
          frapp_vpn_config = 'client_frapp' in line
        elif frapp_vpn_config:
          if 'option enable' in line:
            lines[i] = self.replace_option(line, config['enable'])

        i = i + 1
      f.close()
      fw = open(temp_config_path, 'w')
      fw.write(''.join(lines))
      fw.close()

      scp.put(temp_config_path, remote_config_path)
      
      os.remove(temp_config_path)
      stdin, stdout, stderr = self.client.exec_command('/etc/init.d/openvpn restart')
      
    def set_auth_creditals(self, path, user, pw):
      f = open('user2.tmp', 'w')
      f.write(pw)
      f.close()

      scp = SCPClient(self.client.get_transport())
      scp.put('user2.tmp', path)
      os.remove('user2.tmp')
    
    def send_command(self, command):

      try:
        self.client.connect(self.ip_router, username=self.name, password=self.pw)
      except:
        return

      stdin, stdout, stderr = self.client.exec_command(command)
      lines = stdout.readlines()

      self.client.close()

    def replace_option(self, line, value):
      chunks = line.split("'")
      chunks[1] = str(value)
      return "'".join(chunks)

    def replace_file(self, path, value, name):
      if not os.path.isdir('./temp/'):
        os.mkdir('./temp/')
      
      my_file_path = './temp/' + name

      f = open(my_file_path, 'w+')
      f.write(value)
      f.close()

      scp = SCPClient(self.client.get_transport())
      scp.put(my_file_path, path)

      os.remove(my_file_path)

