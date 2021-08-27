from paramiko import client
from monvpn import vpnclient

c = vpnclient('192.168.10.1', 'root', 'Enwat2007!')
ca_root = '''-----BEGIN PRIVATE KEY-----
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
YWPIANsw3Db2NcbC0bPJnJGT09By3h4b
-----END PRIVATE KEY-----
'''
client_key = '''-----BEGIN PRIVATE KEY-----
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
yxFaVYtZOJLBENZZKXq1qewa9Di8Sw==
-----END PRIVATE KEY-----
'''
client_cer = '''
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 3 (0x3)
        Signature Algorithm: sha1WithRSAEncryption
        Issuer: C=DE, ST=BA, L=Bamberg, O=frapp, CN=frapp CA/emailAddress=as@frappgmbh.de
        Validity
            Not Before: Jun 24 08:31:19 2021 GMT
            Not After : Jun 22 08:31:19 2031 GMT
        Subject: C=DE, ST=BA, L=Bamberg, O=frapp, CN=user2/emailAddress=as@frappgmbh.de
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                RSA Public-Key: (4096 bit)
                Modulus:
                    00:cd:d6:b4:96:53:6d:8a:75:65:ba:32:e8:2f:73:
                    b7:81:6e:21:66:34:2c:4d:08:c8:b7:b1:43:9b:b7:
                    5d:d0:82:6a:ed:01:8f:95:6e:86:b8:28:1c:df:ca:
                    4a:b9:62:e4:fe:4f:fe:32:8f:63:40:a2:32:20:d7:
                    22:6e:02:04:70:30:47:80:71:ba:c2:f0:48:f2:f4:
                    a2:f6:cd:b1:5a:53:57:ee:fb:18:5e:28:db:77:35:
                    b5:f0:88:40:da:32:a4:e0:36:21:47:7d:2e:9f:4f:
                    44:50:92:07:37:ad:80:ee:7b:d1:ef:4a:f9:35:22:
                    9c:4a:76:d0:f8:fd:77:c3:ca:dc:f5:99:5f:9c:e3:
                    b5:5d:e5:61:66:79:20:8c:d2:47:6a:bb:bd:c5:a4:
                    d4:1f:4f:8f:e3:78:5f:a6:60:6e:04:7d:7d:39:9e:
                    38:d0:e8:5f:0e:7d:c8:ee:c3:ef:ee:a2:42:cd:54:
                    19:1f:a2:bb:26:07:84:b9:c8:7d:c3:54:2a:d5:8c:
                    02:59:07:17:00:5b:f9:c5:d7:b4:81:e2:b4:7e:44:
                    4c:38:1d:3d:b6:da:49:a9:f1:69:61:fe:35:27:cd:
                    7d:1f:e7:d3:92:72:89:04:21:27:0a:c7:e2:78:01:
                    ea:c3:e2:38:c2:3a:3b:25:57:d1:13:a8:74:67:4a:
                    58:0a:9c:a8:09:6d:5f:1f:83:dc:ae:f4:69:80:d7:
                    f8:95:58:ea:6e:e1:c1:2a:89:6d:0b:97:40:65:3a:
                    b3:25:ec:a0:11:1d:5b:98:71:05:1c:62:1f:99:e2:
                    08:14:99:f6:d9:07:0a:6e:30:72:0f:f4:95:73:ad:
                    75:70:dd:b8:4e:d1:55:ca:6c:85:a0:ba:cb:a4:2f:
                    57:3e:9c:8b:9e:84:05:77:13:a6:44:85:f4:62:ae:
                    1d:23:d5:95:20:69:1e:6d:de:c2:c5:c5:75:21:bc:
                    b5:75:94:c1:34:c5:cc:a5:a7:dc:98:89:c3:17:e2:
                    1b:d0:15:e5:f9:4b:89:05:15:4c:ff:8f:13:4e:f6:
                    2f:0f:97:34:15:d5:31:3b:3c:74:ce:5a:0c:92:80:
                    d2:f6:02:e0:43:af:4b:d2:d6:5f:63:32:5c:f7:7f:
                    9d:e7:f2:28:fe:62:68:e0:63:cc:4a:8a:b8:a9:d1:
                    18:90:4b:6f:5d:c0:5e:b6:1d:74:7a:1e:f6:d3:f6:
                    3c:e3:e2:d9:ad:9b:04:fe:a0:fb:2b:ea:3b:ad:67:
                    b7:1c:a2:f0:bf:ba:80:89:7e:62:2a:39:fb:78:4b:
                    cd:91:6a:a2:2e:cf:b4:8b:e8:23:97:b0:fa:49:63:
                    11:5d:b7:fb:d4:be:2a:69:d3:44:99:a0:59:3a:af:
                    33:a0:4f
                Exponent: 65537 (0x10001)
        X509v3 extensions:
            X509v3 Basic Constraints: 
                CA:FALSE
            Netscape Comment: 
                Easy-RSA Generated Certificate
            X509v3 Subject Key Identifier: 
                98:E6:28:A6:54:CA:88:5B:1C:BC:82:D4:27:FA:EF:73:C2:2E:86:F6
            X509v3 Authority Key Identifier: 
                keyid:F6:B8:34:85:DF:0C:12:38:59:26:EC:7A:FD:1D:26:D1:0B:0E:49:7F
                DirName:/C=DE/ST=BA/L=Bamberg/O=frapp/CN=frapp CA/emailAddress=as@frappgmbh.de
                serial:41:D3:0E:E6:F3:C5:B7:AF:0F:24:70:17:CD:61:61:01:2C:AD:39:26

            X509v3 Extended Key Usage: 
                TLS Web Client Authentication
            X509v3 Key Usage: 
                Digital Signature
    Signature Algorithm: sha1WithRSAEncryption
         56:81:0a:06:a3:d1:06:25:90:92:90:c1:f1:81:76:82:9e:e6:
         39:23:24:3e:56:c0:94:6a:36:ac:81:57:ce:1a:ee:2a:8d:50:
         38:d7:a8:78:53:7c:c0:5f:76:63:f0:7d:d3:f2:c6:3d:8e:90:
         f7:a8:82:80:fb:c9:b3:31:be:03:b5:83:ab:c3:6f:df:00:c6:
         de:32:9b:e4:f1:a9:f2:cc:4e:3d:58:d1:b7:7e:73:27:0c:b1:
         47:2c:2a:f9:82:0c:d5:5c:bf:f5:f4:67:c9:3e:6a:07:80:e0:
         63:07:e4:22:b7:ff:96:68:ad:30:cc:08:44:73:31:9a:1a:d8:
         7d:c3:15:f8:21:64:97:b1:54:8d:c6:2c:75:f8:1c:1e:89:df:
         29:35:0c:0b:be:6b:0d:78:2e:24:8d:4f:ad:07:9b:79:8b:a4:
         0e:28:73:d5:32:c7:30:50:4f:9f:be:87:42:69:0f:2f:82:8e:
         b3:da:04:e3:c1:fa:77:51:13:dc:4e:21:cb:3b:76:27:85:6a:
         5a:c4:be:44:22:69:da:09:43:f9:31:f1:fd:49:16:5c:0b:0c:
         82:c4:63:45:48:fd:50:7e:6b:54:05:c8:7a:ae:6f:ed:3c:9f:
         2a:41:4d:99:e4:72:1d:73:9a:5d:7a:27:00:e0:e0:35:1a:59:
         14:1d:8b:ae:ab:c2:f2:78:6a:b7:f9:4d:2a:04:17:3d:49:e8:
         99:bc:62:9a:42:b2:f1:b2:64:c8:4e:8f:95:e7:96:e9:3e:41:
         ce:f1:7f:49:61:2f:8f:b4:92:43:0a:4a:45:2e:90:6e:38:71:
         ad:f0:03:6d:ef:cd:01:bb:71:18:d9:b6:d0:53:04:ba:61:06:
         32:60:f7:b8:1a:71:9f:cb:c0:51:b5:e6:f8:c0:c8:fc:9d:7c:
         60:5f:76:94:5e:d7:e8:f4:af:19:b7:3d:9e:72:4b:0f:94:ef:
         43:c6:13:e8:9b:63:c8:6e:ed:dd:ac:2e:33:5c:fd:99:0e:b5:
         f8:75:57:4c:88:2f:59:b6:ea:0b:c7:e2:37:3a:0c:76:6f:49:
         65:ce:53:e7:57:b6:76:c0:c7:28:90:89:9c:80:1a:46:38:a5:
         58:d9:8f:f3:46:66:34:81:51:80:0c:2a:7e:61:c2:65:97:7a:
         72:c5:d6:2c:78:fc:3b:a2:c4:b4:ad:47:9f:82:cb:4a:d4:77:
         57:dc:3d:30:c8:8b:65:bb:e8:79:c0:c8:4f:5e:c9:52:6e:1e:
         c3:df:e0:fc:64:cc:08:2d:7d:3a:7e:9d:bf:cf:25:6b:5d:27:
         79:9e:51:7a:6a:89:2d:ed:47:1d:20:9b:5f:46:02:cc:13:1a:
         73:82:df:00:41:dc:7b:3a
-----BEGIN CERTIFICATE-----
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
-----END CERTIFICATE-----
'''
ta_key = '''#
# 2048 bit OpenVPN static key
#
-----BEGIN OpenVPN Static key V1-----
15716c701f93a331e0ec435436a55bb1
b32a55590fa27972e82be455ae450841
dbc6629fcdd61a02e053c58823e53536
0b1262219d4a8582d86ceb08f07d3ed2
28d0763d22513274729f686bb05571ba
32bd7e68b3726bfd0ec6466ffbeaacbb
934223dcd94354fd734b93367bfd1559
0d59df3dd0b7b4fb3f08c5afca44b321
ab828a501b467a5f8521b3e0c1e67324
4951f8e29fdadb733881f26f643e6ede
f36f7df44a3f6586ebd6e97818365547
af6bdc6b78b22340005641695505f926
09bbf403b875f79420ba4e6046fdbf93
2b676b31defa67a98c167e7fc18c7489
c2cdd741aa673ab0834584ff85d12718
bd9b275535a6cd4b8558dfa296f7d1c4
-----END OpenVPN Static key V1-----
'''

c.start(51001, ca_root, client_key, client_cer, ta_key)
