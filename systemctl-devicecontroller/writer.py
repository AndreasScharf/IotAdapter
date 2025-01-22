import time

with open('/tmp/devicecontroller/request_pipe', 'w') as fifo:
    fifo.write("set-color 255 0 255\n")

time.sleep(1)
with open('/tmp/devicecontroller/response_pipe', 'r') as fifo:
    print(fifo.read())
