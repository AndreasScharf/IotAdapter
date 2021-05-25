import minimalmodbus
import serial


class rs485(object):
    """docstring for rs485."""
    def __init__(self):
      #inititaliserungs code hier
      
      #falls du globale variablen deklaieren musst kannst du des hier machen z.B
      self.error_count = 0


      #globale variablen müssen immer mit self. aufgerufen werden


    def get(self, port, adress, baudrate, register, code, more=0): #deine Argumente hinter 'self,'

      
      """
      Es ist einfacher jedes mal eine neue Verbindung aufzubauen, falls mehre Geräte angesprochen werden fragt man eins nachdem anderen ab
      oder eben das was man braucht
      """
      try:
        device = minimalmodbus.Instrument(port, adress)
        device.serial.baudrate = baudrate
        device.serial.timeout = 1.0
        #parität(none), stoppbits(1), datenbits(8), Übertragungsart(rtu) ist default und sollte auch bei allen Modbus Geräten so sein
      except serial.serialutil.SerialException:
        print("Port ist nicht bekannt")
        fehler = "Error" 
        return fehler
      except Exception as e:
        fehler = "Unbekannter Fehler: " + str(e)
        print(fehler)
        return "Error"
        
      
      try:
        if more == 0:
          if code == 1:
            ergebnis = device.read_bit(register, code) #Einzelnes Coilregister auslesen
          elif code == 2:
            ergebnis = device.read_bit(register,code) #Einzelnes Statusregister auslesen
          elif code == 3:
            ergebnis = device.read_register(register,0,code) #Einzelnes Halteregister auslesen; integer
          elif code == 4:
            ergebnis = device.read_register(register,0,code) #Einzelnes Eingangsregister auslesen; integer
          elif code == 5:
            code = code - 2
            ergebnis = device.read_float(register,code) #float Halteregister
          elif code == 6:
            code = code - 2
            ergebnis = device.read_float(register,code) #float Eingangsregister
          elif code == 7:
            code = code - 4
            ergebnis = device.read_string(register,16,code) #string im Halteregister auslesen
          elif code == 8:
            code = code -4
            ergebnis = device.read_string(register,16, code) #string im Inputregister auslesen

          return ergebnis
        elif more != 0:
          if code == 1:
            ergebnis = device.read_bits(register, more, code) #mehrere Coilregister hintereinander auslesen
          elif code == 2:
            ergebnis = device.read_bits(register,more, code) #mehrere Statusregister hintereinander auslesen          
          elif code == 3:
            ergebnis = device.read_registers(register, more, code)#Mehrere Halteregister hintereinander auslesen
          elif code == 4:
            ergebnis = device.read_registers(register, more,code)#Mehrere Eingangsregister hintereinadnder auslesen
          return ergebnis

      except minimalmodbus.IllegalRequestError:
        print("Angegebenes Register liegt außerhalb des Registerbereichs des Slaves")
        fehler = "Error"
        return fehler
      except minimalmodbus.InvalidResponseError:
        print("Korrekte Adresse des Slaves muss angegeben werden")
        fehler = "Error"
        return fehler
      except minimalmodbus.NoResponseError:
        print("Baudrate stimmt nicht mit Slave überein, Adresse des Slaves ist 0 oder es besteht keine Verbindung/Verbindung ist unterbrochen")
        fehler = "Error"
        return fehler
      except Exception as e:
        fehler = "Unbekannter Fehler: " + str(e)
        print(fehler)
        return "Error"
    
            
      #Schritte zum lesen 
      #1. Verbindung aufbauen falls nicht vorhanden
      #1.5 Fürs erste übergeben wir den USB Port mit den Parameter später müssen wir den PORT automatisch finden aber des machen wir später
      #2. Datentyp auswählen und entsprechend auswählen
      #3. Register auslesen
      #3.5 Falls nötig Wert umwandeln, wenn es nötig ist das du sowas wie 'Floating Point IEEE754' brauchst sag bescheid da hab ich was fertig
      #4. Wert zurückgeben


      #Es können nur Coils oder Holdingregister beschrieben werden
    def set(self, port, adress, baudrate, register, code, value=0, more_values=0):
      connect = "COM" + str(port)
      try:
        device = minimalmodbus.Instrument(connect, adress)
        device.serial.baudrate = baudrate
        device.serial.timeout = 1.0
        #parität(none), stoppbits(1), datenbits(8), Übertragungsart(rtu) ist default und sollte auch bei allen Modbus Geräten so sein
      except serial.serialutil.SerialException:
        print("T")
        fehler = "Port ist nicht bekannt" 
        return fehler
      except Exception as e:
        fehler = "Unbekannter Fehler: " + str(e)
        return fehler

      try: 
        if more_values == 0: 
          if code == 5:
            device.write_bit(register, value, code)# beschreibt einzelne Coil; boolean
          elif code == 6:
            device.write_register(register, value, 0, code) #beschreibt einzelnes Holdingregister; integer
          elif code == 16:
            device.write_float(register, value)#beschreibt Holdingregister; float
        else:
          if code == 15:
            device.write_bits(register, more_values)#beschreibt mehrere Coils;boolean
          elif code == 16:
            device.write_registers(register, more_values) #beschreibt mehrere Holdingregister; integer
      except Exception as e:
        fehler = str(e)
        print(fehler)
        return fehler
