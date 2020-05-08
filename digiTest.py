from gpiozero import MCP3008

multiplier = 1
adc = MCP3008(channel=0)
vol = 3.3 * adc.value * multiplier

print('Temperatur: ' +  vol + '°C')

adc = MCP3008(channel=1)
vol = 3.3 * adc.value * multiplier

print('Pressure: ' +  vol + 'bar')
