import time
import random
import socket
import json
from datetime import datetime

lastNumber = 7
intervall = 900
ipAdress = '85.214.215.187'
port = 12000

def rauschen(a, b):
    global lastNumber
    oddEqualEven = random.randint(1, 4)
    if (oddEqualEven % 3 == 0):
        #up
        try:
            newNumber = random.randint(int(lastNumber*10), int(b*10) + 1)
            newNumber = float(newNumber / 10)
            lastNumber = newNumber;
            return newNumber;
        except:
            return lastNumber;
    elif (oddEqualEven % 3 == 1):
        newNumber = lastNumber
        return newNumber
    else:
        #down
        try:
            newNumber = random.randint(int(a*10), int(lastNumber*10) + 1)
            newNumber = float(newNumber / 10)
            lastNumber = newNumber;
            return newNumber;
        except:
            return lastNumber;
def builddata():
    data = []

    data.append({"name": "MAD", "unit" : "", "value": "pfzsup"})
    data.append({"name": "time", "unit" : "", "value": str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))})
    data.append({"name": "Ph_wert", "unit" : "ph", "value": str(rauschen(6.5, 8.5))})

    #remove the last dot
    #builds commandString
    return data


while 1:
    gesendet = False
    while not gesendet:
        print('sending...')
        try:
            tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp.connect((ipAdress, port))
            print(json.dumps(builddata()))
            tcp.send(bytes(json.dumps(builddata()), 'utf-8'))
            gesendet = True

        except:
            print('error')
            tcp.close()
        finally:
        	tcp.close()

    print('idle')

    time.sleep(intervall)
