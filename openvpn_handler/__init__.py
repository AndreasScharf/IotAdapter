import os


class vpnclient(object):
    """docstring for openvpn control router."""

    def __init__(self, path):
       self.registerd = False
       self.config_path = path

    def create_config(self, ca, key, cert, tls,port):
       
      '''
      create a config file with connection parameters for triangle connection to server
      shared network is usally .225.0/24
      '''
      config_string = '''
client
dev tun
proto udp
remote 85.214.215.187 {port}
resolv-retry infinite
nobind
persist-key
persist-tun
<ca>
{ca}
</ca>
<cert>
{cert}
</cert>
<key>
{key}
</key>
remote-cert-tls server
key-direction 1
<tls-auth>
{tls}
</tls-auth>
cipher AES-256-CBC
verb 3

      '''.format(port=port, ca=ca, cert=cert, key=key, tls=tls)

      f = open(self.config_path, 'w+')
      f.write(config_string)
      # configuration is store usally in /home/pi/Documents/IotAdapter/openvpn_handler/config.ovpn
      # openvpn serivce has a link from /etc/openvpn/client.conf to /home/pi/Documents/IotAdapter/openvpn_handler/config.ovpn

      f.close()
      
    def start_vpn(self):
      #start openvpn as systemctl for running one instance in the background
      order = 'sudo systemctl start openvpn@client'
      print(order)
      os.system(order)
      
    def stop_vpn(self):
      order = 'sudo systemctl stop openvpn@client'
      print(order)
      os.system(order)