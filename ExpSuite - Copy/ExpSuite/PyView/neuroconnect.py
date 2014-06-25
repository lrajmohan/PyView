DEVICE_ON = False # True

if DEVICE_ON:
    from libnidaqmx import System
    from libnidaqmx import Device
    from libnidaqmx import DigitalOutputTask
    from libnidaqmx import DigitalInputTask    
    
from threading import Thread
import threading
import time
from datetime import datetime
from datetime import timedelta

valveChan = [('Dev1/Port5/Line5','Dev1/Port4/Line7'),('Dev1/Port2/Line7','Dev1/Port4/Line6'),
      ('Dev1/Port5/Line7','Dev1/Port4/Line5'),('Dev1/Port5/Line4','Dev1/Port4/Line4'),
      ('Dev1/Port2/Line4','Dev1/Port4/Line3')]
toneChan = 'Dev1/Port11/Line0:7'
toneTTLChan = ['Dev1/Port4/Line2','Dev1/Port4/Line1','Dev1/Port4/Line0','Dev1/Port3/Line7']
leverChan = ('Dev1/Port0/Line0','Dev1/Port3/Line6')
markerChan = 'Dev1/Port2/Line1'

# Front Hub, Hole 17
restartChan = 'Dev1/Port1/Line7'
# Back Hub, Hole 27(input), 28(output)
m8Chan = ('Dev1/Port10/Line2','Dev1/Port7/Line2')

flag = {'tone':True,'taste':True,'pulse':False}
""" ready flags do not run event if we know channel was still busy"""

# time during which to not register additional lever presses in microseconds
leverStandoffTime = timedelta(microseconds=50000)  # time between valid lever presses
lastLeverPress = {'time':None, 'result': False}

class NullEventThread (Thread):
    """ Mark time thread"""
    def __init__(self):
        Thread.__init__(self)
        self.stop_flag = False
        self.success = True
        self.start()

    def run(self):
        if not(DEVICE_ON):
            return
        try:
            m = DigitalOutputTask()
            m.create_channel(markerChan)
            m.start()
            m.write(1)
            m.write(0)
            m.stop()
            m.clear()
        except RuntimeError:
            print "UNABLE TO MARK TIME"
            self.success= False
        
    def stop(self):
        self.stop_flag = True
        
class RestartEventThread (Thread):
    """ New trial thread"""
    def __init__(self):
        Thread.__init__(self)
        self.stop_flag = False
        self.success = True
        self.start()

    def run(self):
        if not(DEVICE_ON):
            return
        try:
            r = DigitalOutputTask()
            r.create_channel(restartChan)
            r.start()
            r.write(1)
            r.write(0)
            r.stop()
            r.clear()
        except RuntimeError:
            print "UNABLE TO MARK RESTART"
            self.success= False
        
    def stop(self):
        self.stop_flag = True

class PlayToneThread (Thread):
    """ Play tone thread"""
    def __init__( self, rD, toneArray,ti):
        Thread.__init__(self)
        self.rd = rD
        self.freqCode = toneArray
        self.stop_flag = False
        self.ti = ti
        self.success = True
        self.start()
        
    def run(self):
        flag['tone'] = False
        channelInUse = toneChan
        if(len(toneTTLChan)-1 <self.ti):
            sizeDiff = (self.ti+1)-len(toneTTLChan)
            print('out of boundd::',sizeDiff)
        else:
            channelNeuralynx = toneTTLChan[self.ti]

        if DEVICE_ON:
            try:
                taskO_Neuralynx = DigitalOutputTask()
                taskO_Neuralynx.create_channel(channelNeuralynx)
            
                taskPlay = DigitalOutputTask()
                taskPlay.create_channel(channelInUse)
                
                taskO_Neuralynx.start()
                taskPlay.start()
    
                if len(self.freqCode)>0:
                    taskPlay.write(self.freqCode,layout='group_by_channel')
        
                taskO_Neuralynx.write(1)
                taskO_Neuralynx.write(0)
                
                playTime = datetime.now()
                deltaTime = playTime
                print 'start @ %s'%(playTime)
                while (deltaTime-playTime)<timedelta(seconds=self.rd) and not(self.stop_flag):
                	time.sleep(0.001)
                	deltaTime = datetime.now()
                print 'stop @ %s'%(deltaTime)
                taskPlay.write([0,0,0,0,0,0,0,0],layout='group_by_channel')
                taskPlay.stop()
                taskPlay.clear()
        
                taskO_Neuralynx.stop()
                taskO_Neuralynx.clear()
                
            except RuntimeError:
                self.success = False
                print "UNABLE TO PLAY OR MARK TONE"

        else:
            time.sleep(self.rd)

    def stop(self):
        self.stop_flag = True
        flag['tone'] = True

class GiveTasteThread (Thread):
    """ Deliver taste thread"""
    def __init__( self, nP, pI, rD, valve=0):
        Thread.__init__(self)
        self.np = nP
        self.pi = pI
        self.rd = rD
        self.valve = valve
        self.success = True
        self.stop_flag = False
        self.start()
        
    def run(self):
        if not(flag['taste']):
            return
        flag['taste'] = False
        channelInUse = valveChan[self.valve][0]
        channelNeuralynx = valveChan[self.valve][1]
 
        if DEVICE_ON:
            try:
                taskO_Neuralynx = DigitalOutputTask()
                taskO_Neuralynx.create_channel(channelNeuralynx)
            
                taskSend = DigitalOutputTask()
                taskSend.create_channel(channelInUse)
        
                taskO_Neuralynx.start()
                taskSend.start()
                
                taskSend.write(1) 
        
                taskO_Neuralynx.write(1)
                taskO_Neuralynx.write(0)
                
                time.sleep(self.rd) #wait for reward duration
                
                taskSend.write(0) # pulse delivery stopped
        
                taskSend.stop()
                taskSend.clear()
        
                taskO_Neuralynx.stop()
                taskO_Neuralynx.clear()
            except RuntimeError:
                self.success = False
                print "UNABLE TO DELIVER OR MARK TASTE"
        else:
            time.sleep(self.rd)
            print "taste from Valve "+str(self.valve+1)
        
        self.stop()

    def stop(self):
        self.stop_flag = True
        flag['taste'] = True

taskI = None
taskO = None
taskSi = None
taskSo = None

def main_init():
    """ Set up tasks for lever"""
    global taskI, taskO, taskSi, taskSo
    if not(DEVICE_ON):
        return
    taskI = DigitalInputTask()
    taskI.create_channel(leverChan[0])
            
    taskO = DigitalOutputTask()
    taskO.create_channel(leverChan[1])

    '''
    taskSi = DigitalInputTask()
    taskSi.create_channel(m8Chan[0])

    taskSo = DigitalOutputTask()
    taskSo.create_channel(m8Chan[1])
    '''        
    taskI.start()
    taskO.start()
    taskO.write(0)
    taskO.write(0)
    '''
    taskSi.start()
    taskSo.start()
    '''
	
def fake_lvpress(pressed):
	global leverLastPressed, leverStandoffTime
	if leverLastPressed!=None:
		diff = datetime.now() - leverLastPressed
		if diff < timedelta(microseconds=leverStandoffTime):
			print 'IGNORE PRESS'
			return False
	if pressed:
		leverLastPressed = datetime.now()
	return pressed
		
	
def main_lvpress():
    """ Detect lever press"""
    global taskI, taskO, lastLeverPress, leverStandoffTime
    if not(DEVICE_ON):
        return False
       
    if lastLeverPress['time']!=None:
       diff = datetime.now() - lastLeverPress['time']
       if diff < leverStandoffTime:
           return False
    try:
        (data,abc) = taskI.read(samples_per_channel = 1, timeout = -1, fill_mode = 'group_by_channel')
        leverPressed = (data[0][0] == 1)
        if leverPressed:
            if not(lastLeverPress['result']):
                taskO.write(1)
                taskO.write(0)
            else:
                leverPressed = False
            lastLeverPress['time'] = datetime.now()
            lastLeverPress['result'] = True
        else:
            if lastLeverPress['result']:
                lastLeverPress['time'] = datetime.now()
            lastLeverPress['result'] = False
        return leverPressed
    except RuntimeError:
        return False

def main_pulse():
    """  Returns 1: start pulse, 0: no pulse, -1: end pulse"""
    if not(DEVICE_ON):
        return 0
    result = 0
    try:
        (sim,mas) = taskSi.read(samples_per_channel = 1, timeout = -1, fill_mode = 'group_by_channel')
        pulseMade = (sim[0][0]==1)
        if not(flag['pulse']) and pulseMade:
            taskSo.write(1)
            taskSo.write(0)
            flag['pulse'] = True
            result = 1
        elif flag['pulse'] and not(pulseMade):
            taskSo.write(1)
            taskSo.write(0)
            flag['pulse'] = False
            result = -1
        else:
            result = 0
    except RuntimeError:
        print 'error'
        result = 0
    return result

def main_automark():
    """ Mark lever press"""
    global taskO
    if not(DEVICE_ON):
        return
    try:
        taskO.write(1)
        taskO.write(0)
    except RuntimeError:
        print "UNABLE TO MARK LEVER PRESS TO TTL"

def main_exit():
    """ free all NI tasks"""
    global taskI, taskO, taskSi, taskSo
    if not(DEVICE_ON):
        return
    taskO.write(0)
    taskO.write(0)
    taskO.stop()
    taskO.clear()
    '''
    taskSo.stop()
    taskSo.clear()
    taskSi.stop()
    taskSi.clear()
    '''
    taskI.stop()
    taskI.clear()
    taskI = None
    taskO = None
    taskSi = None
    taskSo = None
