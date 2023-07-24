# IotAdapter

## Installation

### Standalone Installation
```
# Downloading the github Repository
git clone https://github.com/AndreasScharf/IotAdapter.git ~/Documents/IotAdapter

# Installing Packages & Dependencies
cd ~Documents/IotAdapter
sh installer.sh standalone
```

### Integrated Installation
The Integrated Installation, will be done automaticlly be the frapp Automation Installation.

## Raspberry Enviroment
### Debug the Config File and the automation enviroment
```
# move into IotAdapter folder
cd ~/Documents/IotAdapter

# stop process manager from executing iot
pm2 stop iot

# execute iotadapter.py with debug flag
python3 iotadapter.py

```

### Change IP Adress of Raspberry
First open the DHCP configuration file of the Raspberry Pi
```
sudo nano /etc/dhcpcd.conf
```

Uncomment the following block to enable a static eth0 interface, and set the ip to the desired one.
```
# Example static IP configuration:
#interface eth0
#static ip_address=192.168.0.10/24
#static ip6_address=fd51:42f8:caae:d92e::ff/64
#static routers=192.168.0.1
#static domain_name_servers=192.168.0.1 8.8.8.8 fd51:42f8:caae:d92e::1
```

to, the IP and subnetmask is in cider notation e.g. 192.168.10.199/24 is equal to a subnetmask 255.255.255.0 /16 is equal to 255.255.0.0 ...

```
# Example static IP configuration:
interface eth0
static ip_address=192.168.10.199/24
#static ip6_address=fd51:42f8:caae:d92e::ff/64
static routers=192.168.10.1
static domain_name_servers=8.8.8.8
```

