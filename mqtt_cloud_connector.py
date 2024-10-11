import paho.mqtt.client as mqtt
import ssl
import time
import json
import threading
import hashlib
import requests
import time

from utils import create_realtime_payload
import os

class CertificateError(Exception):
    """Custom exception for specific error handling."""
    pass


CERT_DIR = '/home/pi/Documents/IotAdapter/keys/'
SSL_CA_PATH = os.getenv('SSL_CA_PATH', f'{CERT_DIR}ca-crt.pem')
SSL_CERT_PATH = os.getenv('SSL_CERT_PATH', f'{CERT_DIR}client1-crt.pem')
SSL_KEY_PATH = os.getenv('SSL_KEY_PATH',  f'{CERT_DIR}client1-key.pem')

DEVICE_FINGERPRINT = os.getenv('FINGERPRINT', 0)
PKI_HOST = os.getenv('PKI_HOST', 'https://cdm.frappgmbh.de')

class connector(object):
    def __init__(self, mad=False):
        self.connected = False
        self.not_reconnect = False
        
        self.mqtt_thread = 0

        self.rt_data_object = []

        self.pki_request_allowed = 0

        if mad:
            self.mad = mad
       
    def load_ssl_chain(self):
        if not self.client: raise CertificateError('No Client defined')

        # if all files exist execute loading ssl chain
        if os.path.isfile(SSL_CA_PATH) and os.path.isfile(SSL_CERT_PATH) and os.path.isfile(SSL_KEY_PATH):
            try:
                self.client.tls_set(
                    ca_certs=SSL_CA_PATH, 
                    certfile=SSL_CERT_PATH,
                    keyfile=SSL_KEY_PATH,
                    cert_reqs=ssl.CERT_NONE) # <--- even without arguments
                
                return 0
            except Exception as e:
                print(e)
                raise CertificateError(e)
                
        else:
            
            error_text = ('' if os.path.isfile(SSL_CA_PATH) else '[MQTT Client] SSL_CA_PATH does not exitst\n') + ('' if os.path.isfile(SSL_CERT_PATH) else '[MQTT Client] SSL_CA_PATH does not exitst\n') + ('' if os.path.isfile(SSL_KEY_PATH) else '[MQTT Client] SSL_CA_PATH does not exitst\n')
            

            raise CertificateError(error_text)
     

    def pki_request_check(self):
        # if file exists do not make new request
        if os.path.isfile(SSL_CA_PATH) and os.path.isfile(SSL_CERT_PATH) and os.path.isfile(SSL_KEY_PATH):
            return True

        self.pki_request_certificates()

    def pki_request_certificates(self):

        # wait for the next time to do a PKI Request
        if time.time() < self.pki_request_allowed:
            print('Not yet')
            return
        
        # set new allowed time for next request
        self.pki_request_allowed = time.time() + 5 * 60


        url = f'{PKI_HOST}/pki/get-certificates'
        data = {
            'fingerprint': DEVICE_FINGERPRINT
        }
        try:
            print('[PKI] Certificate Request')

            # Make the POST request
            response = requests.post(url, json=data)

            # Check the response
            if response.ok:
                data = response.json()
                with open(SSL_CA_PATH, 'w') as f:
                    f.write(data['caCert'])

                with open(SSL_CERT_PATH, 'w') as f:
                    f.write(data['cert'])

                with open(SSL_KEY_PATH, 'w') as f:
                    f.write(data['key'])
                
                self.load_ssl_chain()
                
            else:
                print(f'[PKI] Failed with status code {response.status_code}')
                print('[PKI] Error:', response.text)
        except Exception as e:
            print(f'[PKI] Failed with {e}')

    def connect(self, host, port, mad, reconnect=False, request_certs=False ):
        
        self.mad = mad
        self.host = host
        self.port = port
        if self.connected:
            return
         
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False  # Without this line, I does not work
        print('[MQTT Client] connecting...', self.connected)
        if hasattr(self, 'client'):
            self.client.disconnect()
            del self.client

        self.client = mqtt.Client( mqtt.CallbackAPIVersion.VERSION2, client_id=mad )
        
        # problem
        try:
            # this one is called after a connection with bad certificate was established
            if request_certs:
                time.sleep(1 * 60)
                raise CertificateError()
            
            self.load_ssl_chain()
        except CertificateError:
            self.pki_request_certificates()
        
        
        self.client.disable_logger()
        
        if self.client.callback_api_version == mqtt.CallbackAPIVersion.VERSION2:
            self.client.on_connect = lambda client, userdata, flags, rc, props: self.on_connect(client, userdata, flags, rc)
            self.client.on_message = lambda client, userdata, msg : self.on_message(client, userdata, msg)
            self.client.on_disconnect = lambda client, userdata, disconnect_flags, reason_code, properties: self.on_disconnect(client, userdata, disconnect_flags, reason_code, properties)
        elif self.client.callback_api_version == mqtt.CallbackAPIVersion.VERSION1:
            self.client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
            self.client.on_message = lambda client, userdata, msg : self.on_message(client, userdata, msg)
            self.client.on_disconnect = lambda client, userdata, disconnect_flags: self.on_disconnect()
        else:
            print('No MQTT Version Stored')
        
        self.client.username_pw_set(username="mqtt", password="mqttpw1337")
        try:
            # need to connect in async mode
            self.client.connect_async(host, port, 60)
            self.client.loop_start()
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print('Error While Connecting')
            if not reconnect:
                self.on_disconnect()
            
    
    def on_connect(self, client, userdata, flags, rc):
        try:
            # if connection is not accepted 
            # check for bad certificate
            if not rc == mqtt.CONNACK_ACCEPTED:
                pass
                #self.bad_certificate_handler()
                #return

            ret = self.client.publish(self.mad + "/alive", self.mad) 
            self.connected = True
            print('[MQTT Client] connection established')

            self.client.subscribe( self.mad + "/recievedata")

            self.client.subscribe( self.mad + "/startvpn")
            self.client.subscribe( self.mad + "/stopvpn")

            self.client.subscribe( self.mad + "/start-realtime")
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
        
    def bad_certificate_handler(self):
        print('[PKI] bad_certificate_handler')

        # first disconnect from mqtt broker
        self.client.disconnect()

        # reconnect with new certificate request
        self.connect(host=self.host, port=self.port, mad=self.mad, request_certs=True)

        
    def thread_is_alive(self):
        thread_alive = self.client and self.client._thread and self.client._thread.is_alive()

        if not thread_alive:
            print( self.client , self.client._thread , self.client._thread.is_alive())

        return thread_alive
        
                    
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
        elif '/start-realtime' in msg.topic:
            if hasattr(self, 'on_start_realtime') and callable(getattr(self, 'on_start_realtime')):
                self.on_start_realtime(msg.payload)
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

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        print(disconnect_flags, reason_code)
        self.connected = False
        if hasattr(self, 'on_disconnected') and callable(getattr(self, 'on_disconnected')):
            self.on_disconnected()
        else:
            print('on_disconnect not linked')

    def senddata(self, data):
        data = json.dumps(data).strip()

        try:
            (rc, mid) = self.client.publish(self.mad + "/senddata", data) 
            
            # if message doesnt goes trough 
            # enable reconnect
            if rc == mqtt.MQTT_ERR_NO_CONN:
                self.connected = False
        except:
            self.connected = False
            self.not_reconnect = True

    def sendofflinedata(self, data):
        data = json.dumps(data).strip()
        topic = self.mad + "/offlinedata"
        try:
            (rc, mid) = self.client.publish(topic=topic, payload=data, qos=1)
            # if message doesnt goes trough 
            # enable reconnect
            if rc == mqtt.MQTT_ERR_NO_CONN:
                self.connected = False

            # return True if Success other wise return false
            return rc == mqtt.MQTT_ERR_SUCCESS       
        except:
            self.connected = False
            self.not_reconnect = True
            return False

    def vpnstarted(self, auth_token):
        data = json.dumps({'auth_token':auth_token})
        try:
            ret = self.client.publish(self.mad + "/vpn_started", data)
        except:
            self.connected = False
            self.not_reconnect = True

    def setupinputs(self, inputs):
        print(self.mad + "/setupinputs")
        data = json.dumps(inputs)
        try:
            ret = self.client.publish(self.mad + "/setupinputs", data)
        except:
            self.connected = False
            self.not_reconnect = True

    def confirminputs(self, inputs):
        data = json.dumps(inputs)
        try:
            ret = self.client.publish(self.mad + "/confirminputs", data)
        except:
            self.connected = False
            self.not_reconnect = True

    def shell_response(self, response):
        data = json.dumps(response)
        try:
            ret = self.client.publish(self.mad + "/shell-response", data)
        except:
            self.connected = False
            self.not_reconnect = True

    def set_realtime_object(self, valuenames):
        self.rt_data_object = []
        for vn in valuenames:
            self.rt_data_object.append({ "name": vn, "md5": hashlib.md5(vn.lower().encode()).digest(), "value": 0, "updated": False })
    
    def set_realtime_value(self, name, value):
        
        for row in self.rt_data_object:
            if row['name'] == name:
                
                row['value'] = value
                row['updated'] = True
        
        if not len(self.rt_data_object):
            return 0

        # after every set check if real time data object is ready to send
        for row in self.rt_data_object:
            if not row['updated']:
                return 0
       
        
        
        # full data object
        try:
            payload = create_realtime_payload(self.rt_data_object)
            self.client.publish(self.mad + "/send-realtime", payload=payload)
        except ValueError:
            pass
        except:
            self.connected = False
            self.not_reconnect = True

        for row in self.rt_data_object:
            row['updated'] = False

        time.sleep(1)

    def send_error_value(self, name, value):
        
        md5_name = hashlib.md5(name.lower().encode()).digest()
        payload_object = [{ "md5":md5_name, "value": value }]
  
        try:
            payload = create_realtime_payload(payload_object)
            self.client.publish(self.mad + "/send-realtime", payload=payload)
        except ValueError:
            pass
        except:
            self.connected = False
            self.not_reconnect = True


def main():
    print('MQTT Connector Test')
    mqtt_con = connector()
    mqtt_con.connect('localhost', 1883, 'bccef5c1-083b-4da7-a286-a6300bd3d279')

    while 1:
        pass

if __name__ == "__main__":
    main()