curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
sudo apt-get install -y nodejs


pip3 install python-snap7
pip3 install "python-socketio[client]"
pip3 install json

sudo pip3 install python-snap7
sudo pip3 install "python-socketio[client]"
sudo pip3 install json
sudo cp IotAdapter/updates/update0.0/rc.local /etc/rc.local
sudo cp IotAdapter/updates/update0.0/update.json /home/pi/Documents/updater.json


sudo npm install pm2 -g
sudo cd /home/pi/Documents/IotAdapter/webserver

sudo npm install express
sudo npm install socket.io
sudo npm install axios
sudo npm install bcryptjs
sudo npm install assert
sudo npm install python-bridge

sudo pm2 start IotAdapter/webserver/index.js --name WebConfig
sudo pm2 startup
sudo pm2 save

sudo pip install python-crontab
sudo python /home/pi/Documents/IotAdapter/updates/update0.0/cronjob_init.py

sudo python /home/pi/Documents/IotAdapter/updates/update0.0/convert_xml_to_json.py
