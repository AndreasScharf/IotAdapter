from time import sleep
import RPi.GPIO as GPIO



class rotator(object):
  def __init__(self, pin, value, zero_time, start_totalizer, name):
    self.pin = pin
    self.value = value
    self.zero_time = zero_time
    self.impulses = 0
    self.totalizer = start_totalizer
    self.name = name
    def event():
      self.pin_rising()

    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(pin, GPIO.RISING, lambda x: event())
    self.flow_li = 0 #flow last impulses
    self.totalizer_li = 0 #flow last impulses
    
    self.time_no_impuleses = 0 #time no impu

    self.flow = 0
    self.flow_queue = []

  def pin_rising(self):
    self.impulses = self.impulses + 1

  def get_flow(self, time_passed):
      impulses = self.impulses - self.flow_li
      self.flow_li = self.impulses

      if impulses == 0:
          self.time_no_impuleses = self.time_no_impuleses + time_passed
      else:
          self.time_no_impuleses = 0

      
      if(self.time_no_impuleses > self.zero_time):
        return 0

      self.flow = (impulses * self.value) / (time_passed / (1000 * 60 * 60))

      self.flow_queue.append(self.flow)
      if len(self.flow_queue) > 5:
          self.flow_queue.pop(0)    

      return sum(self.flow_queue) / len(self.flow_queue)

  def get_totalizer(self):
      impulses = self.impulses - self.totalizer_li
      self.totalizer_li = self.impulses

      self.totalizer = self.totalizer + self.value * impulses
      return self.totalizer 
  
  