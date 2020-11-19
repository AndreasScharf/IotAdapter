
sudo python /home/pi/Documents/IotAdapter/updates/update0.1/cronjob_init.py

python /home/pi/Documents/IotAdapter/updates/update0.1/change_to_url.py
cp /home/pi/Documents/IotAdapter/updates/update0.1/updater.py /home/pi/Documents/updater.py 
cp /home/pi/Documents/IotAdapter/updates/update0.1/updater.json /home/pi/Documents/updater.json
sudo reboot
