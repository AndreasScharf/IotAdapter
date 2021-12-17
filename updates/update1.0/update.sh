sudo pip3 install pi-ina219
sudo pip3 install paho-mqtt
sudo pip3 install psutil

sudo pip3.8 install pi-ina219
sudo pip3.8 install paho-mqtt
sudo pip3.8 install psutil

cp /home/pi/Documents/IotAdapter/updates/update1.0/updater.json /home/pi/Documents/updater.json

python3 /home/pi/Documents/IotAdapter/updates/update1.0/change_to_mqtt.py
sudo pm2 restart iot