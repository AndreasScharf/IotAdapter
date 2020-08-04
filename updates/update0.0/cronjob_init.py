from crontab import CronTab
cron = CronTab(user='root')
job = cron.new(command='python /home/pi/Documents/updater.py')
job.minute.every(0)
job.hour.every(0)
cron.write()
