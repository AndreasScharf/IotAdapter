import requests
from zipfile import ZipFile
import getpass

host = 'https://cdm-test.frappgmbh.de'
print('PIK:')
u = input('Your Username: ')
p = getpass.getpass('Passphrase: ')
res = requests.post(url='{host}/maschines/get-keys'.format(host=host), data={
    'name': u, 'passphrase': p
})
if res.status_code > 200:
    print('Wrong Authendication')
    exit()
    
open('keys.zip', 'wb').write(res.content)
with ZipFile('keys.zip', 'r') as zip:

 # printing all the contents of the zip file

  zip.printdir()

# extracting all the files in current working directory

  zip.extractall('/home/pi/Documents/IotAdapter/')
