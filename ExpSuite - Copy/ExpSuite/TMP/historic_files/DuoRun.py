import wx
import  wx.lib.rcsizer  as Table
import os
from threading import *
import time
import functools
from pulsar import *
import neuroconnect as neu
import CondTree as pine

neu.DEVICE_ON = False
if neu.DEVICE_ON:
    from libnidaqmx import System
    from libnidaqmx import Device
    from libnidaqmx import DigitalOutputTask
    from libnidaqmx import DigitalInputTask    

seq = DuoSequence()
runner = None
wildcard = "Extended Markup Language (*.xml)|*.xml| All files (*.*)|*.*"
timer = {'total':0.0, 'trial': 0.0, 'toneAt':0.0, 't0':0.0, 'start':0.0, 'offset':0.0 }
counter = {'autoRewards':0,'manualRewards':0,'consecRewards':0, 'trial':1}
flag = {'tonePlayed': False, 'giveManualReward': False, 'giveAutoReward':False, 'pseudoPress':False, 
        'newTrial':True,'correctRun':False}
pheonix = [None,None]
jukebox = None
derby = 0
activeX = 0
timeStamps = []
openValves = []

def bindActions(X,ax):
    global pheonix, jukebox
    def act_restart():
        global derby,activeX
        for i in seq.getExp(activeX).intervalList:
            i.completed = False
            i.duration = i.oriDur
        timer['start'] = time.clock()
        derby = 0
        flag['newTrial'] = True
        counter['trial']+=1 
        timeStamps.append( ('Completed Trial',timer['total'],''))
        X.adjustPostIntTimes(0)
        p = {'time':timer['total'],'trials':counter['trial'],
                     'rewards':counter['autoRewards'],'cc':counter['consecRewards']}
        toSwitch = seq.getLink(activeX).test(p)
        if toSwitch:
            activeX = int(not(activeX)) #switch from 1->0 or 0->1
            zwei.runshow.switch()
  

    def act_taste(self):
        valve = self.valve
        if len(openValves) == 0:
            return
        if valve==-1:
            valve = random.choice(openValves)
        nP = 1
        pI = 0
        rD = self.runTime
        ''' after we add these vars
        if self.isManual:
            nP = Frame.CtrlPanel.numberPulses
            pI = Frame.CtrlPanel.pulseInterval
            rD = Frame.CtrlPanel.pulseDuration / 1000.0
        '''
        # send taste
        neu.main_automark()
        neu.GiveTasteThread(nP,pI,rD,valve)    
        if X.autoRinse:
            #time.sleep(self.runTime)
            neu.GiveTasteThread(1,0,X.rinseTime,0)
        
        # graph delivery & record txt
        if self.isManual:    
            #Frame.Graph.addPoint(timer['trial'], valve+8)
            counter['manualRewards']+=1
            #Frame.CtrlPanel.wManTaste.SetLabel(str(counter['manualRewards']))
        else:
            #Frame.Graph.addPoint(timer['trial'], valve)
            counter['autoRewards'] += 1
            #Frame.CtrlPanel.wNumRewards.SetLabel(str(counter['autoRewards']))
            flag['correctRun'] = True

        timeStamps.append( ('Taste Delivery',timer['total'],'Valve %d'%valve) )
        print '%s Taste \n' % round(timer['total'],2)

    '''        
    def act_jump(self):

        for i in X.intervalList[self.jumpTo:]:
            i.completed = False
        timer['offset'] =  X.intervalList[self.jumpTo].startTime - timer['trial']

    
    def act_cid(self):

        if self.mode==0:
            X.intervalList[self.interval].duration+=self.increment
        else:
            X.intervalList[self.interval].duration*=self.increment
        X.adjustPostIntTimes(self.interval)
        gui.toneOffset = X.intervalList[gui.firstTone].startTime
        if gui.toneOffset>gui.maxTO:
            gui.maxTO = gui.toneOffset
        if X.timeSoFar()>X.trialDuration:
            X.trialDuration = X.timeSoFar()+1.0
        Frame.Graph.redraw_bars = True
        X.swiss.redraw_flag = True
    '''
    
    def act_play(self):
        global timeStamps
        i = freq2int(self.freq)
        a = int2bi8(i)
        neu.PlayToneThread(X.intervalList[derby].duration,a)
        timer['toneAt'] = time.clock()
        flag['tonePlayed'] = True
        timeStamps.append( ('Tone Delivery',timer['toneAt'],str(self.freq)+' Hz') )
        self.performed = False
    
    if jukebox==None:
        jukebox = Actions.PlayTone('Jukebox')
        jukebox.bindAction(functools.partial(act_play,self=jukebox))
        
    for i in X.intervalList:
        if isinstance(i, Intervals.ToneInt):
            i.actions['Begin'] = jukebox
    
    for a in X.actionList:
        if isinstance(a, Actions.Restart):
            a.bindAction(act_restart)
            if pheonix[ax]==None:
                pheonix[ax] = a
        elif isinstance(a, Actions.Taste):
            a.bindAction(functools.partial(act_taste,self=a))
        '''
        elif isinstance(a, Actions.Jump):
            a.bindAction(functools.partial(act_jump,self=a))
        elif isinstance(a, Actions.ChangeIntDur):
            a.bindAction(functools.partial(act_cid,self=a))
        '''
    if pheonix[ax]==None:
        pheonix[ax] = Actions.Restart("Restart")
        pheonix[ax].bindAction(act_restart)  


class MainThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.stop_flag = False
        self.lp = False #lever pressed
        self.start()
    
    def tick(self):
        global derby
        now = time.clock()
        timer['total'] = now - timer['t0']
        timer['trial'] = now - timer['start']
        
        if derby==-1:
            return
        X = seq.getExp(activeX)
        ival = X.intervalList[derby]
        if flag['newTrial']:
            print "\n Trial=%d"%counter['trial']
            self.doBeginAction()
        if timer['trial'] > (ival.startTime+ival.duration):
            ival.completed = True
            self.doEndAction()     
            derby+=1
            #passed interval boundaries
            if derby>=len(X.intervalList):
                derby = -1
                return
            else:
                print "%s at %f"%(X.intervalList[derby].name,timer['trial'])
                self.doBeginAction()
    
    def doEndAction(self):
        if derby==-1: 
            return
        ival = seq.getExp(activeX).intervalList[derby]
        if ival.actions['End']==None:
            return
        if isinstance(ival, Intervals.NogoInt):
            if ival.ready:
                ival.actions['End'].perform(timer['trial'])
        else:
            ival.actions['End'].perform(timer['trial'])    
    
    def doBeginAction(self):
        if derby==-1: 
            return
        ival = seq.getExp(activeX).intervalList[derby]
        if isinstance(ival, Intervals.ToneInt):
            jukebox.freq = ival.freq
            openValves = ival.tastes
        elif isinstance(ival, Intervals.NogoInt):
            ival.ready = True
        if ival.actions['Begin']!=None:
            ival.actions['Begin'].perform(timer['trial'])
    
    def onLeverPress(self):
        global timeStamps
        timeStamps.append( ('Lever Press',timer['total'],'') )
        print "Lever Pressed"
    
    def run(self):
        timer['t0'] = time.clock()
        timer['start'] = time.clock()
        self.tick()
        neu.main_init()
        while not(self.stop_flag):
            self.lp = False
            
            #detect lever press
            self.lp = neu.main_lvpress()
            if flag['pseudoPress']:
                self.lp = True
                flag['pseudoPress'] = False
            
            if self.lp:
                self.onLeverPress()
                lpact = seq.getExp(activeX).intervalList[derby].actions['Lever']
                if lpact!=None:
                    lpact.perform(timer['trial'])
                    
            if flag['newTrial']:
                flag['newTrial'] = False
  
            if timer['trial']>seq.getExp(activeX).trialDuration:
                pheonix[activeX].perform(timer['trial'])
        
            self.tick()
        #end of while loop
        neu.main_exit()
    
    def stop(self):
        self.stop_flag = True

class LoadPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        self.num = self.GetParent().num
        titleText = "Experiment "+str((self.num+1))
        title = wx.StaticText(self,-1,titleText)
        self.urlField = wx.TextCtrl(self,-1)
        self.urlField.SetEditable(False)
        loadButton = wx.Button(self,-1,"Load")
        editButton = wx.Button(self,-1,"Edit")
        
        self.Bind(wx.EVT_BUTTON, self.loadExperiment, loadButton)
        self.Bind(wx.EVT_BUTTON, self.editExperiment, editButton)
        
        grid = Table.RowColSizer()
        grid.SetMinSize((200,-1))
        grid.Add(title,row=1,col=1,colspan=2)
        grid.Add(self.urlField,row=2,col=1,colspan=2)
        grid.Add(loadButton,row=3,col=1)
        grid.Add(editButton,row=3,col=2)
        self.SetSizerAndFit(grid)
        
    def loadExperiment(self,evt):
        opener = wx.FileDialog(zwei.startshow, message="Choose a file", defaultDir=os.getcwd(), defaultFile="",
                               wildcard=wildcard, style=wx.OPEN | wx.CHANGE_DIR)
        if opener.ShowModal()==wx.ID_OK:
            filename = opener.GetPath()
            self.urlField.SetValue(filename)
            seq.setExp(self.num,filename)
        opener.Destroy()
        self.GetParent().updatePanelsOnLoad()

    def editExperiment(self,evt):
        pass

class VarPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        self.num = self.GetParent().num
        self.X = seq.getExp(self.num)
        rows = 1
        if self.X:
            rows = len(self.X.intervalsList)
        self.grid = wx.GridSizer(rows,4,0.5,0.5)
        self.grid.SetMinSize((200,300))
        
        self.SetSizerAndFit(self.grid)
    
    def loadvars(self):
        self.X = seq.getExp(self.num)
        if not(self.X):
            return
        
        rows = len(self.X.intervalList)
        self.grid.SetRows(rows)
        for i in range(0,rows):
            itt = self.X.intervalList[i]
            thname = wx.StaticText(self,label=itt.name)
            thdur = wx.TextCtrl(self,value=str(itt.duration), size=(35,-1))
            thvary = wx.CheckBox(self,-1, "vary by")
            thvaryby = wx.TextCtrl(self,value=str(itt.varyBy), size=(35,-1))
            self.grid.AddMany([(thname,0),(thdur,0),
                              (thvary,0),(thvaryby,0)]) 
        self.grid.Fit(self)

class SwitchPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        self.num = self.GetParent().num
        boxer = wx.BoxSizer(wx.VERTICAL)
        clist = [Conditions.BiasRandom(), Conditions.TimeLimit(), 
            Conditions.TrialsLimit(),Conditions.RewardsLimit(), 
            Conditions.ConRwLimit(), Conditions.Noty(), 
            Conditions.Ory(), Conditions.Andy(), Conditions.Xory()]
        self.copanel = pine.createTreePanel(self,clist)
        
        submitbtn = wx.Button(self,wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.onSubmit, id=wx.ID_OK)
        
        boxer.AddMany([self.copanel,submitbtn])
        self.SetSizerAndFit(boxer)
    
    def onSubmit(self,evt):
        xc = self.copanel.getMasterCondition()
        print xc.toString()
        seq.switchLink(self.num,xc)

class SeqPanel(wx.Panel):
    def __init__(self,parent,num):
        wx.Panel.__init__(self,parent, size=(250,600))
        self.num = num
        self.SetSizeWH(250,600)
        boxer = wx.BoxSizer(wx.VERTICAL)
        self.loadp = LoadPanel(self)
        self.varp = VarPanel(self)
        self.switchp = SwitchPanel(self)
        boxer.Add(self.loadp,0)
        boxer.Add(self.varp,0)
        boxer.Add(self.switchp,0)
        self.SetSizer(boxer,False)
    
    def updatePanelsOnLoad(self):
        self.varp.loadvars()

class CtrlPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,size=(1200,100))
        allSizer = wx.BoxSizer(wx.VERTICAL)
        allSizer.SetMinSize((1200,100))
        
        valveSizer = wx.BoxSizer(wx.HORIZONTAL)
        for i in range(0,8):
            vb = wx.ToggleButton(self,2000+i,"Valve "+str(i+1),size=(150,-1))
            vb.Bind(wx.EVT_TOGGLEBUTTON,self.onToggleValve)
            valveSizer.Add(vb,0,wx.EXPAND)
        valveSizer.Fit(self)
        
        self.exptime = wx.StaticText(self,-1,'0.0')
        self.timeFtone = wx.StaticText(self,-1,'0.0')
        self.pulsedur = wx.TextCtrl(self,-1,'0.0')
        markTimeButton = wx.Button(self,-1,"Mark Time")
        pressLeverButton = wx.Button(self,-1,"Press Lever")
        resetCountersButton = wx.Button(self,-1,"Reset Counter")
        stopButton = wx.Button(self,-1,'STOP')
        startButton = wx.Button(self,-1,'START')
        
        self.Bind(wx.EVT_BUTTON, self.onPressLever, pressLeverButton)
        self.Bind(wx.EVT_BUTTON, self.Parent.startRun, startButton)
        self.Bind(wx.EVT_BUTTON, self.Parent.stopRun, stopButton)
        
        txtSizer = wx.BoxSizer(wx.HORIZONTAL)
        txtSizer.AddMany([wx.StaticText(self,-1,'Experiment time (s): '),self.exptime])
        txtSizer.AddSpacer((50,10))
        txtSizer.AddMany([wx.StaticText(self,-1,'Time from tone (s): '),self.timeFtone])
        txtSizer.AddSpacer((50,10))
        txtSizer.AddMany([wx.StaticText(self,-1,'Pulse duration (ms): '),self.pulsedur])
        txtSizer.AddSpacer((50,10))
        txtSizer.AddMany([markTimeButton,pressLeverButton,resetCountersButton])
        txtSizer.AddSpacer((50,10))
        txtSizer.AddMany([startButton,stopButton])
        txtSizer.Fit(self)
        
        allSizer.Add(valveSizer)
        allSizer.AddSizer((1200,20))
        allSizer.Add(txtSizer)
        self.SetSizerAndFit(allSizer)

    def onToggleValve(self,evt):
        obj = evt.GetEventObject()
        id = obj.GetId()-2000
        print (id,obj.GetValue())
    
    def onPressLever(self,evt):
        flag['pseudoPress'] = True

class GraphPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        self.num = self.GetParent().num
        self.SetMinSize((600,300))
        self.SetBackgroundColour(wx.BLACK)

class ButtonsPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        self.num = self.GetParent().num
    
    def init(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        X = seq.getExp(self.num)
        for act in X.actionList:
            if act.isManual:
                actButton = wx.Button(self,-1, label=act.name)
                sizer.Add(actButton)
        self.SetSizerAndFit(sizer)
                

class RunSeqPanel(wx.Panel):
    def __init__(self,parent,num):
        wx.Panel.__init__(self,parent, size=(600,-1))
        self.num = num
        adidas = wx.BoxSizer(wx.VERTICAL)
        self.graph = GraphPanel(self)
        
        self.trialDur = wx.TextCtrl(self,-1,'0')
        self.rewardCount = wx.StaticText(self,-1,'0')
        self.manualCount = wx.StaticText(self,-1,'0')
        
        grid = wx.GridSizer(3,2,1,1)
        grid.AddMany([wx.StaticText(self,-1,'Trial Duration (s):'),self.trialDur])
        grid.AddMany([wx.StaticText(self,-1,'# Rewards:'),self.rewardCount])
        grid.AddMany([wx.StaticText(self,-1,'# Manual Tastes:'),self.manualCount])
        grid.Fit(self)
        
        self.mb = ButtonsPanel(self)
        
        adidas.AddMany([self.graph,grid,self.mb])
        self.SetSizerAndFit(adidas)
    
    def init(self):
        self.mb.init()
        
class StartFrame(wx.Frame):
    def __init__(self, parent, id, title="Initalize Sequences"):
        wx.Frame.__init__(self, parent, id, title, size=(500, 600))
        tbl = Table.RowColSizer()
        tbl.SetMinSize((500,600))
        self.SetBackgroundColour(wx.NullColor)
        self.panel0 = SeqPanel(self,0)
        self.panel1 = SeqPanel(self,1)
        runButton = wx.Button(self,-1,"RUN!")
        clearButton = wx.Button(self,-1,"Clear")
        saveButton = wx.Button(self,-1,"Save")
        saveAllButton = wx.Button(self,-1,"Save All")
        loadSeqButton = wx.Button(self,-1,"Load Sequence")
        
        self.Bind(wx.EVT_BUTTON, self.loadSeq, loadSeqButton)
        self.Bind(wx.EVT_BUTTON, self.runner, runButton)
        
        tbl.Add(self.panel0, row=1, col=1)
        tbl.Add(self.panel1, row=1, col=2)
        
        btngroup = wx.BoxSizer(wx.HORIZONTAL)
        btngroup.SetMinSize((500,50))
        btngroup.AddMany([clearButton, saveButton, saveAllButton,loadSeqButton])
        btngroup.AddStretchSpacer(1)
        btngroup.Add(runButton,0,wx.EXPAND)
        tbl.Add(btngroup, row=2, col=1, colspan=2)
        self.SetSizerAndFit(tbl)
        self.Show(True)
    
    def loadSeq(self,evt):
        global seq
        opener = wx.FileDialog(zwei.startshow, message="Choose a file", defaultDir=os.getcwd(), defaultFile="",
                               wildcard=wildcard, style=wx.OPEN | wx.CHANGE_DIR)
        if opener.ShowModal()==wx.ID_OK:
            filename = opener.GetPath()
            seq = loadDuoSequence(filename)
            #seq.printDuoSeq()
        opener.Destroy()
    
    def runner(self,evt):
        if seq.x0==None:
            ErrorPopup(self,'Experiment 1 is not loaded')
        elif seq.x1==None: 
            ErrorPopup(self,"Experiment 2 is not loaded")
        elif seq.l0==None: 
            ErrorPopup(self,"Experiment 1 is not switcher not defined")
        elif seq.l1==None: 
            ErrorPopup(self,"Experiment 2 is not switcher not defined")
        else:
            bindActions(seq.x0,0)
            bindActions(seq.x1,1)
            zwei.runshow.init()
            zwei.runshow.Show(True)
            zwei.runshow.startRun(None)

class RunFrame(wx.Frame):
    def __init__(self, parent, id, title="Run Sequences"):
        wx.Frame.__init__(self, parent, id, title, size=(1200, 600))
        tbl = Table.RowColSizer()
        tbl.SetMinSize((1200,600))
        self.SetBackgroundColour('#CCCEFA')
        self.ctrl = CtrlPanel(self)
        self.run0 = RunSeqPanel(self,0)
        self.run1 = RunSeqPanel(self,1)
        tbl.Add(self.ctrl,row=1,col=1,colspan=2)
        tbl.Add(self.run0,row=2,col=1)
        tbl.Add(self.run1,row=2,col=2)
        self.SetSizerAndFit(tbl)
        self.Show(False)
    
    def switch(self):
        if activeX==0:
            self.run0.mb.Enable(True)
            self.run1.mb.Enable(False)
        else:
            self.run1.mb.Enable(True)
            self.run0.mb.Enable(False)
    
    def init(self):
        self.run0.init()
        self.run1.init()
        self.run1.mb.Enable(False)
    
    def startRun(self,evt):
        global runner
        if runner!=None:
            if runner.isAlive():
                return
        runner = MainThread()

    def stopRun(self,evt):
        runner.stop()
        
class DuoRun(wx.App):
    def __init__(self, redirect=False, filename=None):
        wx.App.__init__(self, redirect, filename)
        self.startshow = StartFrame(None,-1)
        self.runshow = RunFrame(None,-1)

def ErrorPopup(frame,msg):
    dlg = wx.MessageDialog(frame, msg,'Error',wx.OK | wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()

zwei = DuoRun()
zwei.MainLoop()
