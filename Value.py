class Value:
    def __init__(self, name, typ, channel, multiplier, unit, val, plc = None, dbblock = None, start = None, length = None, datatype = None):
        self.name = name
        self.typ = typ
        self.channel = channel
        self.multiplier = multiplier
        self.unit = unit
        self.val = val
        #Siemensmaschine
        self.plc = plc
        self.dbblock = dbblock
        self.start = start
        self.length = length
        self.datatype = datatype
