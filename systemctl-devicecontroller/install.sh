# Installer for systemctl-devicecontroller 
#  - Installs the devicecontroller service
#   - Installs the devicecontroller service file
# Additonal Notes:
# dist/index 
#  - service executable
#  BUILD:
#  - open in venv
#  - activate venv
#  - pip installer pyinstaller==6.6.0
#  - pyinstaller --onefile index.py


INSTALLATION_PATH="/home/pi"
WORKING_DICT="$INSTALLATION_PATH/systemctl-devicecontroller/Documents/IotAdapter"

# Install the devicecontroller service
sudo cp "$WORKING_DICT/dist/index" /usr/local/bin/devicecontroller
sudo chmod +x /usr/local/bin/devicecontroller

# Create Working Diconary
sudo mkdir /etc/devicecontroller
# set enviroment file
echo -e "APN=internet.m2mportal.de" > /etc/devicecontroller/config.env


# Install the devicecontroller service file
sudo cp devicecontroller.service /etc/systemd/system/devicecontroller.service

sudo systemctl daemon-reload
sudo systemctl enable devicecontroller --now
