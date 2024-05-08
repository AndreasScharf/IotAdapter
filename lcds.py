import hashlib
import struct
from datetime import datetime, timezone
import os

LCDS_PATH = '/home/pi/Documents/lcds-dump'

def start_lcds():
    if not os.path.isdir(LCDS_PATH):
        os.makedirs(LCDS_PATH)

def lcds_safe_line(mad, valuename, timestemp, value):
    # create file format
    file_path = timestemp.strftime("%Y_%m_%d") + '.hex'

    # create line bytes
    line_content = line_to_hex_format(mad, valuename, timestemp, value)

    # append hex line to the file
    f = open(LCDS_PATH + "/" + file_path, 'a+b')
    f.write(line_content)
    f.close()

def line_to_hex_format(mad, valuename, timestemp, value):
    # create a byte array with 28 bytes

    # create md5 identifiyer of the current value (16 bytes)
    identifier_str = mad + valuename
    identifier_md5 = hashlib.md5(identifier_str.encode()).digest()
   
    # convert date to 4 bytes
    timestemp_hex = date_to_bytes(timestemp)

    # convert messurement (float) to 4 bytes
    value_hex = float_to_bytes(value)

    # concat everything together
    return identifier_md5 + timestemp_hex + value_hex


# converts a datetime object to integer and then to bytes
def date_to_bytes(date_obj):
    # Convert date object to Unix timestamp
    timestamp = int(date_obj.replace(tzinfo=timezone.utc).timestamp())
    # Convert timestamp to bytes using struct.pack
    return struct.pack('>I', timestamp)


# converts a number(float) into 4 bytes
def float_to_bytes(float_num):
    # Pack the float into bytes using IEEE 754 standard (32-bit float)
    return struct.pack('f', float_num)


def test():
    from datetime import datetime, timezone
    line_hex = line_to_hex_format('ABC123', 'Hallentemperatur', datetime(2024, 5, 8, 11, 30, 0, tzinfo=timezone.utc), 3.14)

    print(line_hex)

#test()