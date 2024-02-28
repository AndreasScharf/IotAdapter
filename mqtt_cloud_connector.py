import paho.mqtt.client as mqtt
import ssl
import time
import json
import threading

class connector(object):
    def __init__(self):
        self.connected = False
        self.not_reconnect = False
        
        self.mqtt_thread = 0
       
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
            del self.client

        self.client = mqtt.Client( mqtt.CallbackAPIVersion.VERSION2 )
            
            
        self.client.tls_set(
                ca_certs='/home/pi/Documents/IotAdapter/keys/ca-crt.pem', 
                certfile='/home/pi/Documents/IotAdapter/keys/client1-crt.pem', 
                keyfile='/home/pi/Documents/IotAdapter/keys/client1-key.pem',
                cert_reqs=ssl.CERT_NONE) # <--- even without arguments
        self.client.disable_logger()
        
        if self.client.callback_api_version == mqtt.CallbackAPIVersion.VERSION2:
            self.client.on_connect = lambda client, userdata, flags, rc, props: self.on_connect(client, userdata, flags, rc)
            self.client.on_message = lambda client, userdata, msg : self.on_message(client, userdata, msg)
            self.client.on_disconnect = lambda client, userdata, disconnect_flags, reason_code, properties: self.on_disconnect()
        elif self.client.callback_api_version == mqtt.CallbackAPIVersion.VERSION1:
            self.client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
            self.client.on_message = lambda client, userdata, msg : self.on_message(client, userdata, msg)
            self.client.on_disconnect = lambda client, userdata, disconnect_flags: self.on_disconnect()
        else:
            print('No MQTT Version Stored')
        
        self.client.username_pw_set(username="mqtt", password="mqttpw1337")
        try:
            # need to connect in async mode
            self.connect_async(host, port, 60)
            self.start_mqtt_loop()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            if not reconnect:
                self.on_disconnect()
            
    def on_connect(self, client, userdata, flags, rc):
        try:
            print('connected::')
            ret = self.client.publish(self.mad + "/alive", self.mad) 
            print(ret)
            self.connected = True
            print('connection established')

            self.client.subscribe( self.mad + "/recievedata")

            self.client.subscribe( self.mad + "/startvpn")
            self.client.subscribe( self.mad + "/stopvpn")

            self.client.subscribe( self.mad + "/start_realtime")
            self.client.subscribe( self.mad + "/stop_realtime")
            
            self.client.subscribe(self.mad + "/reconfig_system")
            self.client.subscribe(self.mad + "/update_system")

            # subscripe to the shell cmd listener
            self.client.subscribe(self.mad + "/shell-cmd")
        
        except Exception as e:
            # Broken PIPE ERROR
            print(e)
            
            self.connected = False
            self.on_disconnect()

        if hasattr(self, 'on_connected') and callable(getattr(self, 'on_connected')):
            self.on_connected()

    # thread safe calling of the mqtt functions
    def connect_async(self, host, port, keepalive):
        
        def connect(host, port, keepalive):
            print('Start MQTT Connection')
            try:
                # blocking function
                self.client.connect(host, port, keepalive)
            except Exception as e:
                print('MQTT Connection Error', e)
            
        connection_thread = threading.Thread(target=connect, args=(host, port, keepalive), daemon=True)
        connection_thread.start()
        
            
        
    
    def start_mqtt_loop(self):
        if self.mqtt_thread: 
            return
        
        self.mqtt_thread = threading.Thread(target=self.mqtt_loop, args=(1,),  daemon=True)
        self.mqtt_thread.start()
        
    def mqtt_loop(self, args):
        
        while 1:
            try:
                self.client.loop()    
                print('MQTT Loop')
            except Exception as e:
                print(e)
                
            time.sleep(0.5)
        
        
                    
    # due to qos being 0, this might not be recieved proberly. Also it can be triggered multiple times
    def on_message(self, client, userdata, msg):
        if not (self.mad in msg.topic):
            return
        
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
                self.on_reconfig_system(msg.payload)
            else:
                print('on_reconfig_system not linked')
        elif '/update_system' in msg.topic:
            if hasattr(self, 'on_update') and callable(getattr(self, 'on_update')):
                try:
                    data = json.loads(msg.payload)
                    self.on_update(data)
                except:
                    print('not a json')
            else:
                print('on_update not linked')
        elif '/shell-cmd' in msg.topic:
            if hasattr(self, 'on_shell_cmd') and callable(getattr(self, 'on_shell_cmd')):
                try:
                    data = json.loads(msg.payload)
                    self.on_shell_cmd(data)
                except Exception as e:
                    print(e)
            else:
                print('on_shell_cmd not linked')
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
        (rc, mid) = self.client.publish(self.mad + "/senddata", data) 
        
        # if message doesnt goes trough 
        # enable reconnect
        if rc == mqtt.MQTT_ERR_NO_CONN:
            self.connected = False

    def sendofflinedata(self, data):
        data = json.dumps(data).strip()
        topic = self.mad + "/offlinedata"
        (rc, mid) = self.client.publish(topic=topic, payload=data, qos=1)
        # if message doesnt goes trough 
        # enable reconnect
        if rc == mqtt.MQTT_ERR_NO_CONN:
            self.connected = False

        # return True if Success other wise return false
        return rc == mqtt.MQTT_ERR_SUCCESS       

    def vpnstarted(self, auth_token):
        data = json.dumps({'auth_token':auth_token})
        ret = self.client.publish(self.mad + "/vpn_started", data)
        
    def setupinputs(self, inputs):
        print(self.mad + "/setupinputs")
        data = json.dumps(inputs)
        ret = self.client.publish(self.mad + "/setupinputs", data)

    def confirminputs(self, inputs):
        data = json.dumps(inputs)
        ret = self.client.publish(self.mad + "/confirminputs", data)

    def shell_response(self, response):
        data = json.dumps(response)
        ret = self.client.publish(self.mad + "/shell-response", data)
