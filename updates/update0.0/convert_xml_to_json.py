from xml.dom import minidom
from collections import OrderedDict
import json
json_file = {
  "ip":"85.214.215.187",
  "port": 5000,
  "mad": "",
  "data": []
}

mydoc = minidom.parse('/home/pi/Documents/IotAdapter/konfig.xml')
values = mydoc.getElementsByTagName('value')

for elem in values:
    row = {}
    row['active'] = 'true'
    typ = elem.attributes['typ'].value
    name = elem.attributes['name'].value
    unit = elem.attributes['unit'].value
    row['type'] = typ
    row['name'] = name
    row['unit'] = unit

    if name == 'MAD':
        json_file['mad'] = elem.attributes['values'].value

    if typ == 'static':
        val = elem.attributes['values'].value
        row['value'] = val

    elif typ=='S7':
        row['type'] = 's7'

        row['ip'] = elem.attributes['IP'].value
        row['db'] = elem.attributes['DB'].value
        row['offset'] = elem.attributes['start'].value
        row['length'] = elem.attributes['length'].value
        row['datatype'] = elem.attributes['datatype'].value
    json_file['data'].append(row)
f = open('/home/pi/Documents/IotAdapter/config.json', 'w+')
f.write(json.dumps(OrderedDict(json_file)))
f.close()
