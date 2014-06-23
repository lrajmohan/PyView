from libnidaqmx import DigitalOutputTask
import time
from pulsar import *

taskO = DigitalOutputTask()
#taskO.create_channel('Dev1/Port11/Line0') 
taskO.create_channel('Dev1/Port11/Line0:7')

def play(fx=1):
    taskO.start()
    a = int2bi8(fx)
    if len(a)==0:
        return
    else:
        taskO.write(a,layout='group_by_channel')

def stop():
    taskO.write([0,0,0,0,0,0,0,0],layout='group_by_channel')
    taskO.stop()
