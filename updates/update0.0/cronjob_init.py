import os;

cur_cron = os.popen('sudo crontab -l > current_crontab.txt');
cur_cron.read();
cur_cron.close();
fopen_cron = file('current_crontab.txt', 'a');
fopen_cron.write("\n### Updater immer um 24h aufrufen");
fopen_cron.write("\n0 0 * * * python /home/pi/Documents/updater.py");
fopen_cron.close();
