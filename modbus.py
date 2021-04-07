#deine Imports hier

class rs485(object):
    """docstring for rs485."""
    def __init__(self):
      #inititaliserungs code hier
      
      #falls du globale variablen deklaieren musst kannst du des hier machen z.B
      self.error_count = 0
      #globale variablen müssen immer mit self. aufgerufen werden


    def get(self, ): #deine Argumente hinter 'self,'
      #Schritte zum lesen 
      #1. Verbindung aufbauen falls nicht vorhanden
      #1.5 Fürs erste übergeben wir den USB Port mit den Parameter später müssen wir den PORT automatisch finden aber des machen wir später
      #2. Datentyp auswählen und entsprechend auswählen
      #3. Register auslesen
      #3.5 Falls nötig Wert umwandeln, wenn es nötig ist das du sowas wie 'Floating Point IEEE754' brauchst sag bescheid da hab ich was fertig
      #4. Wert zurückgeben
    
      return 'Hello There'
    def set(self, ):
      return 1337