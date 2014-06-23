from libnidaqmx import DigitalInputTask
import time
from threading import Thread

line = "Dev1/Port1/Line3"

taskI = DigitalInputTask()
taskI.create_channel(line)

goflag = True

class Detector(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.start()

    def run(self):
        while goflag:
            (data,abc) = taskI.read(samples_per_channel = 1, timeout = -1, fill_mode = 'group_by_channel')
            if (data[0][0] == 1):
                print "Input from %s detected"%line

    def stop(self):
        goflag = False

def start():
    Detector()

def stop():
    global goflag
    goflag = False
