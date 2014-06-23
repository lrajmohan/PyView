'''
PyView Version 1.0

This program  handles the Digital Input and Output he National Instruments DAQmx USB-6509 device.
This could be used to run reward based experiments to train rats and to record the neural activity
in their gustatory cortex.

Last Updated: June 5, 2012
Appended By: Alice Q. Wong [aliceqwon@gmail.com]

'''

DEVICE_ON = False

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
from ctypes import *
import threading
import wx
import numpy
import time
import string
import random
from sys import argv
from datetime import datetime
import os
import shutil
import re
import functools
import math
import Ferret

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import _load_bitmap
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import pylab
from pulsar import *
import  wx.lib.rcsizer  as Table
import  wx.lib.scrolledpanel as scrolled

'''
Global Variables
'''
if DEVICE_ON:
    system = System()
    dev = system.devices[0]

# all the calls to time.clock() funtion in the program would-
# -return the time elapsed since the call to this function

random.seed()
cheese = { 'totalRunTime':0, 'trialRunTime':0, 'numRewards':0, 'numTaste':0, 'toneAt':0.0, 'rewardAt':0.0, 'timeOffset':0.0,  'freq':0,
          'tonePlaying':False, 'tonePlayed': False, 'timeStamps':[], 'deliverManualTaste':False, 'pseudoPress':False, 'startTime':0.0, 't0':0.0, 
          'newTrial':False, 'selValve':0, 'defaultDir':'', 'restartAct':None}
derby = 0
openValves = []

valveChan = [('Dev1/Port5/Line5','Dev1/Port4/Line7'),('Dev1/Port2/Line7','Dev1/Port4/Line6'),
      ('Dev1/Port5/Line7','Dev1/Port4/Line5'),('Dev1/Port5/Line4','Dev1/Port4/Line4'),
      ('Dev1/Port2/Line4','Dev1/Port4/Line3'),('Dev1/Port2/Line5','Dev1/Port4/Line2'),
      ('Dev1/Port5/Line6','Dev1/Port4/Line1'),('Dev1/Port2/Line6','Dev1/Port4/Line0')]
toneChan = ('Dev1/Port11/Line0:7','Dev1/Port3/Line7')
leverChan = ('Dev1/Port0/Line0','Dev1/Port3/Line6')
markerChan = 'Dev1/Port2/Line1'


'''
DeliveryThread Class inherited from Thread class. It takes care of all the
deliveries in the experiment, for example taste de'Dev1/Port2/Line1'livery and tone delivery.

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
    def __init__( self, nP, pI, rD, mode, valve=-1):
        Thread.__init__(self)

        # making the parameters passed as local variable for this class
        
        self.np = nP
        self.pi = pI
        self.rd = rD
        self.m = mode
        self.valve = valve
        if mode==1 and valve==-1:
            self.valve = random.choice(openValves)
            cheese['selValve'] = self.valve
        self.stop_flag = False
        self.start()

        
    def run(self):
        channelInUse = ''
        channelNeuralynx = ''
        if len(openValves) == 0:
            Frame.CtrlPanel.logger.AppendText("\nError: no valve selected.\n")
            Frame.CtrlPanel.deliverButton.Enable()
            return
        if self.m == 1:
            channelInUse = valveChan[self.valve][0]
            channelNeuralynx = valveChan[self.valve][1]
            print "taste from Valve "+str(self.valve+1)
        elif self.m == 2:
            channelInUse = toneChan[0] 
            channelNeuralynx = toneChan[1]
        
        if DEVICE_ON:
            
            taskO_Neuralynx = DigitalOutputTask()
            taskO_Neuralynx.create_channel(channelNeuralynx)
        
            taskO = DigitalOutputTask()
            taskO.create_channel(channelInUse)
    
            taskO_Neuralynx.start()
            taskO.start()
            if self.m==2:
                i = freq2int(cheese['freq'])
                a = int2bi8(i)
                if len(a)>0:
                    taskO.write(a,layout='group_by_channel')
            else:
                taskO.write(1) # pulse delivered
    
            taskO_Neuralynx.write(1)
            taskO_Neuralynx.write(0)
            
            time.sleep(self.rd) #wait for reward duration
            if self.m==2:
                taskO.write([0,0,0,0,0,0,0,0],layout='group_by_channel')
            else:
                taskO.write(0) # pulse delivery stopped
    
            taskO.stop()
            taskO.clear()
    
            taskO_Neuralynx.stop()
            taskO_Neuralynx.clear()

        else:
            time.sleep(self.rd)
        
        self.stop()

    def stop(self):
        self.stop_flag = True # stop_flag not required here, because no Stop Button
        if self.m==2:
            cheese['tonePlaying'] = False
            cheese['toneAt'] = time.clock() - cheese['t0']
            cheese['tonePlayed'] = True
        if self.m==1:
            cheese['rewardAt'] = time.clock() - cheese['t0']

class NullEventThread (Thread):
    def __init__(self):
        Thread.__init__(self)
        self.stop_flag = False
        self.taskO_Neuralynx2 = DigitalOutputTask()
        self.taskO_Neuralynx2.create_channel(markerChan)
        self.start()

    def run(self):
        self.taskO_Neuralynx2.start()
        self.taskO_Neuralynx2.write(1)
        self.taskO_Neuralynx2.write(0)
        self.taskO_Neuralynx2.stop()
        self.taskO_Neuralynx2.clear()
        
    def stop(self):
        self.stop_flag = True
        
class MainThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.stop_flag = False
        self.giveReward = False
        self.redraw_flag = False
        self.leverPressed = False
        
        self.dispExpPastTime = 0.00
        self.dispTonePastTime = 0.00
    
    def sendTone(self,dur):
        cheese['tonePlaying'] = True
        cheese['tonePlayed'] = False
        cheese['toneAt'] = time.clock()
        cheese['timeStamps'].append( ('Tone Delivery',cheese['toneAt'],str(cheese['freq'])+' Hz') )
        log('\n\n%s Tone \n\n'% round(cheese['toneAt'],2) )
        X.bleu = DeliveryThread(1,0,dur,2,None)

    def pressedLever(self):
        cheese['timeStamps'].append( ('Lever Press ',cheese['totalRunTime'],'') )
        log('%s \n' % round(cheese['totalRunTime'],2))
    
    def threadAvailable(self):
        if X.bleu!=None:
            if X.bleu.isAlive():
                return False
            else:
                return True
        else:
            return True

    def updateTimes(self):
        cheese['totalRunTime'] = time.clock() - cheese['t0']
        cheese['trialRunTime'] = time.clock() - cheese['startTime'] + cheese['timeOffset']
        
        if round(cheese['totalRunTime'],2)!=self.dispExpPastTime:
            self.dispExpPastTime = round(cheese['totalRunTime'],2)
            Frame.CtrlPanel.wExperimentTime.SetLabel(str(self.dispExpPastTime))
        if cheese['tonePlayed']:
            if round(cheese['totalRunTime']-cheese['toneAt'],2)!=self.dispTonePastTime:
                self.dispTonePastTime = round(cheese['totalRunTime']-cheese['toneAt'],2)
                Frame.CtrlPanel.wTimeTone.SetLabel( str(self.dispTonePastTime) )
        
        self.updateIntPt()

    def updateIntPt(self):
        global derby
        if derby==-1:
            return
        ival = X.intervalList[derby]
        #jump to next interval
        if cheese['trialRunTime'] > (ival.startTime+ival.duration):
            X.intervalList[derby].completed = True
            if X.intervalList[derby].actions['End']!=None:
                # perform after interval action
                if isinstance(X.intervalList[derby], Intervals.NogoInt):
                   if X.intervalList[derby].ready:
                       X.intervalList[derby].actions['End'].perform(cheese['trialRunTime'])
                else:
                    X.intervalList[derby].actions['End'].perform(cheese['trialRunTime'])       
            derby+=1
            #passed interval boundaries
            if derby>=len(X.intervalList):
                derby = -1
            #at start of i
            else:
                if isinstance(X.intervalList[derby], Intervals.ToneInt):
                    Frame.CtrlPanel.updateValves(derby)
                    cheese['freq'] = X.intervalList[derby].freq
                elif isinstance(X.intervalList[derby], Intervals.NogoInt):
                    X.intervalList[derby].ready = True
                if X.intervalList[derby].actions['Begin']!=None:
                    # perform before interval action
                    X.intervalList[derby].actions['Begin'].perform(cheese['trialRunTime'])

    def run(self):
        if DEVICE_ON:
            taskI = DigitalInputTask()
            taskI.create_channel(leverChan[0])
            
            taskO_Neuralynx2 = DigitalOutputTask()
            taskO_Neuralynx2.create_channel(leverChan[1])
            
            taskI.start()
            taskO_Neuralynx2.start()
            taskO_Neuralynx2.write(0)
            taskO_Neuralynx2.write(0)
        
        self.updateTimes()
        log('\nExperiment Begins .. Trial Duration: %s seconds\n' % X.trialDuration)
        while not(self.stop_flag):

            self.giveReward = False
            self.leverPressed = False
            
            #detect lever presses
            if DEVICE_ON:
                (data,abc) = taskI.read(samples_per_channel = 1, timeout = -1, fill_mode = 'group_by_channel')
                self.leverPressed = (data[0][0] == 1)
                if self.leverPressed:
                    taskO_Neuralynx2.write(1)
                    taskO_Neuralynx2.write(0)
                    self.pressedLever()
            else:
                if cheese['pseudoPress']:
                    self.leverPressed = True
                    cheese['pseudoPress'] = False
                    self.pressedLever()
                    
            
            #actions depedent on intervals     
            if derby==-1:
                pass
            
            elif isinstance(X.intervalList[derby], Intervals.ToneInt):
                if DEVICE_ON:
                    taskO_Neuralynx2.write(1)
                    taskO_Neuralynx2.write(0)
                if not(cheese['tonePlaying']) and self.threadAvailable():
                    self.sendTone(X.intervalList[derby].duration)
                    
            elif isinstance(X.intervalList[derby], Intervals.RewardInt):
                if self.leverPressed:
                    if DEVICE_ON:
                        taskO_Neuralynx2.write(1)
                        taskO_Neuralynx2.write(0)
                    if X.intervalList[derby].actions['Lever']!=None:
                        X.intervalList[derby].actions['Lever'].perform(cheese['trialRunTime'])
                    self.giveReward= True
            elif isinstance(X.intervalList[derby], Intervals.NogoInt):
                if self.leverPressed:
                    X.intervalList[derby].ready = False
            else:
                pass
            
            #draw if just lv press
            if self.leverPressed and not(self.giveReward):
                Frame.Graph.addPoint(cheese['trialRunTime'],30)
                self.redraw_flag = True
            
            #send manual reward
            for a in X.actionList:
                if a.isManual and a.ready:
                    if DEVICE_ON:
                        taskO_Neuralynx2.write(1)
                        taskO_Neuralynx2.write(0)
                    a.perform(cheese['trialRunTime'])
                    if isinstance(a, Actions.Taste):
                        self.giveReward = True
                    a.ready = False   
            
            if cheese['newTrial']:
                Frame.Graph.newTrial()
                cheese['newTrial']= False
                self.redraw_flag = True
               
            self.updateTimes()
            if self.redraw_flag:
                Frame.Graph.Refresh()
                self.redraw_flag = False 
            
            if cheese['trialRunTime']>X.trialDuration:
                cheese['restartAct'].perform(cheese['trialRunTime'])
            if X.terminator!=None and not(self.stop_flag):
                if isinstance(X.terminator, Conditions.TimeLimit):
                    self.stop_flag = X.terminator.test(cheese['totalRunTime'])
                elif isinstance(X.terminator, Conditions.TrialsLimit):
                    self.stop_flag = X.terminator.test(Frame.Graph.trial)
                elif isinstance(X.terminator, Conditions.RewardsLimit):
                    self.stop_flag = X.terminator.test(cheese['numRewards'])
                else:
                    pass
        #end of loop
        
        
        writeToFile()
        log('\nEnd of experiment.\n')
        
        if DEVICE_ON:
            taskO_Neuralynx2.write(0)
            taskO_Neuralynx2.write(0)
            taskO_Neuralynx2.stop()
            taskO_Neuralynx2.clear()
            taskI.stop()
            taskI.clear()
                
    def stop(self):
        self.stop_flag = True

class ScatterBrain(object):
    def __init__(self,name,c='#000000',m='o',f=True):
        self.name = name
        self.x = []
        self.y = []
        self.color = c
        self.marker=m
        self.filled = f
        
    def setStyle(self,color,marker,filled=True):
        self.color = color
        self.marker = marker
        self.filled = filled
    
    def addPoint(self, x,y):
        self.x.append(x)
        self.y.append(y)
    
    def getPlot(self,axes):
        fc = 'none'
        if self.filled:
            fc = self.color
        return axes.scatter(self.x,self.y,c=self.color,marker=self.marker,
                            facecolors=fc, edgecolors=self.color, zorder=10)

class GraphPanel(wx.Panel):
    def __init__(self,parent,ctrl):
        wx.Panel.__init__(self,parent)
        self.SetBackgroundColour('#FFFFFF')
        self.SetSizeWH(500,600)
        self.ctrlPanel = ctrl
        self.initGraph()
        wx.EVT_PAINT(self, self.OnPaint)


    def initGraph(self):
        self.trial = 1
        self.sbs = {}
        self.sbs['Lever'] = ScatterBrain('Lever','#3399FF','s')
        self.sbs['Mark'] = ScatterBrain('Mark','#000000','x')
        for i in range(0,8):
            name = 'aTaste%d'%i
            self.sbs[name] = ScatterBrain(name,Ferret.TasteColors[i],'o')
            name2 = 'mTaste%d'%i
            self.sbs[name2] = ScatterBrain(name2,Ferret.TasteColors[i],'o',False)
        
        self.figure = Figure(dpi=100,figsize=(5,5.8))
        self.axes = self.figure.add_subplot(111)
        self.axes.axis([0,X.trialDuration,0,1.5])
        self.axes.set_xlabel('time (s)')


        for i in X.intervalList:
            if isinstance(i, Intervals.WaitInt):
                continue
            color = Ferret.iColors[i.type]
            if isinstance(i, Intervals.ToneInt):
                color = Ferret.freq2color(i.freq)
            self.axes.axvspan(i.startTime,i.startTime+i.duration,facecolor=color,alpha=0.5,lw=0.0, zorder=0)
            
        
        LText = FontProperties()
        LText.set_size("small")
        
        
        self.axes.legend((self.sbs['Lever'].getPlot(self.axes),self.sbs['Mark'].getPlot(self.axes),
                          self.sbs['aTaste1'].getPlot(self.axes),self.sbs['mTaste1'].getPlot(self.axes)),
                         ("Lever Press","Time Marked", "Reward Given","Manual Reward"),
                         prop=LText, fancybox=True, bbox_to_anchor=(0., 1.02, 1., .102), loc=1, ncol=2, mode="expand", borderaxespad=0)
        
        self.canvas = FigureCanvas(self, -1, self.figure)
    
    def clearGraph(self):
        self.figure.delaxes(self.axes)
        self.initGraph()
        self.Refresh()
    
    def addPoint(self,t,pcat):
        if pcat<8:
            self.sbs['aTaste%d'%pcat].addPoint(t,self.trial)
        elif pcat<16:
            self.sbs['mTaste%d'%(pcat-8)].addPoint(t,self.trial)
        elif pcat==30:
            self.sbs['Lever'].addPoint(t,self.trial)
        elif pcat==31:
            self.sbs['Mark'].addPoint(t,self.trial)
    
    def newTrial(self):
        self.trial+=1
        self.axes.set_ylim(top=(self.trial+0.5))
        
    def OnPaint(self, event):
        for k,v in self.sbs.items():
            v.getPlot(self.axes)
        self.canvas.draw()
        event.Skip()

    def OnSetFocus(self, event):
        self.color = 'yellow'
        self.Refresh()

    def OnKillFocus(self, event):
        self.color = '#b3b3b3'
        self.Refresh()
    
    def saveGraph(self,filename="graph.png"):
        self.figure.savefig(filename)


class MainPanel(wx.Panel):
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.quote = wx.StaticText(self, label="MAIN PANEL", pos=(200, 10))
        self.SetSizeWH(400,600)
        ss = Table.RowColSizer()

        # ignore pulses for now
        self.numberPulses = 1
        self.pulseInterval = 0
        self.pulseDuration = 100
        
        ss.Add(wx.StaticText(self,label="Open Valves"),row=2,col=1,rowspan=2,colspan=1)

        def OnToggleValve(event):
            global openValves
            obj = event.GetEventObject()
            objId = obj.GetId()
            n = objId - 1
            if obj.GetValue():
                openValves.append(n)
            else:
                try:
                    openValves.remove(n)
                except ValueError:
                    pass
                
        buttonGroup = wx.GridSizer(2,4,0,0)
        
        self.valveButtons = []
        
        for i in range(0,8):
            self.valveButtons.append(wx.ToggleButton(self, i+1, Ferret.TasteNames[i]))
            self.valveButtons[i].Bind(wx.EVT_TOGGLEBUTTON,OnToggleValve)
            buttonGroup.Add(self.valveButtons[i],0,wx.EXPAND)

        ss.Add(buttonGroup, row=2, col=2, rowspan=3, colspan=3)
        
        rExperimentDur = wx.StaticText(self, label="Trial Duration (s): ")
        self.wExperimentDur = wx.TextCtrl(self, value=str(X.trialDuration), size=(35,-1))
        self.Bind(wx.EVT_TEXT, self.evtExperimentDur, self.wExperimentDur)
        ss.Add(rExperimentDur, row=1, col=1)
        ss.Add(self.wExperimentDur, row=1, col=2)
        
        rPulseDuration = wx.StaticText(self, label="Pulse Duration (ms): ")
        self.wPulseDuration = wx.TextCtrl(self, value=str(self.pulseDuration), size=(40,-1))
        self.Bind(wx.EVT_TEXT, self.evtPulseDuration, self.wPulseDuration)
        ss.Add(rPulseDuration,row=1, col=3)
        ss.Add(self.wPulseDuration,row=1,col=4)
        
        self.pseudoLever = wx.Button(self,label="Lever Press")
        def OnPseudoLeverPress(event):
            cheese['pseudoPress'] = True
        self.Bind(wx.EVT_BUTTON, OnPseudoLeverPress, self.pseudoLever)
        ss.Add(self.pseudoLever, row=5,col=3)
        
        self.markButton = wx.Button(self,label="Mark Time")
        self.Bind(wx.EVT_BUTTON, self.OnMarkTime, self.markButton)
        ss.Add(self.markButton, row=5, col=2)
        
        self.resetButton = wx.Button(self,label="Reset Counter")
        self.Bind(wx.EVT_BUTTON, self.OnResetCounter, self.resetButton)
        ss.Add(self.resetButton,row=5,col=4)
     
        counterGroup = wx.GridSizer(2,4,0,0)
     
        rExperimentTime = wx.StaticText(self, label=" Experiment Time ")
        self.wExperimentTime = wx.StaticText(self, label="0")
        
        rTimeTone = wx.StaticText(self, label=" Time from Tone ")
        self.wTimeTone = wx.StaticText(self, label="0")  

        rNumRewards = wx.StaticText(self, label=" # of Rewards ")
        self.wNumRewards = wx.StaticText(self, label="0")

        rManTaste = wx.StaticText(self,label=" # of Manual Tastes ")
        self.wManTaste = wx.StaticText(self, label="0")
        
        counterGroup.AddMany([(rExperimentTime,0,wx.EXPAND),(self.wExperimentTime,0,wx.EXPAND), (rTimeTone,0,wx.EXPAND),(self.wTimeTone,0,wx.EXPAND),
                              (rNumRewards,0,wx.EXPAND), (self.wNumRewards,0,wx.EXPAND),(rManTaste,0,wx.EXPAND),(self.wManTaste,0,wx.EXPAND)])
        
        ss.Add(counterGroup, row=6, col=1, rowspan=2, colspan=4)

        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        
        ss.Add(wx.StaticText(self,label="Logger"),row=8,col=1,colspan=4,flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.logger = wx.TextCtrl(self,size=(400,100), style=wx.TE_MULTILINE | wx.TE_READONLY) 
        ss.Add(self.logger,row=9,col=1, rowspan=4,colspan=4, flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_BOTTOM)
        
        self.xPanel = scrolled.ScrolledPanel(self, -1, size=(420, 200), style = wx.TAB_TRAVERSAL, name="ExperimentControls" )
        ss.Add(self.xPanel, row=14,col=1,colspan=4)
        
        self.xPanel.intervalGroup = None
        self.xPanel.actionGroup = None
        self.iFields = len(X.intervalList)*[None]
        
        self.initStuff()
                     
        self.SetSizerAndFit(ss)

    def setSibling(self,graph):
        self.graphPanel = graph

    def OnResetCounter(self,evt):
        self.wNumRewards.SetLabel("0")
        cheese['numRewards']=0
        self.wManTaste.SetLabel("0")
        cheese['numTaste']=0
    
    def txtListener(self,event):
        obj = event.GetEventObject()
        objId = obj.GetId()
        try:
            X.intervalList[objId].duration = float(event.GetString())
        except ValueError:
            pass
        X.adjustPostIntTimes(objId)
    
    def varyDurBy(self,event):
        obj = event.GetEventObject()
        objId = obj.GetId()
        try:
            X.intervalList[objId].varyBy = float(event.GetString())
        except ValueError:
            pass

    def varyDur(self,event):
        obj = event.GetEventObject()
        objId = obj.GetId()
        if event.IsChecked():
            r = random.random()
            X.intervalList[objId].duration = X.intervalList[objId].oriDur+X.intervalList[objId].varyBy*(2.0*r-1.0)
            X.adjustPostIntTimes(objId);
            X.intervalList[objId].vary = True
        else:
            X.intervalList[objId].duration = X.intervalList[objId].oriDur
            X.adjustPostIntTimes(objId);
            X.intervalList[objId].vary = False
        self.iFields[objId].SetValue(str(X.intervalList[objId].duration))
    
    def abClick(self,event):
        obj = event.GetEventObject()
        objId = obj.GetId()
        X.actionList[objId].ready = True
        
    def initStuff(self):
        xsizer = wx.BoxSizer(wx.VERTICAL)
        if self.xPanel.intervalGroup!=None:
            self.xPanel.intervalGroup.Clear(True)
            self.xPanel.actionGroup.Clear(True)
            self.iFields = len(X.intervalList)*[None]
        self.xPanel.intervalGroup = wx.GridSizer(10,4,0,0)
        self.xPanel.actionGroup = wx.GridSizer(3,4,0,0)

        firstTone = -1
        i = 0
        for itt in X.intervalList:
            desc = wx.StaticText(self.xPanel,label=(itt.name+" (s): "))
            self.iFields[i] = wx.TextCtrl(self.xPanel, value=str(itt.duration), size=(35,-1), id=i)
            vary = wx.CheckBox(self.xPanel, i, "vary by")
            if itt.vary:
                vary.SetValue(True)
                vd = itt.duration+itt.varyBy*(2.0*random.random()-1.0)
                itt.duration = vd;
                self.iFields[i].SetValue(str(vd))
            varyBy = wx.TextCtrl(self.xPanel,value=str(itt.varyBy), size=(30,-1), id=i)
            self.iFields[i].Bind(wx.EVT_TEXT,self.txtListener)
            vary.Bind(wx.EVT_CHECKBOX, self.varyDur)
            varyBy.Bind(wx.EVT_TEXT, self.varyDurBy)
            self.xPanel.intervalGroup.AddMany([desc,self.iFields[i],vary, varyBy])
            if isinstance(itt, Intervals.ToneInt) and firstTone==-1:
                firstTone = i
            i+=1
                
        if firstTone>=0:
            self.updateValves(firstTone)
            cheese['freq'] = X.intervalList[firstTone].freq
        
        i=0
        for act in X.actionList:
            if act.isManual:
                actButton = wx.Button(self.xPanel, label=act.name, id=i )
                self.Bind(wx.EVT_BUTTON, self.abClick, actButton)
                self.xPanel.actionGroup.Add(actButton)
            i+=1

        xsizer.Add(self.xPanel.intervalGroup)
        xsizer.AddSpacer(10,400)
        xsizer.Add(self.xPanel.actionGroup)
        self.xPanel.SetSizer(xsizer)
        self.xPanel.SetAutoLayout(True)
        self.xPanel.SetupScrolling()
        
    def evtPulseDuration(self, event):
        try:
            self.pulseDuration = int(event.GetString())
        except ValueError:
            pass
        
    def evtExperimentDur(self, event):
        try:
            X.trialDuration = float(event.GetString())
        except ValueError:
            pass
    
    def OnMarkTime(self,event):
        t = time.clock()
        cheese['timeStamps'].append(('Manual Event ',t, ''))
        log('\n\n%s Manual Event \n\n' % round(t,2))
        if DEVICE_ON:
            ne = NullEventThread()
        Frame.Graph.addPoint(cheese['trialRunTime'],31)
        X.feta.redraw_flag = True
        
    def OnSetFocus(self, event):
        self.color = '#0099f7'
        self.Refresh()

    def OnKillFocus(self, event):
        self.color = '#b3b3b3'
        self.Refresh()
    
    def updateValves(self,i):
        global openValves
        del openValves[:]
        openValves.extend(X.intervalList[i].tastes)
        for t in range(0,8):
            if t in openValves:
                self.valveButtons[t].SetValue(True)
            else:
                self.valveButtons[t].SetValue(False)

class OpenTwoDialog(wx.Dialog):
    def __init__(self, parent, ID, title="Load Two Experiments", size=wx.DefaultSize, pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        pre = wx.PreDialog()
        pre.Create(parent, ID, title, pos, (200,150), style)
        self.PostCreate(pre)
        tbl = Table.RowColSizer()
        desc = 'You may load two experiment setting files at once and switch between the trials.'
        tbl.Add(wx.StaticText(self, -1, desc), row=1, col=1, colspan=2)
        
        b1 = wx.Button(self, 101, "Load Experiment 1")
        tbl.Add(b1, row=3, col=1)
        self.t1 = wx.StaticText(self,-1,"")
        tbl.Add(self.t1, row=3, col=2)
        
        b2 = wx.Button(self, 102, "Load Experiment 2")
        tbl.Add(b2, row=5, col=1)
        self.t2 = wx.StaticText(self,-1,"")
        tbl.Add(self.t2, row=5, col=2)
        
        tbl.AddSpacer(400, 10, row=6, col=1, colspan=2)    
        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(wx.Button(self, wx.ID_OK))
        btnsizer.AddButton(wx.Button(self, wx.ID_CANCEL))
        btnsizer.Realize()
        
        self.Bind(wx.EVT_BUTTON, self.onLoadExps, b1)
        self.Bind(wx.EVT_BUTTON, self.onLoadExps, b2)
        self.Bind(wx.EVT_BUTTON, self.onSubmit, id=wx.ID_OK)
        
        tbl.Add(btnsizer, row=7, col=1, colspan=2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        
        self.SetSizer(tbl)
        tbl.Fit(self)
        
    def onSubmit(self,event):
        self.Close()
    
    def onLoadExps(self,evt):
        obj = evt.GetEventObject()
        id = obj.GetId()
        opener = wx.FileDialog(self, message="Choose a file", defaultDir=os.getcwd(), defaultFile="",wildcard=Frame.wildcard, style=wx.OPEN | wx.CHANGE_DIR)
        if opener.ShowModal()==wx.ID_OK:
            filename = opener.GetPath()
            if id==101:
                 self.t1.SetLabel(filename)
            else:
                self.t2.SetLabel(filename)
        opener.Destroy()
        

class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(1000, 600))
        grid = wx.GridSizer(1, 2, 10, 10)
        self.CtrlPanel = MainPanel(self)
        self.Graph = GraphPanel(self,self.CtrlPanel)
        self.CtrlPanel.setSibling(self.Graph)
        grid.AddMany([(self.CtrlPanel, 1, wx.TOP|wx.LEFT,9), (self.Graph, 1, wx.TOP|wx.RIGHT, 9)])
        self.SetSizer(grid)
        
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        openi = fileMenu.Append(wx.NewId(),"&Open")
        savei = fileMenu.Append(wx.NewId(),"&Save")
        open2 = fileMenu.Append(wx.NewId(),"Open Two")
        menuBar.Append(fileMenu,"&File")
        exeMenu = wx.Menu()
        starti = exeMenu.Append(wx.NewId(),"Start")
        stopi = exeMenu.Append(wx.NewId(),"Stop")
        menuBar.Append(exeMenu,"Run")
        graphMenu = wx.Menu()
        graphi = graphMenu.Append(wx.NewId(),"Refresh")
        graphs = graphMenu.Append(wx.NewId(),"Save")
        menuBar.Append(graphMenu,"Graph")
        self.SetMenuBar(menuBar)
        
        self.Bind(wx.EVT_MENU, self.OnStart, starti)
        self.Bind(wx.EVT_MENU, self.OnStop, stopi)
        self.Bind(wx.EVT_MENU, self.doSaveExp, savei)
        self.Bind(wx.EVT_MENU, self.doLoadExp, openi)
        self.Bind(wx.EVT_MENU, self.doLoadTwo, open2)
        self.Bind(wx.EVT_MENU, self.doRefreshGraph, graphi)
        self.Bind(wx.EVT_MENU, self.doSaveGraph, graphs)
        
        self.wildcard = "Extended Markup Language (*.xml)|*.xml| All files (*.*)|*.*"
        cheese['defaultDir'] = os.getcwd()
        
        self.Centre()
        self.Show(True)
    
    def OnStop(self, event):
        if X.feta==None:
            print "feta is null"
            return
        X.feta.stop()

    def OnStart(self, event):
        if len(openValves) == 0:
            log("Error: no valve selected.\n")
            return
        if cheese['restartAct']==None:
            log( "Unable to find restart action. \n")
            return
        self.Graph.clearGraph()
        if cheese['totalRunTime']>0:
            cheese['t0'] = time.clock()
            cheese['startTime'] = time.clock()
            cheese['rewardAt'] = 0.0
            cheese['toneAt'] = 0.0
        X.feta = MainThread()
        X.feta.start()

    def doRefreshGraph(self,event):
        self.Graph.initGraph()
    
    def doSaveGraph(self,event):
        wc = "*.gif|*.png| All files (*.*)|*.*"
        filer = wx.FileDialog(self, message="Save file as ...", defaultDir=os.getcwd() + '/saves', defaultFile="", wildcard=wc, style=wx.SAVE)
        if filer.ShowModal() == wx.ID_OK:
            dest_dir = filer.GetDirectory()
            src_dir = os.getcwd()
            filename = filer.GetFilename()
            Frame.Graph.saveGraph(filename)
            shutil.move(src_dir+'/'+filename, dest_dir+'/'+filename)
        filer.Destroy()
        
    def doSaveExp(self,evt):
        namer = wx.TextEntryDialog(self, 'Give your experiment a descriptive Name', 'Experiment name', 'TestExp')
        if namer.ShowModal()==wx.ID_OK:
            X.name = namer.GetValue()
        filename = re.sub('[^A-Za-z0-9]+', '', X.name)
        namer.Destroy()
        filer = wx.FileDialog(self, message="Save file as ...", defaultDir=os.getcwd()+'/saves',defaultFile=filename, wildcard=self.wildcard, style=wx.SAVE)
        if filer.ShowModal() == wx.ID_OK:
            filepath = filer.GetPath()
            saveExperiment(filepath,X)
        filer.Destroy()
    
    def updateFields(self):
        self.CtrlPanel.initStuff()
        self.CtrlPanel.wExperimentDur.SetValue(str(X.trialDuration))
        self.Graph.initGraph()
        
    def doLoadExp(self,evt):
        global derby
        opener = wx.FileDialog(self, message="Choose a file", defaultDir=os.getcwd(), defaultFile="",wildcard=self.wildcard, style=wx.OPEN | wx.CHANGE_DIR)
        if opener.ShowModal()==wx.ID_OK:
             filename = opener.GetPath()
             #openExp(filename)
             global X 
             X = loadExperiment(filename)
             bindExp()
             self.updateFields()
             derby = 0
             X.feta = None
             X.bleu = None
        opener.Destroy()

    def doLoadTwo(self,evt):
        l2 = OpenTwoDialog(self,-1)
        l2.ShowModal()
        l2.Destroy()
        
def bindExp():
    X.feta = None
    X.bleu = None
    
    def act_restart():
        global derby
        for i in X.intervalList:
            i.completed = False
        cheese['startTime'] = time.clock()
        derby = 0
        cheese['newTrial'] = True
        cheese['timeOffset'] = 0.0
    
    def act_autotaste(self):
        X.feta.redraw_flag = True
        X.bleu = DeliveryThread(1,0,self.runTime,1,self.valve)
        Frame.Graph.addPoint(cheese['trialRunTime'], X.bleu.valve)
        if X.autoRinse:
            time.sleep(self.runTime)
            X.bleu = DeliveryThread(1,0,X.rinseTime,1,0)
        cheese['numRewards'] += 1
        Frame.CtrlPanel.wNumRewards.SetLabel(str(cheese['numRewards']))
        cheese['timeStamps'].append( ('Taste Delivery ',cheese['totalRunTime'], 'Valve %d'%cheese['selValve']) )
        log('\n\n%s Taste \n\n' % round(cheese['totalRunTime'],2))
        cheese['rewartAt'] = cheese['totalRunTime']
        
    def act_mantaste(self):
        X.feta.redraw_flag = True
        nP = Frame.CtrlPanel.numberPulses
        pI = Frame.CtrlPanel.pulseInterval
        rD = Frame.CtrlPanel.pulseDuration / 1000.0
        X.bleu = DeliveryThread(nP, pI, rD,1,self.valve)
        Frame.Graph.addPoint(cheese['trialRunTime'], X.bleu.valve+8)
        if X.autoRinse:
            time.sleep(rD)
            X.bleu = DeliveryThread(1,0,X.rinseTime,1,0)
        cheese['numTaste']+=1
        Frame.CtrlPanel.wManTaste.SetLabel(str(cheese['numTaste']))
        cheese['timeStamps'].append( ('Taste Delivery ',cheese['totalRunTime'],'Valve %d'%cheese['selValve']) )
        log('\n\n%s Taste \n\n' % round(cheese['totalRunTime'],2))
        cheese['rewartAt'] = cheese['totalRunTime']
    
    def act_jump(self):
        for i in X.intervalList[self.jumpTo:]:
            i.completed = False
        cheese['timeOffset'] =  X.intervalList[self.jumpTo].startTime - cheese['trialRunTime']
    
    def act_cid(self):
        if self.mode==0:
            X.intervalList[self.interval].duration+=self.increment
        else:
            X.intervalList[self.interval].duration*=self.increment
    
    for a in X.actionList:
        if isinstance(a, Actions.Restart):
            a.bindAction(act_restart)
            cheese['restartAct'] = a
        elif isinstance(a, Actions.Taste):
            if a.isManual:
                a.bindAction(functools.partial(act_mantaste,self=a))
            else:
                a.bindAction(functools.partial(act_autotaste,self=a))
        elif isinstance(a, Actions.Jump):
            a.bindAction(functools.partial(act_jump,self=a))
        elif isinstance(a, Actions.ChangeIntDur):
            a.bindAction(functools.partial(act_cid,self=a))
        else:
            continue

def log(str):
    Frame.CtrlPanel.logger.AppendText(str)

def writeToFile():
    currDir = cheese['defaultDir']
    dirs = currDir.split('\\')
    dirs.pop()
    currDir = '\\'.join(dirs)
    directory = currDir+'\\Time Stamps\\'
    timeStamp = datetime.now().strftime("%Y.%B.%d, %H.%M.%S")
    fileName = directory + timeStamp + '.txt'
    f = open(fileName, 'w')
    temp = cheese['timeStamps']
    for i in range( len(temp) ):
        tempString = str(temp[i][1])+ '\t' + str(temp[i][0]) + '\t' +temp[i][2] +'\n'
        f.write(tempString)
    f.close()
    #directory = currDir+'\\ExpParams\\'
    fileName = directory + timeStamp+ '_info' + '.txt'
    f = open(fileName,'w')
    f.write("Trial Duration = \t"+str(X.trialDuration)+"\n\n")
    for i in X.intervalList:
        f.write(i.name+" = \t"+str(i.duration))
    f.write("Rewarded Lever Presses = \t"+str(cheese['numRewards'])+"\n")
    f.close()
    log("Writing to File Completed.\n")
    cheese['timeStamps'] = []

frameName = "NI-DAQ "
if DEVICE_ON:
    frameName += dev.get_product_type()     
filename = 'ClassicExp.xml'
if len(argv)==2:
    script,filename = argv
print filename
X = loadExperiment(filename)
app = wx.App(False)  # Create a new app, don't redirect stdout/stderr to a window.     
Frame = MyFrame(None, -1, frameName)
bindExp()
app.MainLoop()