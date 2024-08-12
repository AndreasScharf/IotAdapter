import struct

def create_realtime_payload(data):
    # Initialize an empty list to store the byte sequences
    bytes_list = []

    for entry in data:
        md5_hash = entry['md5']  # 16 bytes
        float_value = entry['value']  # float value to be converted to 4 bytes
        
        # Ensure the MD5 hash is exactly 16 bytes
        if len(md5_hash) != 16:
            raise ValueError("MD5 hash must be exactly 16 bytes")

        # Convert the float to 4 bytes (little-endian format)
        float_bytes = struct.pack('<f', float_value)
        
        # Combine MD5 hash and float bytes, and append to the list
        bytes_list.append(md5_hash + float_bytes)

    # Join all byte sequences into a single bytes object
    return b''.join(bytes_list)


