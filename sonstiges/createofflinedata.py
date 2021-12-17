import sys
from datetime import datetime
import pandas as pd
import random
today = sys.argv[1]

if not today:
    today = '18-11-19'

date_time_obj = datetime.strptime(today, '%d-%m-%y')

start_second = datetime.now().second
lines = []
for i in range(288):
    value = random.uniform(0, 1)

    lines.append(f'{{ "name":"MAD", "unit": "", "value":"gfs_test"}}')
    lines.append(f'{{ "name":"time", "unit": "", "value":"{date_time_obj}"}}')
    lines.append(f'{{ "name":"value1", "unit": "", "value":"{value}" }}')

    date_time_obj = date_time_obj + pd.DateOffset(minutes=5)

str = '\n'.join(lines)
f = open('./' + today + '.json', 'w')
f.write(str)