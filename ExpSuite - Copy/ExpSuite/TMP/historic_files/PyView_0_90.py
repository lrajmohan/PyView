from pulsar import *
import neuroconnect as neu
import gui

neu.DEVICE_ON = False
if neu.DEVICE_ON:
    from libnidaqmx import System
    from libnidaqmx import Device
    from libnidaqmx import DigitalOutputTask
    from libnidaqmx import DigitalInputTask    

from threading import Thread
import threading
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
import wx

#Global Variables

derby = 0

timeStamps = []

counter = {'autoRewards':0,'manualRewards':0,'consecRewards':0,'ptrials':1, 'prew':0, 'pcr': 0}
flag = {'tonePlayed': False, 'giveManualReward': False, 'giveAutoReward':False, 'pseudoPress':False, 
        'newTrial':False,'correctRun':False, 'sjTrigger':False, 'ignoreLever':False}
timer = {'total':0.0, 'trial': 0.0, 'durStart':0.0, 'durLapse':0.0, 'toneAt':0.0, 't0':0.0, 'start':0.0, 'offset':0.0,'pstart':0.0 }
item = {'pheonix':None, 'jukebox':None}
Frame = None
        
class MainThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.stop_flag = False
        self.redraw_flag = False
        self.leverPressed = False
        
        self.dispExpPastTime = 0.00
        self.dispTonePastTime = 0.00

    def pressedLever(self):
        global timeStamps
        timeStamps.append( ('Lever Press',timer['total'],'') )
        log('%s \n' % round(timer['total'],2))
        Frame.Graph.addPoint(timer['trial'],30)
        print "Lever Pressed at %f"%timer['trial']
        self.redraw_flag = True

    def updateTimes(self):
        timer['total'] = time.clock() - timer['t0']
        timer['trial'] = time.clock() - timer['start'] + timer['offset']
        timer['durLapse'] = time.clock() - timer['durStart']
        
        if round(timer['total'],2)!=self.dispExpPastTime:
            self.dispExpPastTime = round(timer['total'],2)
            Frame.CtrlPanel.wExperimentTime.SetLabel(str(self.dispExpPastTime))
        if flag['tonePlayed']:
            tft = round(timer['total']-timer['toneAt'],2)
            if tft!=self.dispTonePastTime:
                self.dispTonePastTime = tft
                Frame.CtrlPanel.wTimeTone.SetLabel( str(self.dispTonePastTime) )
        
        self.updateIntPt()

    def doEndAction(self):
        if derby==-1: 
            return
        elif X.intervalList[derby].actions['End']==None:
            return
        if isinstance(X.intervalList[derby], Intervals.NogoInt):
            if X.intervalList[derby].ready:
                X.intervalList[derby].actions['End'].perform(timer['trial'])
        else:
            X.intervalList[derby].actions['End'].perform(timer['trial'])    
    
    def doBeginAction(self):
        if derby==-1: 
            return
        if isinstance(X.intervalList[derby], Intervals.ToneInt):
            item['jukebox'].freq = X.intervalList[derby].freq
        elif isinstance(X.intervalList[derby], Intervals.NogoInt):
            X.intervalList[derby].ready = True
        if X.intervalList[derby].actions['Begin']!=None:
            X.intervalList[derby].actions['Begin'].perform(timer['trial'])

    def updateIntPt(self):
        global derby
        if derby==-1:
            return
        ival = X.intervalList[derby]
        if timer['trial'] > (ival.startTime+ival.duration):
            ival.completed = True
            self.doEndAction()
            print "%s interval complete \n"%ival.name     
            derby+=1
            #passed interval boundaries
            if derby>=len(X.intervalList):
                derby = -1
                return
            self.doBeginAction()

    def run(self):
        global derby
        derby = 0
        neu.main_init()
        flag['newTrial'] = True
        self.updateTimes()
        log('\nExperiment Begins .. Trial Duration: %s seconds\n' % X.trialDuration)
        while not(self.stop_flag):
            #if timer['trial']<timer['offset']:
            #    self.updateTimes()
            #    continue
            if flag['newTrial']:    
                if not(flag['sjTrigger']):
                    derby=0
                else:
                    flag['sjTrigger'] = False
                    print "offset=%f during run"%timer['offset']
                self.doBeginAction()
                counter['ptrials']+=1
                flag['newTrial'] = False
            #detect lever presses
            self.leverPressed = False
            self.leverPressed = neu.main_lvpress()
            if flag['pseudoPress']:
                self.leverPressed = True
                flag['pseudoPress'] = False
            if flag['ignoreLever']:
                self.leverPressed = False        
            
            #actions depedent on intervals     
            if derby==-1:
                pass
            elif self.leverPressed:
                self.pressedLever()
                neu.main_automark()
                if isinstance(X.intervalList[derby], Intervals.NogoInt):
                    X.intervalList[derby].ready = False
            else:
                pass
            
            #action on lever press (most often auto reward)
            if derby!=-1:
                if X.intervalList[derby].actions['Lever']!=None and self.leverPressed:
                    flag['ignoreLever'] = True
                    X.intervalList[derby].actions['Lever'].perform(timer['trial'])
                    flag['ignoreLever'] = False
            
            #send manual reward
            for a in X.actionList:
                if a.isManual and a.ready:
                    neu.main_automark()
                    a.perform(timer['trial'])
                    a.ready = False   
            
               
            if self.redraw_flag:
                Frame.Graph.Refresh()
                self.redraw_flag = False 
            
            self.updateTimes()
            
            #auto restart
            if timer['trial']>X.trialDuration:
                item['pheonix'].perform(timer['trial'])

            if X.terminator!=None and not(self.stop_flag):
                p = {'time':timer['total'],'trials':Frame.Graph.trial,
                     'rewards':counter['autoRewards'],'cc':counter['consecRewards']}
                self.stop_flag = X.terminator.test(p)
        #end of loop
        
        neu.main_exit()
        Frame.writeToFile()
        log('\nEnd of experiment.\n')
        Frame.starti.Enable()
                
    def stop(self):
        self.stop_flag = True



class MainFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(1000, 600))
        grid = wx.GridSizer(1, 2, 10, 10)
        gui.X = X
        self.CtrlPanel = gui.MainPanel(self)
        self.Graph = gui.GraphPanel(self)
        self.CtrlPanel.sister = self.Graph
        self.Graph.brother = self.CtrlPanel
        grid.AddMany([(self.CtrlPanel, 1, wx.TOP|wx.LEFT,9), (self.Graph, 1, wx.TOP|wx.RIGHT, 9)])
        self.SetSizer(grid)
        
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        openi = fileMenu.Append(wx.NewId(),"&Open")
        savei = fileMenu.Append(wx.NewId(),"&Save")
        printAll = fileMenu.Append(wx.NewId(),"Print Experiment Data")
        menuBar.Append(fileMenu,"&File")
        exeMenu = wx.Menu()
        self.starti = exeMenu.Append(wx.NewId(),"Start")
        self.stopi = exeMenu.Append(wx.NewId(),"Stop")
        tstr = "Turn Device "
        if neu.DEVICE_ON:
            tstr+='Off'
        else:
            tstr+='On'
        self.device = exeMenu.Append(wx.NewId(),tstr)
        menuBar.Append(exeMenu,"Run")
        graphMenu = wx.Menu()
        graphi = graphMenu.Append(wx.NewId(),"Refresh")
        graphs = graphMenu.Append(wx.NewId(),"Save")
        menuBar.Append(graphMenu,"Graph")
        self.SetMenuBar(menuBar)
        
        self.Bind(wx.EVT_MENU, self.OnStart, self.starti)
        self.Bind(wx.EVT_MENU, self.OnStop, self.stopi)
        self.Bind(wx.EVT_MENU, self.OnDeviceToggle, self.device)
        self.Bind(wx.EVT_MENU, self.doSaveExp, savei)
        self.Bind(wx.EVT_MENU, self.doLoadExp, openi)
        self.Bind(wx.EVT_MENU, self.doRefreshGraph, graphi)
        self.Bind(wx.EVT_MENU, self.doSaveGraph, graphs)
        self.Bind(wx.EVT_MENU, self.printExtData, printAll)
        
        self.wildcard = "Extended Markup Language (*.xml)|*.xml| All files (*.*)|*.*"
        self.defaultDir = os.getcwd()
        
        self.Centre()
        self.Show(True)
    
    def OnStop(self, event):
        if X.swiss==None:
            return
        X.swiss.stop()

    def OnStart(self, event):
        if len(gui.openValves) == 0:
            log("Error: no valve selected.\n")
            return
        if item['pheonix']==None:
            log( "Unable to find restart action. \n")
            return
        self.Graph.clearGraph()
        if timer['total']>0:
            timer['t0'] = time.clock()
            timer['pstart'] = time.clock()
            timer['start'] = time.clock()
            timer['toneAt'] = 0.0
            self.OnResetCounter(event)
        X.swiss = MainThread()
        self.starti.Enable(False)
        X.swiss.start()

    def OnDeviceToggle(self,event):
        if neu.DEVICE_ON:
            self.device.SetItemLabel('Turn Device On')
            neu.DEVICE_ON = False
        else:
            self.device.SetItemLabel('Turn Device Off')
            neu.DEVICE_ON = True
        
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
        self.Graph.initGraph()
    
    def OnPseudoLeverPress(self,event):
        flag['pseudoPress'] = True

    def OnResetCounter(self,evt):
        self.CtrlPanel.wNumRewards.SetLabel("0")
        counter['autoRewards']=0
        self.CtrlPanel.wManTaste.SetLabel("0")
        counter['manualRewards']=0
    
    def OnMarkTime(self,event):
        global timeStamps
        t = time.clock()
        timeStamps.append(('Manual Event ',t, ''))
        log('\n\n%s Manual Event \n\n' % round(t,2))
        if neu.DEVICE_ON:
            ne = NullEventThread()
        Frame.Graph.addPoint(timer['trial'],31)
        X.swiss.redraw_flag = True
        
    def doLoadExp(self,evt):
        global derby
        opener = wx.FileDialog(self, message="Choose a file", defaultDir=os.getcwd(), defaultFile="",wildcard=self.wildcard, style=wx.OPEN | wx.CHANGE_DIR)
        if opener.ShowModal()==wx.ID_OK:
             filename = opener.GetPath()
             global X 
             X = loadExperiment(filename)
             bindExp()
             gui.X = X
             self.updateFields()
        derby = 0
        opener.Destroy()
    
    def writeToFile(self):
        global timeStamps
        currDir = self.defaultDir
        dirs = currDir.split('\\')
        dirs.pop()
        currDir = '\\'.join(dirs)
        directory = currDir+'\\Time Stamps\\'
        timeStamp = datetime.now().strftime("%Y.%B.%d, %H.%M.%S")
        fileName = directory + timeStamp + '.txt'
        f = open(fileName, 'w')
        temp = timeStamps
        for i in range( len(temp) ):
            tempString = str(temp[i][1])+ '\t' + str(temp[i][0]) + '\t' +temp[i][2] +'\n'
            f.write(tempString)
        f.close()
        #directory = currDir+'\\ExpParams\\'
        fileName = directory + timeStamp+ '_info' + '.txt'
        f = open(fileName,'w')
        f.write("Trial Duration = \t"+str(X.trialDuration)+"\n\n")
        for i in X.intervalList:
            f.write(i.name+" = \t"+str(i.duration)+" \n")
        f.write("Rewarded Lever Presses = \t"+str(counter['autoRewards'])+"\n")
        f.close()
        log("Writing to File Completed.\n")
        timeStamps = []
    
    def printExtData(self, evt):
        X.printExpData()

def bindExp():
    global item
    #X.feta = None taste
    #X.bleu = None tone
    X.swiss = None #main
    
    def act_restart():
        global derby, timeStamps
        timer['start'] = time.clock()
        if not(flag['sjTrigger']):
            timer['offset'] = 0.0
            derby = 0
        timeStamps.append( ('Restart',timer['total'],''))
        
        for i in X.intervalList:
            i.completed = False
            if i.vary or i.changable:
                i.duration = i.oriDur
        if flag['correctRun']:
            counter['consecRewards'] +=1
            counter['pcr']+=1
        else:
            counter['consecRewards'] = 0
            counter['pcr']=0
        flag['correctRun'] = False
        flag['tonePlayed'] = False
        Frame.CtrlPanel.wTimeTone.SetLabel('0.0')
        gui.toneOffset = gui.oriTO
        X.adjustPostIntTimes(0)
        Frame.Graph.newTrial()
        X.swiss.redraw_flag = True
        flag['newTrial'] = True
        if neu.DEVICE_ON:
            rse = neu.RestartEventThread()
    
    def act_taste(self):
        global timeStamps
        valve = self.valve
        if len(gui.openValves) == 0:
            Frame.CtrlPanel.logger.AppendText("\nError: no valve selected.\n")
            Frame.CtrlPanel.deliverButton.Enable()
            return
        if valve==-1:
            valve = random.choice(gui.openValves)
        nP = 1
        pI = 0
        rD = self.runTime
        if self.isManual:
            nP = Frame.CtrlPanel.numberPulses
            pI = Frame.CtrlPanel.pulseInterval
            rD = Frame.CtrlPanel.pulseDuration / 1000.0
        # send taste
        neu.GiveTasteThread(nP,pI,rD,valve)    
        if X.autoRinse:
            #time.sleep(self.runTime)
            neu.GiveTasteThread(1,0,X.rinseTime,0)
        
        # graph delivery & record txt
        if self.isManual:    
            Frame.Graph.addPoint(timer['trial'], valve+8)
            counter['manualRewards']+=1
            Frame.CtrlPanel.wManTaste.SetLabel(str(counter['manualRewards']))
        else:
            Frame.Graph.addPoint(timer['trial'], valve)
            counter['autoRewards'] += 1
            counter['prew']+=1
            Frame.CtrlPanel.wNumRewards.SetLabel(str(counter['autoRewards']))
            flag['correctRun'] = True
        X.swiss.redraw_flag = True
        timeStamps.append( ('Taste Delivery',timer['total'],'Valve %d'%valve) )
        log('\n\n%s Taste \n\n' % round(timer['total'],2))
    
    def act_jump(self):
        for i in X.intervalList[self.jumpTo:]:
            i.completed = False
        timer['offset'] =  X.intervalList[self.jumpTo].startTime - timer['trial']
    
    def act_sj(self):
        global derby
        flag['sjTrigger'] = True
        si = self.current
        sl = self.switch[si]
        t = timer['total'] - timer['pstart']
        p = {'time':t,'trials':counter['ptrials'], 'rewards':counter['autoRewards'],'cc':counter['pcr']}
        print p
        jump = self.test(p)
        if jump:
            si = int(not(si))
            self.current = si
            sl = self.switch[si]
            timer['pstart'] = time.clock()
            counter['ptrials'] = 1
            counter['prew'] = 0
            counter['pcr'] = 0
        timer['offset'] = X.intervalList[sl].startTime - timer['trial']
        if timer['offset']<0:
            timer['offset'] = X.intervalList[sl].startTime
        derby = sl
        flag['tonePlayed'] = False
        act_restart()
        if jump:
            print "===Switch=== \n\n"
    
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
    
    def act_play(self):
        global timeStamps
        #send tone
        i = freq2int(self.freq)
        a = int2bi8(i)
        neu.PlayToneThread(X.intervalList[derby].duration,a)
        #log text
        timer['toneAt'] = time.clock()
        flag['tonePlayed'] = True
        timeStamps.append( ('Tone Delivery',timer['toneAt'],str(self.freq)+' Hz') )
        log('\n\n%s Tone \n\n'% round(timer['toneAt'],2) )
        Frame.CtrlPanel.updateValves(derby)
        self.performed = False

    
    item['jukebox'] = Actions.PlayTone('Jukebox')
    item['jukebox'].bindAction(functools.partial(act_play,self=item['jukebox']))
    
    for i in X.intervalList:
        if isinstance(i, Intervals.ToneInt):
            i.actions['Begin'] = item['jukebox']
    
    for a in X.actionList:
        if isinstance(a, Actions.Restart):
            a.bindAction(act_restart)
            item['pheonix'] = a
        elif isinstance(a, Actions.Taste):
            a.bindAction(functools.partial(act_taste,self=a))
        elif isinstance(a, Actions.Jump):
            a.bindAction(functools.partial(act_jump,self=a))
        elif isinstance(a, Actions.SwitchJump):
            a.bindAction(functools.partial(act_sj,self=a))
        elif isinstance(a, Actions.ChangeIntDur):
            a.bindAction(functools.partial(act_cid,self=a))
            gui.setTO = True
        else:
            continue
    if item['pheonix']==None:
        item['pheonix'] = Actions.Restart("Restart")

def log(str):
    Frame.CtrlPanel.logger.AppendText(str)

def init():
    global X, Frame
    random.seed()
    currDir = os.getcwd()
    dpdir = currDir+'\default_paradigm'
    dlist = os.listdir(dpdir)
    if len(dlist)==1:
        filename = dpdir+ '\\' + dlist[0]
    else:
        print "There needs to be one and only one file in the 'default_paradigm' directory"
    if len(argv)==2:
        script,filename = argv
    X = loadExperiment(filename)
    frameName = "NI-DAQ "
    if neu.DEVICE_ON:
        system = System()
        dev = system.devices[0]
        frameName += dev.get_product_type()    
    app = wx.App(False)  # Create a new app, don't redirect stdout/stderr to a window.     
    Frame = MainFrame(None, -1, frameName)
    bindExp()
    app.MainLoop()
    
init()
