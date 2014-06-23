'''
PyView Version 1.0

This program  handles the Digital Input and Output he National Instruments DAQmx USB-6509 device.
This could be used to run reward based experiments to train rats and to record the neural activity
in their gustatory cortex.

Last Updated: August 9, 2011

Written By: Anupam Gogar [anupamgogar@gmail.com]
Appended By: Alice Q. Wong [ariqing@gmail.com]

'''

DEVICE_ON = True

'''
Importing libnidaqmx, the library that interacts with the National Instrument's dll
and provides the functionality in python. DigitalInputTask and DigitalOutputTask are
classes defined in python that activate the input and output tasks.
'''

if DEVICE_ON:

    from libnidaqmx import System
    from libnidaqmx import Device
    from libnidaqmx import DigitalOutputTask
    from libnidaqmx import DigitalInputTask

'''

Importing functional libraries for getting time, string manipulation, random number
generation, and multi-threading. 'wx' is for designing the graphical user interface
and numpy is for various numerical calculations.

'''


from threading import Thread
import threading
import wx
import numpy
import time
import string
import random
from datetime import datetime
import os

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import _load_bitmap
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import pylab

'''
Global Variables
'''
if DEVICE_ON:
    system = System()
    dev = system.devices[0]

# all the calls to time.clock() funtion in the program would-
# -return the time elapsed since the call to this function

random.seed()

frameName = "NI-DAQ "
if DEVICE_ON:
    frameName += dev.get_product_type()
    

'''
DeliveryThread Class inherited from Thread class. It takes care of all the
deliveries in the experiment, for example taste delivery and tone delivery.

Four parameters are passed to the constructor namely-

1.) nP, number of pulses
2.) pI, pulse interval
3.) rD, reward duration
4.) mode, 1 stands for Taste Mode and 2 stands for Tone Mode

In usual scenario, number of pulses would be set to 1 and pulse interval
would be set to 0, as we only intend to send one pulse while doing a
manual taste or while giving a reward.

'''

class DeliveryThread (Thread):
    def __init__( self, nP, pI, rD, mode):
        Thread.__init__(self)

        # making the parameters passed as local variable for this class
        
        self.np = nP
        self.pi = pI
        self.rd = rD
        self.m = mode

        self.stop_flag = False
        self.start()

        
    def run(self):
        if Frame.Panel1.numValves == 0:
            Frame.Panel1.logger.AppendText("\nError: no valve selected.\n")
            Frame.Panel1.deliverButton.Enable()
            return
        else:
            if self.m == 1:
                randValIndex = random.randint(0,Frame.Panel1.numValves - 1)
                choosenValve = Frame.Panel1.openValves[randValIndex]
                Frame.Panel1.channelInUse = Frame.Panel1.channels[choosenValve]
                Frame.Panel1.channelNeuralynx = Frame.Panel1.channels[choosenValve+9]
            elif self.m == 2:
                Frame.Panel1.channelInUse = Frame.Panel1.channels[8] #sends to speaker control
                Frame.Panel1.channelNeuralynx = Frame.Panel1.channels[17] #sends to Neuralynx recorder
        
        if DEVICE_ON:
            taskO_Neuralynx = DigitalOutputTask()
            taskO_Neuralynx.create_channel(Frame.Panel1.channelNeuralynx)
        
            taskO = DigitalOutputTask()
            taskO.create_channel(Frame.Panel1.channelInUse)
    
            taskO_Neuralynx.start()
            taskO.start()
            taskO.write(1) # pulse delivered
    
            taskO_Neuralynx.write(1)
            taskO_Neuralynx.write(0)
            
            time.sleep(self.rd) #wait for reward duration
            taskO.write(0) # pulse delivery stopped
    
            taskO.stop()
            taskO.clear()
    
            taskO_Neuralynx.stop()
            taskO_Neuralynx.clear()

        else:
            time.sleep(self.rd)
        
        self.stop()
        Frame.Panel1.deliverButton.Enable()

    def stop(self):
        self.stop_flag = True # stop_flag not required here, because no Stop Button
        if self.m==2:
            Frame.Panel1.tonePlayed=True
            Frame.Panel1.tToneAt = time.clock()
        if self.m==1:
            Frame.Panel1.tRewardAt = time.clock()

class MainThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.stop_flag = False
        self.giveReward = False
        self.redraw_flag = False
        self.start()
    
    def sendTone(self,tn):
        Frame.Panel1.OnDeliver(None, 1, 0, self.tD, 2)
        Frame.Panel1.timeStamps.append( ('Tone Delivery ',tn) )
        Frame.Panel1.logger.AppendText('\n\n%s Tone \n\n'% round(tn,2) )
    
    def sendReward(self,tn,tt):
        Frame.Panel1.OnDeliver(None, 1, 0, self.rD, 1)
        Frame.Panel1.timeStamps.append( ('Taste Delivery ',tn) )
        Frame.Panel1.logger.AppendText('\n\n%s Taste \n\n' % round(tn,2))
        Frame.Panel1.tonePlayed = False
        if Frame.Panel1.deliverManualTaste == 1:
            Frame.Panel2.addPoint(tn-tt+Frame.Panel1.rewardDuration,2)
            Frame.Panel1.numberOfMT+=1
            Frame.Panel1.wManTaste.SetLabel(str(Frame.Panel1.numberOfMT))
        else:
            Frame.Panel2.addPoint(tn-tt+Frame.Panel1.rewardDuration,1)
            Frame.Panel1.numberOfRewards += 1
            Frame.Panel1.wNumRewards.SetLabel(str(Frame.Panel1.numberOfRewards))
        Frame.Panel1.wTimeTone.SetLabel('0.0')
        Frame.Panel1.rewarded = True
        self.redraw_flag = True

    def pressedLever(self,tn,tt):
        Frame.Panel1.timeStamps.append( ('Lever Press ',tn) )
        Frame.Panel1.logger.AppendText('%s \n' % round(tn,2))
        Frame.Panel2.addPoint(tn-tt,0)
        self.redraw_flag = True

    def threadAvailable(self):
        if Frame.Panel1.deliveryT!=None:
            if Frame.Panel1.deliveryT.isAlive():
                return False
            else:
                return True
        else:
            return True


    def run(self):
        
        if DEVICE_ON:
            taskI = DigitalInputTask()
            taskI.create_channel('Dev1/Port0/Line0')
            
            Frame.Panel1.channelNeuralynx2 = Frame.Panel1.channels[18]
    
            taskO_Neuralynx2 = DigitalOutputTask()
            taskO_Neuralynx2.create_channel(Frame.Panel1.channelNeuralynx2)
            
            taskI.start()
        
        t0 = time.clock()
        Frame.Panel1.tRewardAt = t0
        Frame.Panel1.tToneAt = t0
        Frame.Panel1.tonePlayed = False
        Frame.Panel1.rewarded = False
        
        dispExpPastTime = 0.00
        dispTonePastTime = 0.00
        Frame.Panel1.logger.AppendText('\nExperiment Begins .. Duration: %s seconds\n' % Frame.Panel1.experimentDuration)

        #rD - reward Duration (s), tD - tone Duration (s)
        self.rD = Frame.Panel1.rewardDuration
        self.tD = Frame.Panel1.toneDuration

        if DEVICE_ON:
            taskO_Neuralynx2.start()
        #have not exceeded experiment duration
        tCurr = time.clock()
        while (tCurr-t0) < Frame.Panel1.experimentDuration:
            if Frame.Panel1.rewarded:
                Frame.Panel1.tRewardAt = time.clock()
                Frame.Panel1.rewarded = False 
            if round(tCurr-t0,2)!=dispExpPastTime:
                dispExpPastTime = round(tCurr-t0,2)
                Frame.Panel1.wExperimentTime.SetLabel(str(dispExpPastTime))
            
            #terminate loop if stop is called
            if self.stop_flag:
                break
            #read from channels
            if DEVICE_ON:
                (data,abc) = taskI.read(samples_per_channel = 1, timeout = -1, fill_mode = 'group_by_channel')
            
            tCurr=time.clock()
            #Test time to play tone?
            if (tCurr - Frame.Panel1.tRewardAt) >= Frame.Panel1.iti:
                if DEVICE_ON:
                    taskO_Neuralynx2.write(1)
                    taskO_Neuralynx2.write(0)
                if not(Frame.Panel1.tonePlayed) and self.threadAvailable():
                    self.sendTone(tCurr)
                else:
                    if round(tCurr-Frame.Panel1.tToneAt,2)!=dispTonePastTime:
                        dispTonePastTime = round(tCurr-Frame.Panel1.tToneAt,2)
                        Frame.Panel1.wTimeTone.SetLabel( str(dispTonePastTime) )

            # Lever Pressed
            if DEVICE_ON:
                lvpressed = (data[0][0] == 1)
            else:
                lvpressed = Frame.Panel1.pseudoPress
            if lvpressed:
                #print "Lever pressed"
                if DEVICE_ON:
                    taskO_Neuralynx2.write(1)
                    taskO_Neuralynx2.write(0)
                
                tCurr = time.clock()
                minTime = tCurr>(Frame.Panel1.tToneAt+Frame.Panel1.wait)
                maxTime =  tCurr<(Frame.Panel1.tToneAt+Frame.Panel1.wait+Frame.Panel1.rewardInterval)
                if Frame.Panel1.tonePlayed and minTime and maxTime:
                    if DEVICE_ON:
                        taskO_Neuralynx2.write(1)
                        taskO_Neuralynx2.write(0)
                    self.sendReward(tCurr,Frame.Panel1.tRewardAt)
                else:
                    self.pressedLever(tCurr,Frame.Panel1.tRewardAt)
        
                Frame.Panel1.pseudoPress = False

            #lever not pressed
            if DEVICE_ON:
                lvNotPressed = data[0][0] == 0
            else:
                lvNotPressed = not(lvpressed)
                
            if lvNotPressed:
                if DEVICE_ON:
                    taskO_Neuralynx2.write(1)
                    taskO_Neuralynx2.write(0)
                tCurr = time.clock()
                if Frame.Panel1.deliverManualTaste == 1:
                    self.sendReward(tCurr,Frame.Panel1.tRewardAt)
                    Frame.Panel1.deliverManualTaste = 0
            tCurr = time.clock()
            if self.redraw_flag:
                Frame.Panel2.Refresh()
                self.redraw_flag = False
            
# write to file after the experiment has ended            
        if self.stop_flag == False:
            writeToFile()
        Frame.Panel1.logger.AppendText('\nEnd of experiment.\n')
        
        if DEVICE_ON:
            taskO_Neuralynx2.stop()
            taskO_Neuralynx2.clear()
                    
            taskI.stop()
            taskI.clear()
        
        Frame.Panel1.startButton.Enable()

    def stop(self):
        self.stop_flag = True
        

class GraphPanel(wx.Panel):
    def __init__(self,parent,ctrl):
        wx.Panel.__init__(self,parent)
        self.SetBackgroundColour('#FFFFFF')
        self.ctrlPanel = ctrl
        self.initGraph()
        wx.EVT_PAINT(self, self.OnPaint)


    def initGraph(self):
        self.x0 = []
        self.y0 = []
        self.x1 = []
        self.y1 = []
        self.x2 = []
        self.y2 = []
        self.trial = 1
        
        self.figure = Figure(dpi=100,figsize=(5,8))
        self.axes = self.figure.add_subplot(111)
        self.axes.axis([0,self.ctrlPanel.experimentDuration,1,0])
        self.axes.set_xlabel('time (s)')

        bluepts = self.axes.scatter(self.x0, self.y0, c='b',s=10,lw=0.0)
        redpts = self.axes.scatter(self.x1,self.y1, c='r',s=10,lw=0.0)
        purpts = self.axes.scatter(self.x2,self.y2,c='m',s=10,lw=0.0)

        startAt = self.ctrlPanel.iti
        endAt = startAt+self.ctrlPanel.toneDuration
        tone = self.axes.axvspan(startAt,endAt,facecolor='g',alpha=0.5,lw=0.0)
        startAt = endAt
        endAt = startAt+self.ctrlPanel.wait
        wait = self.axes.axvspan(startAt,endAt,facecolor='#aeaeae',alpha=0.5,lw=0.0)
        startAt = endAt
        endAt = startAt + self.ctrlPanel.rewardInterval
        reward = self.axes.axvspan(startAt,endAt,facecolor='#FFCCCC',alpha=0.5,lw=0.0)

        LText = FontProperties()
        LText.set_size("small")
        
        self.axes.legend((bluepts,redpts,purpts,tone,wait,reward),
                         ("Lever Press","Rewarded Press","Manual Reward","Tone Duration","Wait Interval","Reward Interval"),
                         prop=LText, fancybox=True, bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=2, mode="expand", borderaxespad=0)

        self.canvas = FigureCanvas(self, -1, self.figure)
    
    def clearGraph(self):
        self.figure.delaxes(self.axes)
        self.initGraph()
        self.Refresh()
    
    def addPoint(self,t,pcat):
        if pcat==1:
            self.x1.append(t)
            self.y1.append(self.trial)
            self.trial+=1
            self.axes.set_ylim(bottom=self.trial)
        elif pcat==2:
            self.x2.append(t)
            self.y2.append(self.trial)
            self.trial+=1
            self.axes.set_ylim(bottom=self.trial)
        else:
            self.x0.append(t)
            self.y0.append(self.trial)
    
        
    def OnPaint(self, event):

        self.bluepts = self.axes.scatter(self.x0, self.y0, c='b',s=10,lw=0.0)
        self.redpts = self.axes.scatter(self.x1,self.y1, c='r',s=10,lw=0.0)
        self.purpts = self.axes.scatter(self.x2,self.y2,c='m',s=10,lw=0.0)
        self.canvas.draw()
        event.Skip()

    def OnSetFocus(self, event):
        #self.color = '#0099f7'
        self.color = 'yellow'
        self.Refresh()

    def OnKillFocus(self, event):
        self.color = '#b3b3b3'
        self.Refresh()


class MainPanel(wx.Panel):
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.quote = wx.StaticText(self, label="MAIN PANEL", pos=(200, 10))
        self.deliveryT = None
        # A multiline TextCtrl - This is here to show how the events work in this program, don't pay too much attention to it
        self.timeStamps = []
        self.numberOfRewards = 0
        self.numberOfMT = 0
        self.deliverManualTaste = 0
        self.valveArray = numpy.zeros ( 8, int )
        self.numValves = 0
        self.openValves = []
        self.pseudoPress = False
        # 19 channels
        '''Channel Menu [Valve1, Valve2, Valve3, Valve4,
        Valve5, Valve6, Valve7, Valve8,
        Tone1, Neuralynx Pair 1, Neuralynx Pair 2, Neuralynx Pair 3,
        Neuralynx Pair 4, Neuralynx Pair 5, Neuralynx Pair 6, Neuralynx Pair 7,
        Neuralynx Pair 8, Neuralynx Pair 9, Neuralynx Pair 10]'''
        self.channels = ['Dev1/Port5/Line5', 'Dev1/Port2/Line7', 'Dev1/Port5/Line7', 'Dev1/Port5/Line4',
                         'Dev1/Port2/Line4', 'Dev1/Port2/Line5', 'Dev1/Port5/Line6', 'Dev1/Port2/Line6',
                         'Dev1/Port11/Line7', 'Dev1/Port4/Line7','Dev1/Port4/Line6','Dev1/Port4/Line5',
                         'Dev1/Port4/Line4','Dev1/Port4/Line3','Dev1/Port4/Line2','Dev1/Port4/Line1',
                         'Dev1/Port4/Line0','Dev1/Port3/Line7','Dev1/Port3/Line6'] 
        self.tonePlayed = False
        self.timeSinceTone = 0
        self.expTime = 0
        
        # Default valutes
        self.numberPulses = 1
        self.pulseInterval = 0
        self.pulseDuration = 100
        self.experimentDuration = 60
        self.rewardInterval = 5.0
        self.rewardDuration = 0.043
        self.iti = 2
        self.wait = 0
        self.toneDuration = 1

        self.channelInUse = ''
        
        self.logger = wx.TextCtrl(self, pos=(20,400), size=(400,200), style=wx.TE_MULTILINE | wx.TE_READONLY)        

        def OnToggleValve(event):
            obj = event.GetEventObject()
            objId = obj.GetId()
            n = objId - 1
            if self.valveArray[n] == 1:
               self.valveArray[n] = 0
               self.numValves -= 1
               self.openValves.remove(n)
            else:
               self.valveArray[n] = 1
               self.numValves += 1
               self.openValves.append(n)

        valve1 = wx.ToggleButton(self, 1, 'Valve 1', (20, 25))
        valve2 = wx.ToggleButton(self, 2, 'Valve 2', (20, 55))
        valve3 = wx.ToggleButton(self, 3, 'Valve 3', (20, 85))
        valve4 = wx.ToggleButton(self, 4, 'Valve 4', (20, 115))

        valve5 = wx.ToggleButton(self, 5, 'Valve 5', (110, 25))
        valve6 = wx.ToggleButton(self, 6, 'Valve 6', (110, 55))
        valve7 = wx.ToggleButton(self, 7, 'Valve 7', (110, 85))
        valve8 = wx.ToggleButton(self, 8, 'Valve 8', (110, 115))

        valve1.Bind(wx.EVT_TOGGLEBUTTON,OnToggleValve)
        valve2.Bind(wx.EVT_TOGGLEBUTTON,OnToggleValve)
        valve3.Bind(wx.EVT_TOGGLEBUTTON,OnToggleValve)
        valve4.Bind(wx.EVT_TOGGLEBUTTON,OnToggleValve)
        valve5.Bind(wx.EVT_TOGGLEBUTTON,OnToggleValve)
        valve6.Bind(wx.EVT_TOGGLEBUTTON,OnToggleValve)
        valve7.Bind(wx.EVT_TOGGLEBUTTON,OnToggleValve)
        valve8.Bind(wx.EVT_TOGGLEBUTTON,OnToggleValve)

        self.deliverButton = wx.Button(self, label="Manual Taste", pos = (60, 300) )

        def helperDeliver(evt):
            self.deliverManualTaste = 1
            nP = self.numberPulses
            pI = self.pulseInterval
            rD = self.pulseDuration / 1000.0
            #self.OnDeliver(evt, nP, pI, rD, 1)
        
        self.Bind(wx.EVT_BUTTON, helperDeliver, self.deliverButton)

        self.pseudoLever = wx.Button(self,label="Lever Press",pos=(60,270))
        def OnPseudoLeverPress(event):
            self.pseudoPress = True
        self.Bind(wx.EVT_BUTTON, OnPseudoLeverPress, self.pseudoLever)

        self.startButton = wx.Button(self, label = "Start", pos = (260,300) )
        self.Bind (wx.EVT_BUTTON, self.OnStart, self.startButton)

        self.stopButton = wx.Button(self, label = "Stop", pos = (260,360) )
        self.Bind (wx.EVT_BUTTON, self.OnStop, self.stopButton)
        
        self.resetButton = wx.Button(self,label="Reset Counter", pos=(300,710))
        self.Bind(wx.EVT_BUTTON, self.OnResetCounter, self.resetButton)

       
        # Text input

        self.rDuration = wx.StaticText(self, label="Pulse Duration (ms): ",pos=(20,340))
        self.wDuration = wx.TextCtrl(self, value=str(self.pulseDuration), pos=(115, 336), size=(40,-1))
        self.Bind(wx.EVT_TEXT, self.evtDuration, self.wDuration)
        
        self.rExperimentDur = wx.StaticText(self, label="Experiment Duration (s): ",pos=(220,130))
        self.wExperimentDur = wx.TextCtrl(self, value=str(self.experimentDuration), pos=(345, 130), size=(35,-1))
        self.Bind(wx.EVT_TEXT, self.evtExperimentDur, self.wExperimentDur)
        
        self.rRewardInt = wx.StaticText(self, label="Reward Interval (s): ",pos=(220,160))
        self.wRewardInt = wx.TextCtrl(self, value=str(self.rewardInterval), pos=(345, 160), size=(35,-1))
        self.Bind(wx.EVT_TEXT, self.evtRewardInt, self.wRewardInt)

        self.rRewardDur = wx.StaticText(self, label="Reward Duration (s): ",pos=(220,190))
        self.wRewardDur = wx.TextCtrl(self, value=str(self.rewardDuration), pos=(345, 190), size=(45,-1))
        self.Bind(wx.EVT_TEXT, self.evtRewardDur, self.wRewardDur)

        self.rITI = wx.StaticText(self, label =" Inter Trial Interval (s):", pos=(220,50))
        self.wITI = wx.TextCtrl(self, value =str(self.iti), pos=(365, 45), size=(35,-1))
        self.Bind(wx.EVT_TEXT, self.evtITI, self.wITI)

        self.rWait = wx.StaticText(self, label=" Wait Interval (s):", pos=(220,100))
        self.wWait = wx.TextCtrl(self, value=str(self.wait), pos=(365,95), size=(35,-1))
        self.Bind(wx.EVT_TEXT, self.evtWait, self.wWait)

        self.rToneDur = wx.StaticText(self, label=" Tone Duration (s):", pos=(20,160))
        self.wToneDur = wx.TextCtrl(self, value=str(self.toneDuration), pos=(120, 155), size=(40,-1))
        self.Bind(wx.EVT_TEXT, self.evtToneDur, self.wToneDur)

        self.rExperimentTime = wx.StaticText(self, label=" Experiment Time ", pos=(50,650))
        self.wExperimentTime = wx.StaticText(self, label="0", pos=(160, 648))

        self.rNumRewards = wx.StaticText(self, label=" # of Rewards ", pos=(300,650))
        self.wNumRewards = wx.StaticText(self, label="0", pos=(400, 650))

        self.rManTaste = wx.StaticText(self,label=" # of Manual Tastes ", pos=(300,680))
        self.wManTaste = wx.StaticText(self, label="0", pos=(400, 680))

        self.rTimeTone = wx.StaticText(self, label=" Time from Tone ", pos=(50,710))
        self.wTimeTone = wx.StaticText(self, label="0", pos=(160, 708))   

        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def setSibling(self,graph):
        self.graphPanel = graph
        
    def OnDeliver(self,event, nP, pI, rD, mode):
        self.deliverButton.Disable()
        self.deliveryT = DeliveryThread(nP,pI,rD, mode)

    def OnResetCounter(self,evt):
        self.wNumRewards.SetLabel("0")
        self.numberOfRewards=0
        self.wManTaste.SetLabel("0")
        self.numberOfMT=0
        
               
# IMP Note: Digital Inputs are normally pulled high
# IMP Note: 'Normal Close' for Lever Input

    def OnStop(self, event):
        self.worker.stop()
        self.startButton.Enable()
        writeToFile()

    def OnStart(self, event):
        #if len(self.timeStamps)>0:
        #    clearGraph()
        #    self.timeStamps = []
        clearGraph()
        if Frame.Panel1.numValves == 0:
            Frame.Panel1.logger.AppendText("Error: no valve selected.\n")
            return
        self.worker = MainThread()
        #Disable any widgets which could affect your thread
        self.startButton.Disable()
        
    def evtDuration(self, event):
        try:
           self.pulseDuration = int(event.GetString())
        except ValueError:
           pass
    
    def evtWait(self, event):
        try:
           self.wait = float(event.GetString())
        except ValueError:
           pass

    def evtExperimentDur(self, event):
        try:
           self.experimentDuration = float(event.GetString())
        except ValueError:
           pass

    def evtRewardInt(self, event):
        try:
            self.rewardInterval = float(event.GetString())
        except ValueError:
            pass

    def evtRewardDur(self, event):
        try:
            self.rewardDuration = float(event.GetString())
        except ValueError:
            pass

    def evtITI(self, event):
        try:
            self.iti = float(event.GetString())
        except ValueError:
            pass

    def evtToneDur(self, event):
        try:
            self.toneDuration= float(event.GetString())
        except ValueError:
            pass

    def OnSetFocus(self, event):
        self.color = '#0099f7'
        self.Refresh()

    def OnKillFocus(self, event):
        self.color = '#b3b3b3'
        self.Refresh()

class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(1000, 800))
        grid = wx.GridSizer(1, 2, 10, 10)
        self.Panel1 = MainPanel(self)
        self.Panel2 = GraphPanel(self,self.Panel1)
        self.Panel1.setSibling(self.Panel2)
        grid.AddMany([(self.Panel1, 1, wx.EXPAND|wx.TOP|wx.LEFT,9), (self.Panel2, 1, wx.EXPAND|wx.TOP|wx.RIGHT, 9)])

        self.SetSizer(grid)
        self.Centre()
        self.Show(True)

def plotGraph(event):
    Frame.Panel2.OnPaint(event)

def clearGraph():
    Frame.Panel2.clearGraph()
    
#def test():

    
def writeToFile():
    
    currDir = os.getcwd()
    dirs = currDir.split('\\')
    dirs.pop()
    currDir = '\\'.join(dirs)
    directory = currDir+'\\Time Stamps\\'
    fileName = directory + datetime.now().strftime("%Y.%B.%d, %H.%M.%S") + '.txt'
    f = open(fileName, 'w')
    temp = Frame.Panel1.timeStamps
    for i in range( len(temp) ):
        tempString = str(temp[i][1])+ '\t' + str(temp[i][0]) + '\n'
        f.write(tempString)
    f.close()
   
    Frame.Panel1.logger.AppendText("Writing to File Completed.\n")
    Frame.Panel1.timeStamps = []
        
app = wx.App(False)  # Create a new app, don't redirect stdout/stderr to a window.     
Frame = MyFrame(None, -1, frameName)
app.MainLoop()




