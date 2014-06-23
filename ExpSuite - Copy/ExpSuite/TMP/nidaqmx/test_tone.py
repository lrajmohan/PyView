from libnidaqmx import System
from libnidaqmx import Device
from libnidaqmx import DigitalOutputTask
from libnidaqmx import DigitalInputTask
import time

taskO = DigitalOutputTask()
#taskO.create_channel('Dev1/Port11/Line0') 
taskO.create_channel('Dev1/Port11/Line0:3')

def play():
    taskO.start()
    #taskO.write(1)
    taskO.write([1,0,1,1],layout='group_by_channel')

def stop():
    #taskO.write(0)
    taskO.write([0,0,0,0],layout='group_by_channel')
    taskO.stop()
