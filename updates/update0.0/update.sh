curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
sudo apt-get install -y nodejs


pip3 install python-snap7
pip3 install "python-socketio[client]"
pip3 install json

sudo pip3 install python-snap7
sudo pip3 install "python-socketio[client]"
sudo pip3 install json
sudo cp IotAdapter/updates/update0.0/c.local /etc/rc.local
sudo cp IotAdapter/updates/update0.0/update.json /home/pi/Documents/update.json


sudo npm install pm2 -g
sudo npm install express -g
sudo npm install socket.io -g
sudo npm install axios -g
sudo npm install bcryptjs -g
sudo npm install assert -g
sudo npm install python-bridge -g

sudo pm2 start IotAdapter/webserver/index.js --name WebConfig
sudo pm2 startup
sudo pm2 save
