from libnidaqmx import DigitalOutputTask
import time
import framework

taskO = DigitalOutputTask() 
taskO.create_channel('Dev1/Port11/Line0:7')

taskA = DigitalOutputTask()
taskA.create_channel('Dev1/Port5/Line5')

def play(fx=1):
    taskO.start()
    a = framework.int2bi8(fx)
    if len(a)==0:
        return
    else:
        taskO.write(a,layout='group_by_channel')

def stop():
    taskO.write([0,0,0,0,0,0,0,0],layout='group_by_channel')
    taskO.stop()

def strikeA():
    taskA.start()
    taskA.write(1)
    time.sleep(0.05)
    taskA.write(0)
    taskA.stop()
