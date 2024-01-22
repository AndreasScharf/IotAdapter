def get_mobil_usage():
    rx_bytes, tx_bytes, error = get_network_bytes('wwan0')
    
    if error:
        print('no wwan0 Adapter')
        return (0, 0, 0)
    
    return (rx_bytes, tx_bytes, int(rx_bytes) + int(tx_bytes))
          
def get_network_bytes(interface):
    for line in open('/proc/net/dev', 'r'):
        if interface in line:
            data = line.split('%s:' % interface)[1].split()
            rx_bytes, tx_bytes = (data[0], data[8])
            return (rx_bytes, tx_bytes, None)
        
    return (0, 0, 'no wwan')
if __name__ == '__main__':
    get_mobil_usage()