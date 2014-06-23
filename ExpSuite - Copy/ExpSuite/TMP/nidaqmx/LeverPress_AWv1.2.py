'''
PyView Version 1.0

This program  handles the Digital Input and Output he National Instruments DAQmx USB-6509 device.
This could be used to run reward based experiments to train rats and to record the neural activity
in their gustatory cortex.

Last Updated: August 9, 2011

Written By: Anupam Gogar [anupamgogar@gmail.com]

'''


'''
Importing libnidaqmx, the library that interacts with the National Instrument's dll
and provides the functionality in python. DigitalInputTask and DigitalOutputTask are
classes defined in python that activate the input and output tasks.
'''


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
import pylab

'''
Global Variables
'''

system = System()
dev = system.devices[0]

#time.clock();

# all the calls to time.clock() funtion in the program would-
# -return the time elapsed since the call to this function

random.seed();

frameName = "NI-DAQ " + dev.get_product_type();


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
        #print threading.activeCount()
        if Frame.Panel1.numValves == 0:
            Frame.Panel1.logger.AppendText("\nError: no valve selected.\n")
            #Frame.Panel1.logger.AppendText("number of valves %s \n" % Frame.Panel1.numValves)
            Frame.Panel1.deliverButton.Enable()
            return
        else:
            #Frame.Panel1.logger.AppendText("\n list of open valves : %s" % Frame.Panel1.openValves)
            if self.m == 1:
                abc = random.randint(0,Frame.Panel1.numValves - 1)
                bcd = Frame.Panel1.openValves[abc]
                Frame.Panel1.channelInUse = Frame.Panel1.channels[bcd]
                Frame.Panel1.channelNeuralynx = Frame.Panel1.channels[bcd+9]
            elif self.m == 2:
                Frame.Panel1.channelInUse = Frame.Panel1.channels[8]
                Frame.Panel1.channelNeuralynx = Frame.Panel1.channels[17]

        taskO_Neuralynx = DigitalOutputTask()
        taskO_Neuralynx.create_channel(Frame.Panel1.channelNeuralynx)
    
        taskO = DigitalOutputTask()
        taskO.create_channel(Frame.Panel1.channelInUse)

        taskO_Neuralynx.start()
        taskO.start()
        taskO.write(1) # pulse delivered

        taskO_Neuralynx.write(1)
        taskO_Neuralynx.write(0)
        
        time.sleep(self.rd)
        taskO.write(0) # pulse delivery stopped

                
        '''for i in range(self.np):
            taskO.write(1) # pulse delivered
            time.sleep(self.rd)
            taskO.write(0) # pulse delivery stopped
        
            T1 = time.clock()
            T2 = time.clock()                
            while (T2 - T1) < self.pi: 
                # waiting to deliver the pulse
                T2 = time.clock()'''

        taskO.stop()
        taskO.clear()

        taskO_Neuralynx.stop()
        taskO_Neuralynx.clear()
        
        Frame.Panel1.deliveryT.stop()
        Frame.Panel1.deliverButton.Enable()

    def stop(self):
        self.stop_flag = True # stop_flag not required here, because no Stop Button
        if self.m==2:
            Frame.tonePlayed=True

class MainThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        
        time.clock()
        self.stop_flag = False

        #This calls the run() to start the new thread
        self.start()
        self.giveReward = False


    def run(self):
        """ Over-rides the super-classes run()"""
        taskI = DigitalInputTask()
        taskI.create_channel('Dev1/Port0/Line0')

        Frame.Panel1.channelNeuralynx2 = Frame.Panel1.channels[18]

        taskO_Neuralynx2 = DigitalOutputTask()
        taskO_Neuralynx2.create_channel(Frame.Panel1.channelNeuralynx2)
        
        taskI.start()

        T0 = time.clock()
        T1 = time.clock() # before start loop time
        T2 = time.clock() # time at the of each loop iteration
        T3 = time.clock()

        T5 = time.clock()
        T6 = time.clock()
        T7 = time.clock()

        timeFromToneCounter = 0
        
        Frame.Panel1.logger.AppendText('\nExperiment Begins .. Duration: %s seconds\n' % Frame.Panel1.experimentDuration)
        counter = 0
        rD = string.atoi(Frame.Panel1.rewardDuration) / 1000.000
        tD = string.atoi(Frame.Panel1.toneDuration) / 1000.000

        taskO_Neuralynx2.start()
        #have not exceeded experiment duration
        while (T2-T1) < string.atoi(Frame.Panel1.experimentDuration):

            T6 = time.clock() #time at start of iteration
   
            Frame.Panel1.wExperimentTime.ChangeValue(str(T6-T5))
            
            if self.stop_flag:
                break
            (data,abc) = taskI.read(samples_per_channel = 1, timeout = -1, fill_mode = 'group_by_channel')
            
            if T2 - T3 >= string.atoi(Frame.Panel1.iti):

                taskO_Neuralynx2.write(1)
                taskO_Neuralynx2.write(0)
                
                if not(Frame.tonePlayed):
                    Frame.Panel1.OnDeliver(None, 1, 0, tD, 2)
                tn = time.clock()
                Frame.Panel1.timeStamps.append( ('Tone Delivery ',tn) )
                Frame.Panel1.logger.AppendText('\n\n%s Tone \n\n'% round(tn,2) )
                Frame.Panel2.axes.axhline(y=tn,color='g',lw=0.5)
                timeFromToneCounter = 1
                T0 = T2 + tD
                T7 = T2 + tD
                T3 = 999999

            if (T2 - T7 >= 0 and timeFromToneCounter == 1):
                Frame.Panel1.wTimeTone.ChangeValue( str(T2-T7) )            
            
            if T2 - T0 >= string.atoi(Frame.Panel1.rewardInterval) :
                self.giveReward = True
                T0 = 999999
                

                
# earlier when T3 was set to 999, this loop would go infinitely if the program has
# run for 999 seconds
                
            if (data[0][0] == 1 and counter == 1 and Frame.tonePlayed) or Frame.Panel1.pseudoPress:
                
                taskO_Neuralynx2.write(1)
                taskO_Neuralynx2.write(0)

                tn = time.clock()
                counter = 0
                Frame.Panel1.timeStamps.append( ('Lever Press ',tn) )
                Frame.Panel1.logger.AppendText('%s \n' % round(tn,2))
                Frame.Panel2.axes.axhline(y=tn,color='b',lw=0.5)
                if self.giveReward:
                    
                    taskO_Neuralynx2.write(1)
                    taskO_Neuralynx2.write(0)
                    timeFromToneCounter = 0
                    Frame.Panel1.OnDeliver(None, 1, 0, rD, 1)
                    tn = time.clock()
                    Frame.Panel1.timeStamps.append( ('Taste Delivery ',tn) )
                    Frame.Panel1.logger.AppendText('\n\n%s Taste \n\n' % round(tn,2))
                    Frame.Panel2.axes.axhline(y=tn,color='r',lw=0.5)
                    Frame.Panel1.numberOfRewards += 1
                    Frame.Panel1.wNumRewards.ChangeValue(str(Frame.Panel1.numberOfRewards))
                    self.giveReward = False
                    T3 = T2
                Frame.Panel1.pseudoPress = False

            elif data[0][0] == 0:
                counter = 1

                taskO_Neuralynx2.write(1)
                taskO_Neuralynx2.write(0)
                
                if Frame.Panel1.deliverManualTaste == 1:
                    tn = time.clock()
                    Frame.Panel1.logger.AppendText('\n\n%s Taste \n\n' % round(tn,2))
                    Frame.Panel1.timeStamps.append( ('Taste Delivery ',tn) )
                    Frame.Panel2.axes.axhline(y=tn,color='r',lw=0.5)
                    Frame.Panel1.numberOfRewards += 1
                    Frame.Panel1.wNumRewards.ChangeValue(str(Frame.Panel1.numberOfRewards))
                    self.giveReward = False
                    T3 = T2
                    T2 = 999999
                    Frame.Panel1.deliverManualTaste = 0
            T2 = time.clock()
            Frame.Panel2.canvas.draw()
            
# write to file after the experiment has ended            
        if self.stop_flag == False:
            writeToFile()
        Frame.Panel1.logger.AppendText('\nEnd of experiment.\n')

        taskO_Neuralynx2.stop()
        taskO_Neuralynx2.clear()
                
        taskI.stop()
        taskI.clear()
        Frame.Panel1.startButton.Enable()

    def stop(self):
        self.stop_flag = True
        


class GraphPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        self.SetBackgroundColour('#FFFFFF')
        self.quote = wx.StaticText(self,label = "GRAPH PANEL", pos = (200,10))
        self.figure = Figure(dpi=100,figsize=(5,8))
        self.axes = self.figure.add_subplot(111)
        self.axes.axis([0,1,0,60])
        self.axes.set_ylabel('time (s)')
        green = self.axes.axhline(y=-1,color='g',lw=4)
        blue = self.axes.axhline(y=-1,color='b',lw=4)
        red = self.axes.axhline(y=-1,color='r',lw=4)
        self.axes.legend((green,blue,red),("Tone","Level Press","Reward"),loc="upper right")
        self.canvas = FigureCanvas(self, -1, self.figure)
        wx.EVT_PAINT(self, self.OnPaint)

    def OnPaint(self, event):
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

        # A multiline TextCtrl - This is here to show how the events work in this program, don't pay too much attention to it
        self.timeStamps = []
        self.numberOfRewards = 0

        self.deliverManualTaste = 0

        self.valveArray = numpy.zeros ( 8, int )
        
        self.numValves = 0

        self.openValves = []

        self.pseudoPress = False

        self.channels = ['Dev1/Port5/Line5', 'Dev1/Port2/Line7', 'Dev1/Port5/Line7', 'Dev1/Port5/Line4', 'Dev1/Port2/Line4', 'Dev1/Port2/Line5', 'Dev1/Port5/Line6', 'Dev1/Port2/Line6', 'Dev1/Port11/Line7', 'Dev1/Port4/Line7','Dev1/Port4/Line6','Dev1/Port4/Line5','Dev1/Port4/Line4','Dev1/Port4/Line3','Dev1/Port4/Line2','Dev1/Port4/Line1','Dev1/Port4/Line0','Dev1/Port3/Line7','Dev1/Port3/Line6'] 

        # Channel Menu [Valve1, Valve2, Valve3, Valve4, Valve5, Valve6, Valve7, Valve8, Tone1, Neuralynx Pair 1, Neuralynx Pair 2, Neuralynx Pair 3, Neuralynx Pair 4, Neuralynx Pair 5, Neuralynx Pair 6, Neuralynx Pair 7, Neuralynx Pair 8, Neuralynx Pair 9, Neuralynx Pair 10]

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
            nP = string.atoi(self.numberPulses)
            pI = string.atoi(self.pulseInterval)
            rD = string.atoi(self.pulseDuration) / 1000.0
            self.OnDeliver(evt, nP, pI, rD, 1)
        
        self.Bind(wx.EVT_BUTTON, helperDeliver, self.deliverButton)

        self.pseudoLever = wx.Button(self,label="Lever Press",pos=(60,270))
        def OnPseudoLeverPress(event):
            self.pseudoPress = True
        self.Bind(wx.EVT_BUTTON, OnPseudoLeverPress)

        self.startButton = wx.Button(self, label = "Start", pos = (260,300) )
        self.Bind (wx.EVT_BUTTON, self.OnStart, self.startButton)

        self.stopButton = wx.Button(self, label = "Stop", pos = (260,360) )
        self.Bind (wx.EVT_BUTTON, self.OnStop, self.stopButton)
        
        self.resetButton = wx.Button(self,label="Reset Counter", pos=(300,680))
        self.Bind(wx.EVT_BUTTON, self.OnResetCounter, self.resetButton)

        
        # Default valutes
        self.numberPulses = "1"
        self.pulseInterval = "0"
        self.pulseDuration = "100"
        self.experimentDuration = "60"
        self.rewardInterval = "5"
        self.rewardDuration = "43"
        self.iti = "2"
        self.toneDuration = "1000"
       
        # Text input
        
        self.rDuration = wx.StaticText(self, label="Duration (ms): ",pos=(40,340))
        self.wDuration = wx.TextCtrl(self, value=self.pulseDuration, pos=(115, 336), size=(40,-1))
        self.Bind(wx.EVT_TEXT, self.evtDuration, self.wDuration)
        
        self.rExperimentDur = wx.StaticText(self, label="Experiment Duration (s): ",pos=(220,130))
        self.wExperimentDur = wx.TextCtrl(self, value=self.experimentDuration, pos=(345, 130), size=(35,-1))
        self.Bind(wx.EVT_TEXT, self.evtExperimentDur, self.wExperimentDur)
        
        self.rRewardInt = wx.StaticText(self, label="Reward Interval (s): ",pos=(220,160))
        self.wRewardInt = wx.TextCtrl(self, value=self.rewardInterval, pos=(345, 160), size=(35,-1))
        self.Bind(wx.EVT_TEXT, self.evtRewardInt, self.wRewardInt)

        self.rRewardDur = wx.StaticText(self, label="Reward Duration (ms): ",pos=(220,190))
        self.wRewardDur = wx.TextCtrl(self, value=self.rewardDuration, pos=(345, 190), size=(35,-1))
        self.Bind(wx.EVT_TEXT, self.evtRewardDur, self.wRewardDur)

        self.rITI = wx.StaticText(self, label =" Inter Trial Interval (s):", pos=(250,50))
        self.wITI = wx.TextCtrl(self, value = self.iti, pos=(365, 45), size=(20,-1))
        self.Bind(wx.EVT_TEXT, self.evtITI, self.wITI)

        self.rToneDur = wx.StaticText(self, label=" Tone Duration (ms):", pos=(20,160))
        self.wToneDur = wx.TextCtrl(self, value=self.toneDuration, pos=(120, 155), size=(40,-1))
        self.Bind(wx.EVT_TEXT, self.evtToneDur, self.wToneDur)

        self.rExperimentTime = wx.StaticText(self, label=" Experiment Time ", pos=(50,650))
        self.wExperimentTime = wx.TextCtrl(self, value="0", pos=(160, 648), size=(60,-1))

        self.rNumRewards = wx.StaticText(self, label=" # of Rewards ", pos=(300,650))
        self.wNumRewards = wx.TextCtrl(self, value="0", pos=(380, 648), size=(40,-1))
        self.Bind(wx.EVT_TEXT, self.evtNumRewards,self.wNumRewards)

        self.rTimeTone = wx.StaticText(self, label=" Time from Tone ", pos=(50,710))
        self.wTimeTone = wx.TextCtrl(self, value="0", pos=(160, 708), size=(60,-1))   

        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        

    def OnDeliver(self,event, nP, pI, rD, mode):
        self.deliverButton.Disable()
        self.deliveryT = DeliveryThread(nP,pI,rD, mode)

    def OnResetCounter(self,evt):
        self.wNumRewards.SetValue("0")
        Frame.Panel1.numberOfRewards=0
        
               
# IMP Note: Digital Inputs are normally pulled high
# IMP Note: 'Normal Close' for Lever Input

    def OnStop(self, event):
        self.worker.stop()
        self.startButton.Enable()
        writeToFile()

    def OnStart(self, event):
        if len(self.timeStamps)>0:
            clearGraphs()
            self.timeStamps = []
        if Frame.Panel1.numValves == 0:
            Frame.Panel1.logger.AppendText("Error: no valve selected.\n")
            return
        self.worker = MainThread()
        #Disable any widgets which could affect your thread
        self.startButton.Disable()
        
    def evtDuration(self, event):
        self.pulseDuration = event.GetString()

    def evtExperimentDur(self, event):
        self.experimentDuration = event.GetString()
        updateScope(float(self.experimentDuration))

    def evtRewardInt(self, event):
        self.rewardInterval = event.GetString()

    def evtRewardDur(self, event):
        self.rewardDuration = event.GetString()

    def evtITI(self, event):
        self.iti = event.GetString()

    def evtToneDur(self, event):
        self.toneDuration= event.GetString()

    def evtNumRewards(self,event):
        newcount = event.GetString()
        self.numberOfRewards = string.atoi(newcount)

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
        self.Panel2 = GraphPanel(self)
        grid.AddMany([(self.Panel1, 1, wx.EXPAND|wx.TOP|wx.LEFT,9), (self.Panel2, 1, wx.EXPAND|wx.TOP|wx.RIGHT, 9)])

        self.SetSizer(grid)
        self.Centre()
        self.Show(True)

def updateScope(y):
    Frame.Panel2.axes.axis([0,1,0,y])
    Frame.Panel2.canvas.draw()

def clearGraph():
    Frame.Panel2.axes.clear()
    Frame.Panel2.canvas.draw()
    #Frame.Panel2 = GraphPanel(Frame)
        
app = wx.App(False)  # Create a new app, don't redirect stdout/stderr to a window.     
Frame = MyFrame(None, -1, frameName)
Frame.tonePlayed = False
app.MainLoop()




