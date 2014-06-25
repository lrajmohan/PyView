from framework import *
import neuroconnect as neu
import gui

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
import uservars as uv

#Global Variables

derby = 0
count = 0 #raj- to hold the number of trials in the Graph
timeStamps = []

counter = {'autoRewards':0,'manualRewards':0,'consecRewards':0, 'lvpress':0}
flag = {'tonePlayed': False, 'giveManualReward': False, 'giveAutoReward':False, 'pseudoPress':False,
        'newTrial':False,'correctRun':False, 'sjTrigger':False, 'ignoreLever':False, 'freezeDerby':False}
timer = {'total':0.0, 'durStart':0.0, 'durLapse':0.0, 'toneAt':0.0, 't0':0.0, 'start':0.0, 'iEnds':0.0}
item = {'jukebox':None}
Frame = None
filename = ''
toneThread = None

class MainThread(Thread):
    """ Main thread running while experiment is running
    """
    def __init__(self):
        Thread.__init__(self)
        self.stop_flag = False
        self.redraw_flag = False
        self.leverPressed = False


        self.dispExpPastTime = 0.00
        self.dispTonePastTime = 0.00
        self.doMA = []

    def pressedLever(self):
        """ Respond to lever press"""
        global timeStamps
        timeStamps.append( ('Lever Press',time.clock(),'') )
        log('%s Lever Pressed\n' % round(timer['total'],2))
        counter['lvpress']+=1
        timex = timer['durLapse']
        if derby==-1:
            timex+=timer['iEnds']
        Frame.Graph.addPoint(derby,timex,30)
        self.redraw_flag = True

    def pulseDelivered(self,stat):
        """ Respond to pulse delivered"""
        global timeStamps
        timeStamps.append(('Pulse'+stat,time.clock(), ''))
        log('%s Pulse %s \n' % (round(timer['total'],2),stat))

    def updateTimes(self):
        """ Updates time at end of the loop"""
        global timer
        T = time.clock()
        timer['total'] = T - timer['t0']
        timer['durLapse'] = T - timer['durStart']

        et = round(timer['total'],1)
        if et!=self.dispExpPastTime:
            self.dispExpPastTime = et
            Frame.CtrlPanel.wExperimentTime.SetLabel(str(self.dispExpPastTime))
        if flag['tonePlayed']:
            tft = round(timer['total']-timer['toneAt'],1)
            if tft!=self.dispTonePastTime:
                self.dispTonePastTime = tft
                Frame.CtrlPanel.wTimeTone.SetLabel( str(self.dispTonePastTime) )
    def updateIntPt(self):
        """ check to see if pointer to interval index needs to be updated"""
        global derby
        if derby==-1:
            return
        ival = X.intervalList[derby]
        if timer['durLapse'] > (ival.duration):
            ival.completed = True
            self.doEndAction()
            if not(flag['freezeDerby']):
                derby+=1
                if derby>=len(X.intervalList):
                    timer['iEnds'] = ival.startTime + timer['durLapse']
                    print "\t intervals ended at=%f"%timer['iEnds']
                    derby = -1
                    return
            else:
                flag['freezeDerby'] = False
            #passed interval boundaries
            starti = "\n%s >>> %s (%s Interval) ENTERED \n"%(timer['total'], X.intervalList[derby].name,X.intervalList[derby].type)
            log(starti)
            timer['durStart'] = time.clock()
            timer['durLapse'] = 0.0
            self.doBeginAction()
        else:
        	if flag['freezeDerby']:
        		starti = "\n%s >>> %s (%s Interval) ENTERED \n"%(timer['total'], X.intervalList[derby].name,X.intervalList[derby].type)
        		log(starti)
        		flag['freezeDerby'] = False


    def doEndAction(self):
        """ perform End action"""
        if derby==-1:
            return
        elif X.intervalList[derby].actions['End']==None:
            return
        if isinstance(X.intervalList[derby], Intervals.NogoInt):
            if X.intervalList[derby].ready:
                X.intervalList[derby].actions['End'].perform(X.intervalList[derby].startTime+timer['durLapse'])
        else:
            X.intervalList[derby].actions['End'].perform(X.intervalList[derby].startTime+timer['durLapse'])

    def doBeginAction(self):
        """ perform Begin action"""
        if derby==-1:
            return
        if isinstance(X.intervalList[derby], Intervals.ToneInt):
            item['jukebox'].freq = X.intervalList[derby].freq
        elif isinstance(X.intervalList[derby], Intervals.NogoInt):
            X.intervalList[derby].ready = True
        if X.intervalList[derby].actions['Begin']!=None and not(flag['newTrial']):
            X.intervalList[derby].actions['Begin'].perform(X.intervalList[derby].startTime+timer['durLapse'])

    def run(self):
        global derby
        global newMaxDuration#raj-change- new variable to store the max duration
        global newRefreshDuration #raj - starting trial value used when new trial is started using refresh
        global count
        derby = 0
        neu.main_init()
        #raj- experiment starts here
        flag['newTrial'] = True
        self.updateTimes()
        self.updateIntPt()
        log('\nExperiment Begins .. Trial Duration: %s seconds\n' % X.trialDuration)
        while not(self.stop_flag):
            if flag['newTrial']:
                count+=1 #raj-change- counting number of trials
                #print 'Number of Trials are:',count
                if Frame.Graph.trial ==1: #raj-change- getting the max value from the first trial
                      newMaxDuration = X.intervalList[0].maxDuration  #raj-change- getting the max value from the first trial
                      newRefreshDuration = X.intervalList[0].duration #raj - change
                starti = "\n%s >>> %s (%s Interval) ENTERED \n"%(timer['total'], X.intervalList[derby].name,X.intervalList[derby].type)
                log(starti)
                #print "new trial at %f \n"%time.clock()
                flag['newTrial'] = False
                self.doBeginAction()

            #detect lever presses
            self.leverPressed = False
            self.leverPressed = neu.main_lvpress()
            if flag['pseudoPress']:
                self.leverPressed = True
                #self.leverPressed = neu.fake_lvpress(True)
                flag['pseudoPress'] = False
            if flag['ignoreLever']:
                self.leverPressed = False

            # detect pulse
            # detect pulse
            '''
            pv = neu.main_pulse()
            if pv==1:
                self.pulseDelivered('starts')
            elif pv==-1:
                self.pulseDelivered('ends')
            '''

            #actions depedent on intervals
            if self.leverPressed:
                self.pressedLever()
                neu.main_automark()
                if derby!=-1:
                    if isinstance(X.intervalList[derby], Intervals.NogoInt):
                        X.intervalList[derby].ready = False
            else:
                pass

            #action on lever press (most often auto reward)
            if derby!=-1:
                if X.intervalList[derby].actions['Lever']!=None and self.leverPressed:
                    flag['ignoreLever'] = True
                    X.intervalList[derby].actions['Lever'].perform(X.intervalList[derby].startTime+timer['durLapse'])
                    #X.intervalList[derby].actions['Lever'].perform(timer['trial'])
                    flag['ignoreLever'] = False

            #send manual reward
            #mwStart = time.clock()
            if len(self.doMA)>0:
                for a in self.doMA:
                    a.perform(X.intervalList[derby].startTime+timer['durLapse'])
                    a.ready = False
                del self.doMA[:]
                self.flagMA = False
            #for a in X.actionList:
            #    if a.isManual and a.ready:
            #        a.perform(X.intervalList[derby].startTime+timer['durLapse'])
            #        a.ready = False
            #mwDone = time.clock()
            #mwDiff = mwDone-mwStart
            #if mwDiff>0.001:
            #    print "manual event check time=%f"%(mwDiff)

            if self.redraw_flag:
                #drawStart = time.clock()
                Frame.Graph.Refresh()
                self.redraw_flag = False
                #drawDone = time.clock()
                #print "draw time=%f"%(drawDone-drawStart)

            self.updateTimes()
            self.updateIntPt()

            #auto restart
            trialTime = timer['durLapse']
            if derby!=-1:
                trialTime+=X.intervalList[derby].startTime
            else:
                trialTime+=timer['iEnds']
            #raj-change starts here - making the jump when it reaches the end of the tone
            if derby!=-1:
                perTrialTotalTime =0 #raj
                lengthofIntervalListPerTrial = len(X.intervalList)
                for i in range(0,lengthofIntervalListPerTrial):
                    perTrialTotalTime += X.intervalList[i].duration
            #if (trialTime)>X.trialDuration: #Before changing
            if (trialTime)>perTrialTotalTime:
              #  print timer
              #  print 'intervalList',X.intervalList
              #  print 'iEnds',timer['iEnds'] #raj
              #  print 'trial time', trialTime#raj
              #  print 'trial duration',X.trialDuration#raj
              #  print 'toataltime',perTrialTotalTime
                startNewTrial()
            #raj-change ends here- making the jump when it reaches the end of the tone
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
        #neu.stopTone()


class MainFrame(wx.Frame):
    """ main frame for program"""
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
        """ manually stops experiment """
        if X.swiss==None:
            return
        X.swiss.stop()
    def OnStart(self, event):
        """ start experiment """
        if X.swiss!=None:
            if X.swiss.isAlive():
                return
        self.Graph.clearGraph()
        if timer['total']>0:
            timer['t0'] = time.clock()
            timer['start'] = time.clock()
            timer['durStart'] = time.clock()
            timer['durLapse'] = 0.0
            timer['toneAt'] =  0.0
            counter['consecRewards'] =0
            counter['lvpress'] =0
            self.OnResetCounter(None)
        flag['newTrial'] = True
        self.initWrite()
        self.CtrlPanel.unbindAndDisable()
        X.swiss = MainThread()
        self.starti.Enable(False)
        X.swiss.start()

    def OnDeviceToggle(self,event):
        """ Flag if device is on/off """
        if neu.DEVICE_ON:
            self.device.SetItemLabel('Turn Device On')
            neu.DEVICE_ON = False
        else:
            self.device.SetItemLabel('Turn Device Off')
            neu.DEVICE_ON = True

    def doRefreshGraph(self,event):
        """ refresh graph"""
        X.intervalList[0].duration =newRefreshDuration #raj- added this to make the trial start appropriately
        self.Graph.initGraph()

    def doSaveGraph(self,event):
        """ save graph """
        wc = "Portable Network Graphic (*.png) | *.png"
        filer = wx.FileDialog(self, message="Save file as ...", defaultDir=os.getcwd() + '/saves', defaultFile="", wildcard=wc, style=wx.SAVE)
        if filer.ShowModal() == wx.ID_OK:
            dest_dir = filer.GetDirectory()
            src_dir = os.getcwd()
            filename = filer.GetFilename()
            Frame.Graph.saveGraph(filename)
            shutil.move(src_dir+'/'+filename, dest_dir+'/'+filename)
        filer.Destroy()

    def doSaveExp(self,evt):
        """ save experiment paradigm """
        namer = wx.TextEntryDialog(self, 'Give your experiment a short description here', 'Experiment Description', 'TestExp')
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
        """ Updated on experiment load"""
        self.CtrlPanel.initStuff()
        self.Graph.initGraph()

    def OnPseudoLeverPress(self,event):
        """ manually button lever press"""
        flag['pseudoPress'] = True

    def OnResetCounter(self,evt):
        self.CtrlPanel.wNumRewards.SetLabel("0")
        counter['autoRewards']=0
        self.CtrlPanel.wManTaste.SetLabel("0")
        counter['manualRewards']=0

    def OnMarkTime(self,event):
        """ respond to mark time button"""
        global timeStamps
        t = time.clock() - timer['t0']
        timeStamps.append(('Mark Time',time.clock(), ''))
        log('%s Mark Time \n' % round(t,2))
        if neu.DEVICE_ON:
            ne = neu.NullEventThread()
        timex = timer['durLapse']
        if derby==-1:
            timex+=timer['iEnds']
        Frame.Graph.addPoint(derby,timex,31)
        X.swiss.redraw_flag = True

    def doLoadExp(self,evt):
        """ load experiment from XML file """
        global derby
        #global loadedfilename
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

    def initWrite(self):
        """ write info file"""
        currDir = self.defaultDir
        dirs = currDir.split('\\')
        dirs.pop()
        currDir = '\\'.join(dirs)
        self.saveDir = currDir+'\\Events\\'
        self.saveName = datetime.now().strftime("%Y.%B.%d, %H.%M.%S")
        self.infoFilename = self.saveDir + self.saveName +'_info.txt'
        f = open(self.infoFilename,'w')
        f.write("EXPERIMENT DESCRIPTION : "+X.name+"\n")
        f.write("EXPERIMENT FILE : "+X.loadedfilename+" \n") #raj-change - changed to the file which is loaded
        f.write("Trial Duration = \t"+str(X.trialDuration)+"\n")
        if X.autoRinse:
            f.write("Auto Rinse On. Lag = %f s, Delivery Time = %f s \n\n"%(X.rinseTime, X.rinseWait))
        f.write("Intervals Sequence\n")
        for i in X.intervalList:
            extra = ""
            if isinstance(i, Intervals.ToneInt):
                extra = "\t"+str(i.freq)+" Hz "
            f.write(i.name+" = \t"+str(i.duration)+extra+" \n")
        f.write("\nActions Detail \n")
        for a in X.actionList:
            if isinstance(a, Actions.Taste):
                f.write("%s Delivery Time = %f s \n"%(a.name,a.runTime))
        f.close()

    def writeToFile(self):
        """ write events, log, and graph"""
        global timeStamps

        fileName = self.saveDir + self.saveName + '_events.txt'
        f = open(fileName, 'w')
        for i in range( len(timeStamps) ):
            ttlcode = 'xxxxxxxx'
            try:
                ttlcode = uv.ttlMap[timeStamps[i][0]]
            except KeyError:
                if timeStamps[i][0] in ('Taste Delivery','Tone Delivery'):
                    try:
                        ttlcode = uv.ttlMap[timeStamps[i][2]]
                    except KeyError:
                        pass
            tx = timeStamps[i][1] - timer['t0']
            tempString = str(tx)+ '\t' +ttlcode + '\t % ' + str(timeStamps[i][0]) + '\t' +timeStamps[i][2] +'\n'
            f.write(tempString)
        f.close()

        f = open(self.infoFilename, 'a')
        f.write("\nExperiment Run Summary \n")
        f.write("Total experiment runtime = "+str(timer['total'])+"\n")
        f.write("Trials = "+str(self.Graph.trial)+"\n")
        f.write("Number of Lever Presses = "+str(counter['lvpress'])+"\n")
        f.write("Rewards = "+str(counter['autoRewards'])+"\n")
        f.write("Manual Rewards = "+str(counter['manualRewards'])+"\n")
        f.close()

        self.runnerFilename = self.saveDir + self.saveName +'_log.txt'
        f = open(self.runnerFilename,'w')
        f.write(Frame.CtrlPanel.logger.GetValue())
        f.close()

        graphfile = self.saveDir + self.saveName +'_graph.png'
        Frame.Graph.saveGraph(graphfile)

        log("Writing to File Completed.\n")
        del timeStamps [:]

    def printExtData(self, evt):
        """ Print experiment information"""
        X.printExpData()

def startNewTrial(startAt=0):
    """ New trial function"""
    global derby, toneThread

    if toneThread!=None:
        if toneThread.is_alive():
            toneThread.stop()

    inum = 0
    for i in X.intervalList:
        #if i.changable:
        #    continue
        if i.vary:
            i.varyDuration()
            X.adjustPostIntTimes(inum)
        #elif not(i.changable) and i.duration != i.oriDur:
        #    i.duration = i.oriDur
        #    X.adjustPostIntTimes(inum)
        Frame.CtrlPanel.iFields[inum].SetValue(str(i.duration))
        inum+=1
    if flag['correctRun']:
        counter['consecRewards'] +=1
    else:
        counter['consecRewards'] = 0
    flag['correctRun'] = False
    flag['tonePlayed'] = False
    Frame.CtrlPanel.wTimeTone.SetLabel('0.0')
    X.adjustPostIntTimes(0)
    Frame.Graph.newTrial()
    X.swiss.redraw_flag = True
    flag['newTrial'] = True

    nowt = time.clock()
    timer['start'] = nowt
    timer['durStart'] = nowt
    timer['durLapse'] = 0.0
    derby = startAt
    timeStamps.append( ('New Trial',nowt,''))
    log('- - Trial %d - - \n\n'%Frame.Graph.trial)
    if neu.DEVICE_ON:
        rse = neu.RestartEventThread()

def bindExp():
    """ Bind the act() function of actions to defined functions"""
    global item
    X.swiss = None
    """ MainThread"""

    def act_taste(self):
        global timeStamps
        valve = 0
        nov = len(self.valves)
        if nov == 0:
            log("\nError: no valve selected.\n")
            Frame.CtrlPanel.deliverButton.Enable()
            return
        elif nov==1:
            valve = self.valves[0]
        else:
            valve = random.choice(self.valves)
        Frame.CtrlPanel.updateValves(valve)
        nP = 1
        pI = 0
        rD = self.runTime
        # send taste
        candy = neu.GiveTasteThread(nP,pI,rD,valve)

        timeStamps.append( ('Taste Delivery',time.clock(),'Valve %d'%(valve+1)) )
        log('%s Taste \n' % round(timer['total'],2))

        if X.autoRinse:
            while candy.isAlive():
                time.sleep(0.01)
            time.sleep(X.rinseWait)
            water = neu.GiveTasteThread(1,0,X.rinseTime,0)
            timeStamps.append( ('Taste Delivery',time.clock(),'Valve %d'%(valve+1)) )

        # graph delivery & record txt
        if self.isManual:
            Frame.Graph.addPoint(derby,timer['durLapse'], valve+8)
            counter['manualRewards']+=1
            Frame.CtrlPanel.wManTaste.SetLabel(str(counter['manualRewards']))
        else:
            Frame.Graph.addPoint(derby,timer['durLapse'], valve)
            counter['autoRewards'] += 1
            Frame.CtrlPanel.wNumRewards.SetLabel(str(counter['autoRewards']))
            flag['correctRun'] = True
        X.swiss.redraw_flag = True

    def act_jump(self):
        global derby
        t = timer['total'] - timer['start']
        p = {'time':t,'trials':Frame.Graph.trial,
             'rewards':counter['autoRewards'],'cc':counter['consecRewards']}
        #print 'p in act_jump',p #raj
        yesJump = self.test(p)
        if not(yesJump):
            return
        r = random.random()
        jumpTo = self.selectIval(r)

        if self.newTrial:
            startNewTrial(jumpTo)
        else:
            timer['durStart'] = time.clock()
            timer['durLapse'] = 0.0
            derby = jumpTo
        X.swiss.redraw_flag = True
        flag['freezeDerby'] = True

    #here is where the increment operation is performed
    def act_cid(self):
        newdur = X.intervalList[self.interval].duration
        if self.mode==0 :
            newdur += self.increment
        else:
            newdur *= self.increment
       # print 'max duration ',X.intervalList[self.interval].maxDuration
        if Frame.Graph.trial >1: #raj-change- setting the max values for the following trials
           X.intervalList[self.interval].maxDuration = newMaxDuration  #raj-change #changing the max duration
        if newdur<=X.intervalList[self.interval].maxDuration and newdur>0:
        #print 'inside the redraw flag'
            X.intervalList[self.interval].duration = newdur
            X.adjustPostIntTimes(self.interval)
            Frame.Graph.redraw_bars = True
            X.swiss.redraw_flag = True
        #print "\t Increment by = %f \t NEW DURATION=%f \t Max Dur=%f"%(self.increment,newdur,X.intervalList[self.interval].maxDuration)
        #X.intervalList[self.interval].duration

    def act_play(self):
        global timeStamps, toneThread
        #send tone
        i = freq2int(self.freq)
        a = int2bi8(i)
        try:
            di = uv.ToneFreq.index(self.freq)
        except IndexError:
            di = 0
        toneThread = neu.PlayToneThread(X.intervalList[derby].duration,a,di)
        #log text
        timer['toneAt'] = time.clock() - timer['t0']
        flag['tonePlayed'] = True
        timeStamps.append( ('Tone Delivery',time.clock(),str(self.freq)+' Hz') )
        log('%s Tone \n'% round(timer['toneAt'],2) )
        self.performed = False


    # make tone player action and bind it to all tone intervals' begin-action
    item['jukebox'] = Actions.PlayTone('Jukebox')
    item['jukebox'].bindAction(functools.partial(act_play,self=item['jukebox']))
    for i in X.intervalList:
        if isinstance(i, Intervals.ToneInt):
            i.actions['Begin'] = item['jukebox']

    # bind actions to defined functions
    for a in X.actionList:
        if isinstance(a, Actions.Taste):
            a.bindAction(functools.partial(act_taste,self=a))
        elif isinstance(a, Actions.Jump):
            a.bindAction(functools.partial(act_jump,self=a))
        elif isinstance(a, Actions.ChangeIntDur):
            #raj - here is where the interval change function is called
            a.bindAction(functools.partial(act_cid,self=a))
        else:
            continue

def log(str):
    """ Add text to log"""
    Frame.CtrlPanel.logger.AppendText(str)

def init():
    """ initalize program"""
    global X, Frame, filename
    random.seed()
    currDir = os.getcwd()
    dpdir = currDir+'\default_paradigm'
    dlist = os.listdir(dpdir)
    if len(dlist)==1:
        filename = dpdir+ '\\' + dlist[0]
    else:
        print "There needs to be only one file in the 'default_paradigm' directory"
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
