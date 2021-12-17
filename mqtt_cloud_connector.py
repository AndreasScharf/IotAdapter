import paho.mqtt.client as mqtt
import ssl
import time
import json

class connector(object):
    def __init__(self):
        self.connected = False
        self.not_reconnect = False
       
    def connect(self, host, port, reconnect=False):
        
        self.host = host
        self.port = port
        if self.connected:
            return
         
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False  # Without this line, I does not work
        print('connecting', self.connected)
        if hasattr(self, 'client'):
            self.client.disconnect()

        self.client = mqtt.Client()
            
            
        self.client.tls_set(
                ca_certs='/home/pi/Documents/IotAdapter/keys/ca-crt.pem', 
                certfile='/home/pi/Documents/IotAdapter/keys/client1-crt.pem', 
                keyfile='/home/pi/Documents/IotAdapter/keys/client1-key.pem',
                cert_reqs=ssl.CERT_NONE) # <--- even without arguments
        self.client.disable_logger()
        self.client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.client.on_message = lambda client, userdata, msg : self.on_message(client, userdata, msg)
        self.client.on_disconnect = lambda  client, userdata, rc : self.on_disconnect()


        self.client.username_pw_set(username="mqtt", password="mqttpw1337")
        try:
            self.client.connect(host, port, 60)
            self.connected = True
            self.client.loop_start()
        except KeyboardInterrupt:
            raise
        except:
            if not reconnect:
                self.on_disconnect()

    def on_connect(self, client, userdata, flags, rc):
        ret = self.client.publish(self.mad + "/alive", self.mad) 

        self.connected = True
        print('connection established')
        self.client.subscribe("$SYS/#")

        self.client.subscribe( self.mad + "/recievedata")

        self.client.subscribe( self.mad + "/startvpn")
        self.client.subscribe( self.mad + "/stopvpn")

        self.client.subscribe( self.mad + "/start_realtime")
        self.client.subscribe( self.mad + "/stop_realtime")
        
        self.client.subscribe(self.mad + "/reconfig_system")


        if hasattr(self, 'on_connected') and callable(getattr(self, 'on_connected')):
            self.on_connected()

    def on_message(self, client, userdata, msg):

        if '/startvpn' in msg.topic:
            if hasattr(self, 'on_startvpn') and callable(getattr(self, 'on_startvpn')):
                try:
                    data = json.loads(msg.payload)
                    self.on_startvpn(data)
                except:
                    print('not a json')
            else:
                print('on_startvpn not linked')   
        elif '/stopvpn' in msg.topic:
            if hasattr(self, 'on_stopvpn') and callable(getattr(self, 'on_stopvpn')):
                self.on_stopvpn()
            else:
                print('on_stopvpn not linked')
        elif '/recievedata' in msg.topic:
            if hasattr(self, 'on_recievedata') and callable(getattr(self, 'on_recievedata')):
                self.on_recievedata(msg.payload)
            else:
                print('on_recievedata not linked')
        elif '/start_realtime' in msg.topic:
            if hasattr(self, 'on_start_realtime') and callable(getattr(self, 'on_start_realtime')):
                self.on_start_realtime()
            else:
                print('on_start_realtime not linked')
        elif '/stop_realtime' in msg.topic:
            if hasattr(self, 'on_stop_realtime') and callable(getattr(self, 'on_stop_realtime')):
                self.on_stop_realtime()
            else:
                print('on_stop_realtime not linked')
        elif '/reconfig_system' in msg.topic:
            if hasattr(self, 'on_stop_realtime') and callable(getattr(self, 'on_stop_realtime')):
                self.on_reconfig_system()
            else:
                print('on_reconfig_system not linked')
        else:
            pass

    def on_disconnect(self):
        self.connected = False
        if hasattr(self, 'on_disconnected') and callable(getattr(self, 'on_disconnected')):
            self.on_disconnected()
        else:
            print('on_disconnect not linked')


    def senddata(self, data):
        data = json.dumps(data).strip()
        ret = self.client.publish(self.mad + "/senddata", data) 

    def sendofflinedata(self, data):
        data = json.dumps(data).strip()
        ret = self.client.publish(self.mad + "/offlinedata", data)

    def vpnstarted(self, auth_token):
        data = json.dumps({'auth_token':auth_token})
        ret = self.client.publish(self.mad + "/vpn_started", data)
