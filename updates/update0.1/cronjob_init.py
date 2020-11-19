from crontab import CronTab
cron = CronTab(user='root')
job = cron.new(command='/usr/bin/python /home/pi/Documents/updater.py')
job.minute.on(0)
job.hour.on(0)
cron.write()
