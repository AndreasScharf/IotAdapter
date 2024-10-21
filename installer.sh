
# FINGERPINT= && curl https://raw.githubusercontent.com/AndreasScharf/IotAdapter/staging/installer.sh | bash -s -- standalone

INSTALLATION_PATH="/home/pi/uf"
if [ "$FINGERPRINT" = "" ]; then 
    echo "Fingerprint missing..."
    exit 1
fi

# downloading the git repository
git clone https://github.com/AndreasScharf/IotAdapter.git /home/pi/Documents/IotAdapter

# set enviroment file
echo -e "FINGERPRINT=$FINGERPRINT\nPKI_HOST=https://cdm.frappgmbh.de\nCONNECTION=mqtt://mqtt.enwatmon.de:1883" > /home/pi/Documents/IotAdapter/.env


# For getting the MQTT Keys
cd /home/pi/Documents/IotAdapter


# Standalone request
if [ "$1" = "standalone" ]; then
    echo "Standalone Installtion ..."
      # copy Siemens UF Copy as standart config.json

    INSTALLATION_PATH="/home/pi"
    WORKING_DICT="$INSTALLATION_PATH/Documents/IotAdapter"

    cp "$WORKING_DICT/Konfigs/configStandart2.json" "$WORKING_DICT/config.json"
    python3 "$WORKING_DICT/installer/changeMad.py" $MAD
    # Whole UPDATE
    sudo apt update -y
    sudo apt full-upgrade -y

    # Install Node JS
    curl -sL https://deb.nodesource.com/setup_18.x | sudo bash -
    sudo apt-get install nodejs -y
    # Install dev enviroment
    sudo apt-get install libudev-dev -y
    # Install python3 enviroment 
    sudo apt-get install python3-pip -y
    sudo pip3 install setuptools

    
    # Install PM2
    sudo npm install pm2 -g
    sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u pi --hp /home/pi

    # Remove Unused Packages
    sudo apt-get purge -y wolfram-engine
    sudo apt-get purge -y libreoffice*
    sudo apt-get purge -y oracle-java*
    sudo apt-get purge -y scratch2
    sudo apt-get purge -y scratch

    sudo apt-get autoremove -y
    sudo apt-get clean -y

    # Disable RSyslog and journald
    sudo systemctl disable --now rsyslog
    sudo systemctl disable --now systemd-journald

    # disable SWAP
    sudo sed 's/# CONF_SWAPSIZE=100/CONF_SWAPSIZE=0' /etc/dphys-swapfile
    sudo systemctl restart dphys-swapfile

    # Install AndiDB Client
    git clone https://github.com/AndreasScharf/andiDBClientC ~/Downloads/andiDBValue
    cd ~/Downloads/andiDBValue
    sudo python3 setup.py install
    cd ~

  
 
fi

# Install Snap7
cd "$INSTALLATION_PATH"


wget https://sourceforge.net/projects/snap7/files/1.4.1/snap7-full-1.4.1.tar.gz
tar -xzvf snap7-full-1.4.1.tar.gz
cd snap7-full-1.4.1/build/unix
make -f arm_v7_linux.mk
cd ../bin/arm_v7-linux
sudo cp libsnap7.so /usr/lib/libsnap7.so

cd ~/Documents/IotAdapter

pip3 install python-snap7

rm "$INSTALLATION_PATH/snap7-full-1.4.1.tar.gz"
rm "$INSTALLATION_PATH/snap7-full-1.4.1/" -r
sudo ldconfig

cd ~/Documents/IotAdapter

pip3 install python-snap7
pip3 install "python-socketio[client]"

pip3 install -U minimalmodbus
pip3 install pythonping

pip3 install pi-ina219
pip3 install paho-mqtt==2.0.0
pip3 install psutil

pip3 install python-dotenv
pip3 uninstall serial -y
pip3 install pyserial


# In Standalone Mode Start All processes
if [ "$1" = "standalone" ]; then
    cd ~/Documents/IotAdapter
    pm2 start
    pm2 delete web

    pm2 startup
    # Startup Script

    pm2 save
fi