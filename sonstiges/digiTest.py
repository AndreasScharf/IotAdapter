import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
gpios = [7, 17, 27, 22]

for g in gpios:
    GPIO.setup(g, GPIO.IN)

while 1:
    for g, i in enumerate(gpios):
        v = GPIO.input(g)
        print('DI{}: {}'.format(i, v))
    time.sleep(1)