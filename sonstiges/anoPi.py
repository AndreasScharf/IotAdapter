from python_anopi import AnoPi

a = AnoPi()

for i in range(4):
    value, err = a.ai_mA(i)  # For Analog Input 0
    print('AI {index}: {value}mA'.format(index=i, value=value))
