import snap7

s7 = snap7.client.Client()
s7.connect('192.168.14.61', 0, 1)
result = s7.db_read(101, 0.1, 0.)
print(get_bool(result, 0))
#läuft nix
