import json
path = '/home/pi/Documents/IotAdapter/config.json'
rf = open(path, 'r')
config = json.loads(rf.read())
config['domain'] = 'mqtt://mqtt.enwatmon.de:1883'

if 'ip' in config and 'port' in config:
    del config['ip']
    del config['port']

wf = open(path, 'w')
wf.write(json.dumps(config))
rf.close()
wf.close()
