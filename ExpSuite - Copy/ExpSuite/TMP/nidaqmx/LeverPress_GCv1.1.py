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

'''

Importing plotting libraries

'''
import wx.lib.plot as plot

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbars

import pylab

'''
Global Variables
'''

system = System()
dev = system.devices[0]

time.clock();

# all the calls to time.clock() funtion in the program would-
# -return the time elapsed since the call to this function

random.seed();

frameName = "NI-DAQ " + dev.get_product_type();


def writeToFile():
    fileName = 'C:/Users/giancarlo/Desktop/Project/Time Stamps/' + datetime.now().strftime("%Y.%B.%d, %H.%M.%S") + '.txt'
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
        
        Frame.Panel1.deliveryT.stop() # might not be needed, because it is only setting the flag to False, and flag is not used anywhere
        Frame.Panel1.deliverButton.Enable()

    def stop(self):
        self.stop_flag = True # stop_flag not required here, because no Stop Button
        

class MainThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        

        self.stop_flag = False

        #This calls the run() to start the new thread
        self.start()
        self.rewardCounter = 0


    def run(self):
        """ Over-rides the super-classes run()"""
        taskI = DigitalInputTask()
        taskI.create_channel('Dev1/Port0/Line0')

        Frame.Panel1.channelNeuralynx2 = Frame.Panel1.channels[18]

        taskO_Neuralynx2 = DigitalOutputTask()
        taskO_Neuralynx2.create_channel(Frame.Panel1.channelNeuralynx2)
        
        taskI.start()

        T0 = time.clock()
        T1 = time.clock()
        T2 = time.clock()
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
        
        while (T2-T1) < string.atoi(Frame.Panel1.experimentDuration):

            T6 = time.clock()
   
            Frame.Panel1.editname8.ChangeValue(str(T6-T5))
            
            if self.stop_flag:
                break
            (data,abc) = taskI.read(samples_per_channel = 1, timeout = -1, fill_mode = 'group_by_channel')
            
            if T2 - T3 >= string.atoi(Frame.Panel1.iti):

                taskO_Neuralynx2.write(1)
                taskO_Neuralynx2.write(0)
                
                Frame.Panel1.OnDeliver(None, 1, 0, tD, 2)
                Frame.Panel1.timeStamps.append( ('Tone Delivery ',time.clock()) )
                Frame.Panel1.logger.AppendText('\n\n%s Tone \n\n' % time.clock())
                timeFromToneCounter = 1
                T0 = T2 + tD
                T7 = T2 + tD
                T3 = 999999

            if (T2 - T7 >= 0 and timeFromToneCounter == 1):
                Frame.Panel1.editname10.ChangeValue( str(T2-T7) )            
            
            if T2 - T0 >= string.atoi(Frame.Panel1.rewardInterval) :
                self.rewardCounter = 1
                T0 = 999999
                

                
# earlier when T3 was set to 999, this loop would go infinitely if the program has
# run for 999 seconds
                
            if data[0][0] == 1 and counter == 1:
                
                taskO_Neuralynx2.write(1)
                taskO_Neuralynx2.write(0)
                
                Frame.Panel1.timeStamps.append( ('Lever Press ',time.clock()) )
                counter = 0
                Frame.Panel1.logger.AppendText('%s \n' % time.clock())
                if self.rewardCounter == 1:
                    
                    taskO_Neuralynx2.write(1)
                    taskO_Neuralynx2.write(0)
                    
                    timeFromToneCounter = 0
                    Frame.Panel1.OnDeliver(None, 1, 0, rD, 1)
                    Frame.Panel1.logger.AppendText('\n\n%s Taste \n\n' % time.clock())
                    Frame.Panel1.timeStamps.append( ('Taste Delivery ',time.clock()) )
                    Frame.Panel1.numberOfRewards += 1
                    Frame.Panel1.editname9.ChangeValue(str(Frame.Panel1.numberOfRewards))
                    self.rewardCounter = 0
                    T3 = T2

            elif data[0][0] == 0:
                counter = 1

                taskO_Neuralynx2.write(1)
                taskO_Neuralynx2.write(0)
                
                if Frame.Panel1.deliverManualTaste == 1:
                    Frame.Panel1.logger.AppendText('\n\n%s Taste \n\n' % time.clock())
                    Frame.Panel1.timeStamps.append( ('Taste Delivery ',time.clock()) )
                    Frame.Panel1.numberOfRewards += 1
                    Frame.Panel1.editname9.ChangeValue(str(Frame.Panel1.numberOfRewards))
                    self.rewardCounter = 0
                    T3 = T2
                    T2 = 999999
                    Frame.Panel1.deliverManualTaste = 0
            T2 = time.clock()
            
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

        self.numberOfRewards = 0

        self.deliverManualTaste = 0

        self.valveArray = numpy.zeros ( 8, int )

        self.timeStamps = []
        
        self.numValves = 0

        self.openValves = []

        self.channels = ['Dev1/Port5/Line5', 'Dev1/Port2/Line7', 'Dev1/Port5/Line7', 'Dev1/Port5/Line4', 'Dev1/Port2/Line4', 'Dev1/Port2/Line5', 'Dev1/Port5/Line6', 'Dev1/Port2/Line6', 'Dev1/Port11/Line7', 'Dev1/Port4/Line7','Dev1/Port4/Line6','Dev1/Port4/Line5','Dev1/Port4/Line4','Dev1/Port4/Line3','Dev1/Port4/Line2','Dev1/Port4/Line1','Dev1/Port4/Line0','Dev1/Port3/Line7','Dev1/Port3/Line6'] 

        # Channel Menu [Valve1, Valve2, Valve3, Valve4, Valve5, Valve6, Valve7, Valve8, Tone1, Neuralynx Pair 1, Neuralynx Pair 2, Neuralynx Pair 3, Neuralynx Pair 4, Neuralynx Pair 5, Neuralynx Pair 6, Neuralynx Pair 7, Neuralynx Pair 8, Neuralynx Pair 9, Neuralynx Pair 10]

        self.channelInUse = ''
        
        self.logger = wx.TextCtrl(self, pos=(20,400), size=(400,200), style=wx.TE_MULTILINE | wx.TE_READONLY)        

        self.valve1 = wx.ToggleButton(self, 1, 'Valve 1', (20, 25))
        self.valve2 = wx.ToggleButton(self, 2, 'Valve 2', (20, 55))
        self.valve3 = wx.ToggleButton(self, 3, 'Valve 3', (20, 85))
        self.valve4 = wx.ToggleButton(self, 4, 'Valve 4', (20, 115))

        self.valve5 = wx.ToggleButton(self, 5, 'Valve 5', (110, 25))
        self.valve6 = wx.ToggleButton(self, 6, 'Valve 6', (110, 55))
        self.valve7 = wx.ToggleButton(self, 7, 'Valve 7', (110, 85))
        self.valve8 = wx.ToggleButton(self, 8, 'Valve 8', (110, 115))

        self.Bind( wx.EVT_TOGGLEBUTTON, self.OnToggle1, id = 1 )
        self.Bind( wx.EVT_TOGGLEBUTTON, self.OnToggle2, id = 2 )
        self.Bind( wx.EVT_TOGGLEBUTTON, self.OnToggle3, id = 3 )
        self.Bind( wx.EVT_TOGGLEBUTTON, self.OnToggle4, id = 4 )
        self.Bind( wx.EVT_TOGGLEBUTTON, self.OnToggle5, id = 5 )
        self.Bind( wx.EVT_TOGGLEBUTTON, self.OnToggle6, id = 6 )
        self.Bind( wx.EVT_TOGGLEBUTTON, self.OnToggle7, id = 7 )
        self.Bind( wx.EVT_TOGGLEBUTTON, self.OnToggle8, id = 8 )


        # Text Input

        #self.lblname0 = wx.StaticText(self, label=" Number of Pulses ", pos=(20,150))
        #self.editname0 = wx.TextCtrl(self, value="1", pos=(140, 150), size=(50,-1))
        #self.Bind(wx.EVT_TEXT, self.EvtText0, self.editname0)
        self.numberPulses = "1"

        # Text Input

        #self.lblname1 = wx.StaticText(self, label="Pulse Interval (ms): ", pos=(20,180))
        #self.editname1 = wx.TextCtrl(self, value="0", pos=(140, 180), size=(50,-1))
        #self.Bind(wx.EVT_TEXT, self.EvtText1, self.editname1)
        self.pulseInterval = "0"

        # Text Input
        
        self.lblname2 = wx.StaticText(self, label="Duration (ms): ",pos=(40,340))
        self.editname2 = wx.TextCtrl(self, value="100", pos=(115, 336), size=(40,-1))
        self.Bind(wx.EVT_TEXT, self.EvtText2, self.editname2)
        self.pulseDuration = "100"

        # Buttons
        self.deliverButton = wx.Button(self, label="Manual Taste", pos = (60, 300) )

        def helperDeliver(evt):
            self.deliverManualTaste = 1
            nP = string.atoi(self.numberPulses)
            pI = string.atoi(self.pulseInterval)
            rD = string.atoi(self.pulseDuration) / 1000.0
            return self.OnDeliver(evt, nP, pI, rD, 1)
        
        self.Bind(wx.EVT_BUTTON, helperDeliver, self.deliverButton)

        self.startButton = wx.Button(self, label = "Start", pos = (260,300) )
        self.Bind (wx.EVT_BUTTON, self.OnStart, self.startButton)

        self.stopButton = wx.Button(self, label = "Stop", pos = (260,360) )
        self.Bind (wx.EVT_BUTTON, self.OnStop, self.stopButton)
       
        # Text input
        
        self.lblname3 = wx.StaticText(self, label="Experiment Duration (s): ",pos=(220,130))
        self.editname3 = wx.TextCtrl(self, value="60", pos=(345, 130), size=(35,-1))
        self.Bind(wx.EVT_TEXT, self.EvtText3, self.editname3)
        self.experimentDuration = "60"

        # Text Input
        
        self.lblname4 = wx.StaticText(self, label="Reward Interval (s): ",pos=(220,160))
        self.editname4 = wx.TextCtrl(self, value="5", pos=(345, 160), size=(35,-1))
        self.Bind(wx.EVT_TEXT, self.EvtText4, self.editname4)
        self.rewardInterval = "5"

        # Text Input
        
        self.lblname5 = wx.StaticText(self, label="Reward Duration (ms): ",pos=(220,190))
        self.editname5 = wx.TextCtrl(self, value="43", pos=(345, 190), size=(35,-1))
        self.Bind(wx.EVT_TEXT, self.EvtText5, self.editname5)
        self.rewardDuration = "43"

        # Text Input

        self.lblname6 = wx.StaticText(self, label =" Inter Trial Interval (s):", pos=(250,50))
        self.editname6 = wx.TextCtrl(self, value = "2", pos=(365, 45), size=(20,-1))
        self.Bind(wx.EVT_TEXT, self.EvtText6, self.editname6)
        self.iti = "2"


        # Text Input

        self.lblname7 = wx.StaticText(self, label=" Tone Duration (ms):", pos=(20,160))
        self.editname7 = wx.TextCtrl(self, value="1000", pos=(120, 155), size=(40,-1))
        self.Bind(wx.EVT_TEXT, self.EvtText7, self.editname7)
        self.toneDuration = "1000"

        # Text Display

        self.lblname8 = wx.StaticText(self, label=" Experiment Duration ", pos=(50,650))
        self.editname8 = wx.TextCtrl(self, value="0", pos=(160, 648), size=(60,-1))

        # Text Display

        self.lblname9 = wx.StaticText(self, label=" # of Rewards ", pos=(300,650))
        self.editname9 = wx.TextCtrl(self, value="0", pos=(380, 648), size=(40,-1))

        # Text Display

        self.lblname10 = wx.StaticText(self, label=" Time from Tone ", pos=(175,710))
        self.editname10 = wx.TextCtrl(self, value="0", pos=(260, 708), size=(40,-1))   

        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def OnDeliver(self,event, nP, pI, rD, mode):
        self.deliverButton.Disable()
        self.deliveryT = DeliveryThread(nP,pI,rD, mode)
        
        
               
# IMP Note: Digital Inputs are normally pulled high
# IMP Note: 'Normal Close' for Lever Input

    def OnStop(self, event):
        self.worker.stop()
        self.startButton.Enable()
        writeToFile()

    def OnStart(self, event):
        self.timeStamps = []
        if Frame.Panel1.numValves == 0:
            Frame.Panel1.logger.AppendText("Error: no valve selected.\n")
            return
        self.worker = MainThread()
        #Disable any widgets which could affect your thread
        self.startButton.Disable()
        

    def OnToggle1(self,event):
        if self.valveArray[0] == 1:
            self.valveArray[0] = 0
            self.numValves -= 1
            self.openValves.remove(0)
        else:
            self.valveArray[0] = 1
            self.numValves += 1
            self.openValves.append(0)
            
    def OnToggle2(self,event):
        if self.valveArray[1] == 1:
            self.valveArray[1] = 0
            self.numValves -= 1
            self.openValves.remove(1)
        else:
            self.valveArray[1] = 1
            self.numValves += 1
            self.openValves.append(1)
            
            
    def OnToggle3(self,event):
        if self.valveArray[2] == 1:
            self.valveArray[2] = 0
            self.numValves -= 1
            self.openValves.remove(2)
        else:
            self.valveArray[2] = 1
            self.numValves += 1
            self.openValves.append(2)
            
    def OnToggle4(self,event):
        if self.valveArray[3] == 1:
            self.valveArray[3] = 0
            self.numValves -= 1
            self.openValves.remove(3)
        else:
            self.valveArray[3] = 1
            self.numValves += 1
            self.openValves.append(3)
            
    def OnToggle5(self,event):
        if self.valveArray[4] == 1:            
            self.valveArray[4] = 0
            self.numValves -= 1
            self.openValves.remove(4)
        else:
            self.valveArray[4] = 1
            self.numValves += 1
            self.openValves.append(4)
            
    def OnToggle6(self,event):
        if self.valveArray[5] == 1:
            self.valveArray[5] = 0
            self.numValves -= 1
            self.openValves.remove(5)
        else:
            self.valveArray[5] = 1
            self.numValves += 1
            self.openValves.append(5)
            
    def OnToggle7(self,event):
        if self.valveArray[6] == 1:
            self.valveArray[6] = 0
            self.numValves -= 1
            self.openValves.remove(6)
        else:
            self.valveArray[6] = 1
            self.numValves += 1
            self.openValves.append(6)
            
    def OnToggle8(self,event):
        if self.valveArray[7] == 1:
            self.valveArray[7] = 0
            self.numValves -= 1
            self.openValves.remove(7)
        else:
            self.valveArray[7] = 1
            self.numValves += 1
            self.openValves.append(7)
        
        
    def EvtText0(self, event):
        self.logger.AppendText('No. of Pulses: %s\n' % event.GetString())
        self.numberPulses = event.GetString()

    def EvtText1(self, event):
        self.pulseInterval = event.GetString()

    def EvtText2(self, event):
        self.pulseDuration = event.GetString()

    def EvtText3(self, event):
        self.experimentDuration = event.GetString()

    def EvtText4(self, event):
        self.rewardInterval = event.GetString()

    def EvtText5(self, event):
        self.rewardDuration = event.GetString()

    def EvtText6(self, event):
        self.iti = event.GetString()

    def EvtText7(self, event):
        self.toneDuration= event.GetString()

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
        
app = wx.App(False)  # Create a new app, don't redirect stdout/stderr to a window.     
Frame = MyFrame(None, -1, frameName)
app.MainLoop()




