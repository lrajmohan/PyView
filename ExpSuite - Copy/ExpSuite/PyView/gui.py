import wx
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import _load_bitmap
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import pylab
import  wx.lib.rcsizer  as Table
import  wx.lib.scrolledpanel as scrolled

from framework import *
import uservars as uv

X = None
lastTrialDuration = 0
from threading import Thread
import threading


graphStartTimes = []

class ScatterBrain(object):
    """Scatter plot properties"""
    def __init__(self,name,c='#000000',m='o',f=True):
        self.name = name
        self.x = []
        self.y = []
        self.color = c
        self.marker=m
        self.filled = f
        
    def setStyle(self,color,marker,filled=True):
        """ Set series color, marker, and if it is filled"""
        self.color = color
        self.marker = marker
        self.filled = filled
    
    def addPoint(self, x,y):
        """ add point to scatter plot series"""
        self.x.append(x)
        self.y.append(y)
    
    def getPlot(self,axes):
        """ draw scatter plot based on this properties"""
        fc = 'none'
        if self.filled:
            fc = self.color
        zindex = 10
        if self.name=='Lever':
            zindex = 1
        elif self.name=='Mark':
            zindex = 20
        return axes.scatter(self.x,self.y,c=self.color,marker=self.marker,
                            facecolors=fc, edgecolors=self.color, zorder=zindex)

class GraphPanel(wx.Panel):
    """Graph panel draws the runtime graph"""


    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        self.SetBackgroundColour('#FFFFFF')
        self.SetSizeWH(500,600)
        self.initGraph()

        wx.EVT_PAINT(self, self.OnPaint)
        self.redraw_bars = False
        self.brother = None

    def drawSpans(self,FirstLoad=False):
        """ draws interval spans"""
        global lastTrialDuration
        global  newWaitDuration
        startAt = self.trial-0.5
        h= 1.0

        if self.trial==1:
           startAt=0
           h=1.5
        drawX = 0.0

        del graphStartTimes[:]
        for i in X.intervalList:
            graphStartTimes.append(drawX)
            color = uv.iColors[i.type]
            if isinstance(i, Intervals.ToneInt):
                color = uv.freq2color(i.freq)
                self.axes.bar(drawX, h, 
                              color=color,zorder=0,lw=0.0, width=i.duration, bottom=startAt,)
            else:

                self.axes.bar(drawX, h, 
                              color=color,zorder=0,lw=0.0, width=i.duration, bottom=startAt,)

            drawX+=i.duration #raj-changed the value from i.maxDuration to i.duration to make the graph change dynamically based on lever press


                    
    def initGraph(self):
        """ initalize graph to draw spans """

        self.trial = 1
        self.sbs = {}
        self.sbs['Lever'] = ScatterBrain('Lever','#3399FF','o')
        self.sbs['Mark'] = ScatterBrain('Mark','#000000','x')
        for i in range(0,5):
            name = 'aTaste%d'%i
            self.sbs[name] = ScatterBrain(name,uv.TasteColors[i],'s')
            name2 = 'mTaste%d'%i
            self.sbs[name2] = ScatterBrain(name2,uv.TasteColors[i],'s',False)
        
        self.figure = Figure(dpi=100,figsize=(5,5.5))
        self.axes = self.figure.add_subplot(111)
        self.axes.axis([0,X.trialDuration,0,1.5])
        self.axes.set_xlabel('time (s)')
        
        self.drawSpans(True)
        
        LText = FontProperties()
        LText.set_size("small")
        
        
        self.axes.legend((self.sbs['Lever'].getPlot(self.axes),self.sbs['Mark'].getPlot(self.axes),
                          self.sbs['aTaste1'].getPlot(self.axes),self.sbs['mTaste1'].getPlot(self.axes)),
                         ("Lever Press","Time Marked", "Reward Given","Manual Reward"),
                         prop=LText, fancybox=True, bbox_to_anchor=(0., 1.02, 1., .102), loc=1, ncol=2, mode="expand", borderaxespad=0)
        
        self.canvas = FigureCanvas(self, -1, self.figure)
    
    def clearGraph(self):
        """ clear graph"""
        self.figure.delaxes(self.axes)
        self.initGraph()
        self.Refresh()
    
    def addPoint(self,i,t,pcat):
        """ add point to a scatter plot
        Args:
            i (int): index of intervals
            t (float): time to point to
            pcat (int): which scatter plot to add point to
        """
        ti = t
        if i!=-1:
            ti+= graphStartTimes[i]
        if pcat<8:
            self.sbs['aTaste%d'%pcat].addPoint(ti,self.trial)
        elif pcat<16:
            self.sbs['mTaste%d'%(pcat-8)].addPoint(ti,self.trial)
        elif pcat==30:
            self.sbs['Lever'].addPoint(ti,self.trial)
        elif pcat==31:
            self.sbs['Mark'].addPoint(ti,self.trial)
    
    def shiftPoints(self, offset):
        """ Move points """
        lvlen = len(self.sbs['Lever'].x)
        r = range(0,lvlen)
        r.reverse()
        for i in r:
            if self.sbs['Lever'].y[i]==self.trial:
                self.sbs['Lever'].x[i]-= offset
            else:
                break
    
    def newTrial(self):
        """ prepare graph for new trial"""
        self.trial+=1
        self.axes.set_ylim(top=(self.trial+0.5))
        self.redraw_bars = True
        
    def OnPaint(self, event):
        """ Redraw """
        """
        if self.redraw_bars:
            self.redraw_bars = False
            self.drawSpans()
        for k,v in self.sbs.items():
            v.getPlot(self.axes)
            del v.x[:]
            del v.y[:]
        self.canvas.draw() """
        d = DrawThread(self)
        d.start()
        event.Skip()

    def OnSetFocus(self, event):
        self.color = 'yellow'
        self.Refresh()

    def OnKillFocus(self, event):
        self.color = '#b3b3b3'
        self.Refresh()
    
    def saveGraph(self,filename="graph.png"):
        """Save graph as file"""
        self.figure.savefig(filename)

class DrawThread(Thread):
    def __init__(self,graph):
        Thread.__init__(self)
        self.g = graph
    
    def run(self):
        if self.g.redraw_bars:
            self.g.redraw_bars = False
            self.g.drawSpans()
        for k,v in self.g.sbs.items():
            v.getPlot(self.g.axes)
            del v.x[:]
            del v.y[:]
        self.g.canvas.draw()

class MainPanel(wx.Panel):
    """Control panel"""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.quote = wx.StaticText(self,label="Classic Experiment",pos=(200, 6),style=wx.ALIGN_CENTER) #raj-center
        self.Centre()
        self.SetSizeWH(400,600)
        ss = Table.RowColSizer()
        self.sister = None
        self.numberPulses = 1
        self.pulseInterval = 0
        self.pulseDuration = 100
        self.doMA = []

        ss.Add(wx.StaticText(self,label="Open Valves"),row=2,col=1,rowspan=2,colspan=1)
        buttonGroup = wx.GridSizer(2,4,0,0)

        self.valveButtons = []

        for i in range(0,5):
            self.valveButtons.append(wx.ToggleButton(self, i+1, uv.TasteNames[i]))
            self.valveButtons[i].Enable(False)
            buttonGroup.Add(self.valveButtons[i],0,wx.EXPAND)
        
        ss.Add(buttonGroup, row=2, col=2, rowspan=3, colspan=3)

        start_button = wx.Button(self,label="START", size=(-1,33))
        start_button.SetBackgroundColour("#00FF00")
        self.Bind(wx.EVT_BUTTON, self.Parent.OnStart, start_button)
        ss.Add(start_button, row=1, col=1, colspan=2, flag=wx.EXPAND)
        
        stop_button = wx.Button(self,label="STOP", size=(-1,33))
        stop_button.SetBackgroundColour("#FF0000")
        self.Bind(wx.EVT_BUTTON, self.Parent.OnStop, stop_button)
        ss.Add(stop_button, row=1, col=3, colspan=2, flag=wx.EXPAND)
        
        rExperimentDur = wx.StaticText(self, label="Trial Duration (s): ")
        self.wExperimentDur = wx.TextCtrl(self, value=str(X.trialDuration), size=(35,-1))
        self.Bind(wx.EVT_TEXT, self.evtExperimentDur, self.wExperimentDur)
        ss.Add(rExperimentDur, row=4, col=1)
        ss.Add(self.wExperimentDur, row=4, col=2)
        
        rPulseDuration = wx.StaticText(self, label="Pulse Duration (ms): ")
        self.wPulseDuration = wx.TextCtrl(self, value=str(self.pulseDuration), size=(40,-1))
        self.wPulseDuration.Enable(False)
        self.Bind(wx.EVT_TEXT, self.evtPulseDuration, self.wPulseDuration)
        ss.Add(rPulseDuration,row=4, col=3)
        ss.Add(self.wPulseDuration,row=4,col=4)
        
        self.pseudoLever = wx.Button(self,label="Lever Press")
        self.Bind(wx.EVT_BUTTON, self.Parent.OnPseudoLeverPress, self.pseudoLever)
        ss.Add(self.pseudoLever, row=5,col=3)
        
        self.markButton = wx.Button(self,label="Mark Time")
        self.Bind(wx.EVT_BUTTON, self.Parent.OnMarkTime, self.markButton)
        ss.Add(self.markButton, row=5, col=2)
     
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
    
    def txtListener(self,event):
        """ respond changes to intervals duration text field"""
        obj = event.GetEventObject()
        objId = obj.GetId()
        try:
            X.intervalList[objId].duration = float(event.GetString())
            X.intervalList[objId].oriDur = X.intervalList[objId].duration
            if not(X.intervalList[objId].changable):
                X.intervalList[objId].maxDuration = X.intervalList[objId].duration
        except ValueError:
            pass
        X.adjustPostIntTimes(objId)
    

    def updateValves(self,i):
        """update valve buttons"""
        for t in range(0,5):
            if t==i:
                self.valveButtons[t].SetValue(True)
            else:
                self.valveButtons[t].SetValue(False)

    
    def varyDurBy(self,event):
        """ update interval vary by"""
        obj = event.GetEventObject()
        objId = obj.GetId()
        try:
            X.intervalList[objId].varyBy = float(event.GetString())
        except ValueError:
            pass

    def varyDur(self,event):
        """ set if vary interval duration is true"""
        obj = event.GetEventObject()
        objId = obj.GetId()
        if event.IsChecked():
           # X.intervalList[objId].varyDuration()
            #X.adjustPostIntTimes(objId)
            X.intervalList[objId].vary = True
        else:
            #X.intervalList[objId].duration = X.intervalList[objId].oriDur
            #X.adjustPostIntTimes(objId);
            X.intervalList[objId].vary = False
        self.iFields[objId].SetValue(str(X.intervalList[objId].duration))
    
    def abClick(self,event):
        """ Buttons for manual actions"""
        obj = event.GetEventObject()
        objId = obj.GetId()
        X.actionList[objId].ready = True
        X.swiss.doMA.append(X.actionList[objId])
        
    def initStuff(self):
        """ Initialize components based on experiments"""
        self.wExperimentDur.SetValue(str(X.trialDuration))
        #self.quote.SetLabel('This is an experimentThis is an experimentThis is an experimen') #raj- label diplayed in the GUI
        self.quote.SetLabel(X.name) #raj- label diplayed in the GUI
        #self.Layout()
        print 'name::',X.name
        xsizer = wx.BoxSizer(wx.VERTICAL)
        if self.xPanel.intervalGroup!=None:
            self.xPanel.intervalGroup.Clear(True)
            self.xPanel.actionGroup.Clear(True)
            self.iFields = len(X.intervalList)*[None]
        self.xPanel.intervalGroup = wx.GridSizer(10,4,0,0)
        self.xPanel.actionGroup = wx.GridSizer(3,4,0,0)

        i = 0
        for itt in X.intervalList:
            desc = wx.StaticText(self.xPanel,label=(itt.name+" (s): "))
            self.iFields[i] = wx.TextCtrl(self.xPanel, value=str(itt.duration), size=(35,-1), id=i)
            vary = wx.CheckBox(self.xPanel, i, "vary by")
            if itt.vary:
                vary.SetValue(True)
                self.iFields[i].SetValue(str(itt.duration))
            varyBy = wx.TextCtrl(self.xPanel,value=str(itt.varyBy), size=(30,-1), id=i)
            self.iFields[i].Bind(wx.EVT_TEXT,self.txtListener)
            vary.Bind(wx.EVT_CHECKBOX, self.varyDur)
            varyBy.Bind(wx.EVT_TEXT, self.varyDurBy)
            self.xPanel.intervalGroup.AddMany([desc,self.iFields[i],vary, varyBy])
            i+=1
    
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
    
    def unbindAndDisable(self):
        for tf in self.iFields:
            tf.Enable(False)
            tf.Unbind(wx.EVT_TEXT)
        
    def evtPulseDuration(self, event):
        """ Update pulse duration"""
        try:
            self.pulseDuration = int(event.GetString())/1000
        except ValueError:
            pass
        
    def evtExperimentDur(self, event):
        """ update trial duration """
        try:
            X.trialDuration = float(event.GetString())
        except ValueError:
            pass
        
    def OnSetFocus(self, event):
        self.color = '#0099f7'
        self.Refresh()

    def OnKillFocus(self, event):
        self.color = '#b3b3b3'
        self.Refresh()
