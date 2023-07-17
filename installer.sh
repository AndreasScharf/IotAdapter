# Install Snap7
cd ~/uf
wget https://sourceforge.net/projects/snap7/files/1.4.1/snap7-full-1.4.1.tar.gz
tar -xzvf snap7-full-1.4.1.tar.gz
cd snap7-full-1.4.1/build/unix
make -f arm_v7_linux.mk
cd ../bin/arm_v7-linux
sudo cp libsnap7.so /usr/lib/libsnap7.so

cd ~/Documents/IotAdapter

pip3 install python-snap7

rm /home/pi/uf/snap7-full-1.4.1.tar.gz
rm /home/pi/uf/snap7-full-1.4.1/ -r
sudo ldconfig

pip3 install python-snap7
pip3 install "python-socketio[client]"
pip3 install json

pip3 install -U minimalmodbus
pip3 install pythonping

pip3 install pi-ina219
pip3 install paho-mqtt
pip3 install psutil