import wx
from framework import *
import wx.lib.agw.rulerctrl as Ruler
import  wx.lib.rcsizer  as Table
import wx.lib.ogl as ogl
import  wx.lib.scrolledpanel as scrollp
import uservars as uv
import os
import re
import subprocess
import CondTree as pine
# global variables
X = Experiment()
X.trialDuration = 30
ToneCount = 0
choosenOnes = []
"""selected intervals and actions"""
palette = {} 
"""dictionary of Pens and Brushes"""
saveExp = False
"""if Save or Save As has been called since changes made"""
rootDir = os.getcwd()

class IntervalShape(ogl.CompositeShape):
    """Extends composite shape to represent an interval. Made up of 4 rectangle shapes
    One represents the interval span. 
    The other three represent tick marks for Begin/End/Lever linked actions
    """
    def __init__(self, canvas):
        ogl.CompositeShape.__init__(self)
        self.SetCanvas(canvas)
        self.selected = False
        self.rect = ogl.RectangleShape(0,0)
        self.leftMark = ogl.RectangleShape(1,3)
        self.centerMark = ogl.RectangleShape(1,3)
        self.rightMark = ogl.RectangleShape(1,3)
        
        self.AddChild(self.rect)
        self.AddChild(self.leftMark)
        self.AddChild(self.centerMark)
        self.AddChild(self.rightMark)
        
        self.rect.__dict__['OnLeftClick'] = self.OnLeftClick
        self.rect.__dict__['OnLeftDoubleClick'] = self.OnLeftDoubleClick
    
    def getTick(self,name):
        """ Returns Rectangle shape object for corresponding tick mark
        Args:
            name: ['Begin',End','Lever']
        """
        if name=='Begin':
            return self.leftMark
        elif name=='End':
            return self.rightMark
        else:
            return self.centerMark
        
    def setIndexSize(self, i, x, w):
        """Set position and size of IntervalShape
        Args:
            i (int): index of interval in list
            x (float): horizontal position of interval shape
            w (float): width of interval shape
        """
        self.index = i
        self.selected = False
        self.SetX(x)
        self.SetY(25)
        self.SetWidth(w)
        self.SetHeight(50)
        self.rect.SetX(x)
        self.rect.SetY(25)
        self.rect.SetWidth(w)
        self.rect.SetHeight(50)
        self.leftMark.SetX(x-(w/2))
        self.centerMark.SetX(x)
        self.rightMark.SetX(x+(w/2))
        self.leftMark.SetY(50)
        self.centerMark.SetY(50)
        self.rightMark.SetY(50)
        self.SetDraggable(False, True)
    
    
    def setColors(self,pen, brush):
        """Set color of interval"""
        for a in self.GetChildren():
            if a==self.rect:
                self.rect.SetBrush(brush)
                self.rect.SetPen(pen)
            else:
               a.SetPen(wx.BLACK_DASHED_PEN)
               a.SetBrush(wx.TRANSPARENT_BRUSH) 
    
    def OnLeftClick(self, x, y, keys=0, attachment=0):
        """Responds to single click on Shape
        Highlights Interval shape and adds corresponding interval to selection list
        if it is already selected, then we deselect this interval
        """
        E.panel.logger.SetValue(X.intervalList[self.index].toString())
        E.statusBar.SetStatusText("Double click to edit interval")
        if self.selected:
             self.deselect()
        else:
            self.select()
        self.GetCanvas().Refresh(True)
      
    def OnLeftDoubleClick(self, x, y, keys, attachment):
        """Responds to double click on Shape
        Opens edit dialog for corresponding interval
        """
        if isinstance(X.intervalList[self.index], Intervals.WaitInt):
            wv = DialogWait(E.panel, self.index)
        elif  isinstance(X.intervalList[self.index], Intervals.ToneInt):
            wv = DialogTone(E.panel, self.index)
        elif  isinstance(X.intervalList[self.index], Intervals.RewardInt):
            wv = DialogRewardInt(E.panel, self.index)
        elif  isinstance(X.intervalList[self.index], Intervals.NogoInt):
            wv = DialogNogo(E.panel, self.index)
        else:
            wv = None
        if wv != None:
            wv.ShowModal()
            wv.Destroy()
        X.adjustPostIntTimes(self.index)
        E.panel.adjustTd()
        E.timeline.adjustPostIntShapes(self.index,False)
    
    def select(self):
        """Select shape: adds corresponding interval to selection list"""
        self.rect.SetPen(palette['stroke'])
        choosenOnes.append(X.intervalList[self.index])
        self.selected = True
    
    def deselect(self):
        """deselect shape if already selected"""
        self.rect.SetPen(palette[X.intervalList[self.index].type+'_pen'])
        choosenOnes.remove(X.intervalList[self.index])
        self.selected = False

    def GetX(self):
        """get X of interval rectangle (center point in shape)"""
        return self.rect.GetX()
    
    def GetY(self):
        """get Y interval rectangle (center point in shape)"""
        return self.rect.GetY()
    
    def GetWidth(self):
        """get width of interval rectangle shape"""
        return self.rect.GetWidth()

    def GetHeight(self):
        """get height of interval rectangle shape"""
        return self.rect.GetHeight()
    
    def SetX(self,x):
        """ set X interval rectangle """
        ogl.CompositeShape.SetX(self,x)
        self.rect.SetX(x)
    
    def SetY(self,y):
        """ set Y interval rectangle """
        ogl.CompositeShape.SetY(self,y)
        self.rect.SetY(y)
     
    def SetWidth(self,w):
        """set width interval rectangle """
        ogl.CompositeShape.SetWidth(self,w)
        self.rect.SetWidth(w)
    
    def SetHeight(self,h):
        """set height interval rectangle """
        ogl.CompositeShape.SetHeight(self,h)
        self.rect.SetHeight(h)
        
    def updateMarks(self):
        """Update marks when interval startTime or duration changes"""
        x = self.GetX()
        w = self.GetWidth()
        self.leftMark.SetX(x-(w/2))
        self.centerMark.SetX(x)
        self.rightMark.SetX(x+(w/2))
        self.leftMark.SetY(50)
        self.centerMark.SetY(50)
        self.rightMark.SetY(50)

class ActionShape(ogl.CircleShape):
    """Extends Circle shape to represent Actions"""
    def __init__(self, r):
        ogl.CircleShape.__init__(self, r)
        self.moving = False
        """True if object is currently being dragged around. Used when placing object at initalization"""
        self.selected = False
    
    def setIndexColor(self, i):
        """link to the Action's index in the Experiment's actions list"""
        self.index = i
        self.AddText(X.actionList[i].name)
        self.SetDraggable(True)
    
    def startMoving(self):
        """set shape to moving"""
        self.moving = True
    
    def stopMoving(self):
        """set shape to not moving"""
        self.moving = False
    
    def OnLeftClick(self, x, y, keys=0, attachment=0):
        """Responds to single click: select/deselect action"""
        E.panel.logger.SetValue(X.actionList[self.index].toString())
        E.statusBar.SetStatusText("Double click to edit action")
        if self.selected:
             self.deselect()
        else:
            self.select()
        self.GetCanvas().Refresh(True)
    
    def OnLeftDoubleClick(self, x, y, keys, attachment):
        """Responds to double click: Opens edit dialog for Action"""
        if isinstance(X.actionList[self.index], Actions.Taste):
            wv = DialogTaste(E.panel, self.index)
        elif isinstance(X.actionList[self.index], Actions.Jump):
            wv = DialogJump(E.panel, self.index)
        elif isinstance(X.actionList[self.index], Actions.ChangeIntDur):
            wv = DialogChangeIntDur(E.panel, self.index)
        else:
            wv = None
        if wv != None:
            wv.ShowModal()
            wv.Destroy()

    def select(self):
        """ select action shape"""
        self.SetPen(palette['stroke'])
        choosenOnes.append(X.actionList[self.index])
        self.selected = True
    
    def deselect(self):
        """ deselect action shape"""
        self.SetPen(palette[X.actionList[self.index].type+'_pen'])
        choosenOnes.remove(X.actionList[self.index])
        self.selected = False

class Timeline(wx.Panel):
    """Extends Panel to visualize Experiment control flow"""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour('#FFFFFF')
        self.w = 800
        self.SetSizeWH(self.w, 200)
        
        # Create sizer
        box = wx.BoxSizer(wx.VERTICAL)
        box.SetMinSize((200, self.w))
        
        # Make ruler
        self.ruler = Ruler.RulerCtrl(self, -1, orient=wx.HORIZONTAL, style=wx.SUNKEN_BORDER)
        self.ruler.SetSize((self.w, 20))
        self.ruler.SetRange(0, X.trialDuration)
        
        # Make Open Graphics Library canvas
        self.canvas = ogl.ShapeCanvas(self)
        self.canvas.SetBackgroundColour("#ffffff")
        ogl.OGLInitialize()
        
        self.timeStep = self.w / X.trialDuration
        """Width of teach time unit"""
        self.ghost = None
        """Temp variable to host a moving ActionShape"""
        
        box.AddMany([(self.ruler, 0, wx.EXPAND), (self.canvas, 1, wx.EXPAND)])
        self.diagram = ogl.Diagram()
        self.canvas.SetDiagram(self.diagram)
        self.diagram.SetCanvas(self.canvas)      
        self.diagram.ShowAll(True)
        self.dc = wx.ClientDC(self.canvas)
        self.SetSizer(box)
        
        self.linesMap = {}
        """Dictonary of all the lines as defined by a tuple key 
        (startShape,endShape) and the value is a LineShape object"""
        self.bracts = 0
        """Used when opening experiments as a counter on how to place action items horizontally"""
        
        self.Fit()
        self.Show()
      
    def bindPlaceMouse(self):
        """Activate Mouse Move and Mouse Down listeners
        used when user is placing the ActionShape object 
        on the timeline for the first time """
        self.canvas.Bind(wx.EVT_MOTION, self.onMouseMove)
        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.onMouseDown)
    
    def unbindPlaceMouse(self):
        """Deactivate Mouse Move and Mouse Down listeners
        after ActionShape object has been placed
        """
        self.canvas.Unbind(wx.EVT_MOTION)
        self.canvas.Unbind(wx.EVT_LEFT_DOWN)
      
    def onMouseMove(self, evt):
        """ Move ActionShape with mouse 
        """
        if self.ghost == None:
            return
        self.ghost.SetX(evt.GetX())
        self.ghost.SetY(evt.GetY())
        self.canvas.Refresh(True)
    
    def onMouseDown(self, evt):
        """ Confirm ActionShape placement """
        if self.ghost:
            self.ghost.stopMoving()
            act = X.actionList[self.ghost.index]
            self.drawActionLinks(act)
            self.ghost = None
            self.unbindPlaceMouse()
        self.diagram.ShowAll(True)
        self.canvas.Refresh(True)
    
    def drawActionLinks(self,act):
        """ Make link"""
        if isinstance(act,Actions.Jump):
            for it in act.jumper:
                self.makeLink(act.icon,X.intervalList[it[0]].icon)
        elif isinstance(act, Actions.ChangeIntDur):
            self.makeLink(act.icon, X.intervalList[act.interval].icon)
        else:
            return
    
    def extendTrialDuration(self,called=False):
        """ Extend trial duration to max interval duration + 5 secs"""
        newdur = X.timeSoFar()+5
        E.panel.input_expDur.SetValue(str(newdur))
        if called:
            ErrorPopup("The total time of allocated intervals exceeds a trial duration. Trial durtion extended to %f"%newdur)
       
    def addInterval(self, i):
        """Make IntervalShape associated with new Interval
        Args:
            i (int): index of interval in the intervalList
        """
        itt = X.intervalList[i]
        iw = self.timeStep * itt.duration
        xat = itt.startTime * self.timeStep + (iw / 2)
        rect = IntervalShape(self.canvas)
        rect.setIndexSize(i, xat, iw)
        rect.setColors(palette[itt.type+'_pen'], palette[itt.type+'_brush'])
        if isinstance(itt, Intervals.ToneInt):
            rect.AddText("%d Hz" % itt.freq)
        itt.icon = rect
        self.diagram.AddShape(rect)
        self.diagram.ShowAll(True)
        self.canvas.Refresh(True)
        return rect
    
    def addAction(self, i, setpos):
        """Make ActionShape associated with new Action
        Args:
            i (int): index of action in the actionList
            setpos (bool): True/False on whether or not to active manual placing.
        """
        act = X.actionList[i]
        ces = ActionShape(49)
        ces.setIndexColor(i)
        ces.SetBrush(palette[act.type+'_brush'])
        ces.SetPen(palette[act.type+'_pen'])
        act.icon = ces
        self.diagram.AddShape(ces)
        self.diagram.ShowAll(True)
        self.canvas.Refresh(True)
        if setpos:
            ces.startMoving()
            self.ghost = ces
        return ces
    
    def adjustPostIntShapes(self, i, delete):
        """ Move intervals after i-th interval changed its duration
        Args:
            i (int): index in intervalList
            delete (bool): if i-th interval was deleted
        """
        dc = wx.ClientDC(self.canvas)
        for j in range(i, len(X.intervalList)):
            iw = self.timeStep * X.intervalList[j].duration
            xat = X.intervalList[j].startTime * self.timeStep + (iw / 2)
            X.intervalList[j].icon.SetX(xat)
            X.intervalList[j].icon.SetWidth(iw)
            X.intervalList[j].icon.updateMarks()
            for la in X.intervalList[j].actions.values():
                if la:
                    la.icon.SetX(xat)
            if delete:
                X.intervalList[j].icon.index-=1
        self.canvas.Refresh(True)
        self.redrawLinks()
    
    def redrawLinks(self):
        """Redraw links between shapes"""
        dc = wx.ClientDC(self.canvas)
        for a in X.actionList:
            a.icon.MoveLinks(dc)
        for i in X.intervalList:
            for k in i.actions.keys():
                i.icon.getTick(k).MoveLinks(dc)
    
    def updateExpDur(self, dur):
        """ Adjust the timeline
        Args:
            dur (float): trial duration
        """
        self.ruler.SetRange(0, dur)
        self.timeStep = self.w / dur
        self.adjustPostIntShapes(0,False)
    
    def makeLink(self, fromShape, toShape,flag=''):
        """Make link between two shapes
        Args:
            fromShape, toShape : arrow drawn from and to shape
            flag (str): is defined when the link drawn is as an Interval-Action
        """
        line = ogl.LineShape()
        line.SetCanvas(self.canvas)
        line.SetPen(wx.BLACK_PEN)
        line.SetBrush(wx.BLACK_BRUSH)
        line.AddArrow(ogl.ARROW_ARROW)
        line.MakeLineControlPoints(2)
        fromPlace = fromShape
        if flag=='Begin':
            fromPlace = fromShape.leftMark
        elif flag=='Lever':
            fromPlace = fromShape.centerMark
        elif flag=='End':
            fromPlace = fromShape.rightMark
        self.linesMap[(fromPlace,toShape)] = line
        fromPlace.AddLine(line, toShape)
        self.diagram.AddShape(line)
        line.Show(True)
        self.canvas.Refresh(True)
    
    # Remove link between two shapes
    #    (fromShape, toShape) = arrow drawn from and to shape
    def destroyLink(self,fromShape,toShape):
        """Remove link between two shapes
            (fromShape, toShape) = arrow drawn from and to shape
        """
        try:
            L = self.linesMap[(fromShape,toShape)]
            fromShape.RemoveLine(L)
            self.diagram.RemoveShape(L)
            del self.linesMap[(fromShape,toShape)]
        except KeyError:
            pass
        self.canvas.Refresh(True)

class CtrlPanel(wx.Panel):
    """ Top panel with buttons and log """
    def __init__(self, parent, tl):
        wx.Panel.__init__(self, parent)
        self.timeline = tl
        self.SetBackgroundColour('#E0EEEE')
        self.SetSizeWH(800, 400)
        self.currTime = 0.0
        ss = Table.RowColSizer()
        # Make items
        ss.Add(wx.StaticText(self, -1, "Trial Duration"), row=1, col=1)
        self.input_expDur = wx.TextCtrl(self, id=299, value=str(X.trialDuration), size=(40, -1))
        ss.Add(self.input_expDur, row=1, col=2)

        self.autoRinseFlag = wx.CheckBox(self,-1,"Auto Rinse")
        if X.autoRinse:
            self.autoRinseFlag.SetValue(True)
        
        self.autoRinseTime = wx.TextCtrl(self,-1)
        self.autoRinseTime.SetValue(str(X.rinseTime))

        self.autoRinseWait = wx.TextCtrl(self,-1)
        self.autoRinseWait.SetValue(str(X.rinseWait))
        
        rinseSet = wx.GridSizer(3,2,0,0)
        rinseSet.AddMany([self.autoRinseFlag, wx.StaticText(self,-1,"")])
        rinseSet.AddMany([wx.StaticText(self,-1,"Wait Time (s)"), self.autoRinseWait])
        rinseSet.AddMany([wx.StaticText(self,-1,"Rinse Time (s)"), self.autoRinseTime])
        
        ss.Add(rinseSet, row=2, col=1, colspan=2)
        
        self.logger = wx.TextCtrl(self, size=(300, 100), style=wx.TE_MULTILINE | wx.TE_READONLY) 
        ss.Add(self.logger, row=3, col=1, colspan=2, rowspan=4)
#raj- added frequency text control boxes at top right of the editor (changes starts)
        freqGrid1 = wx.GridSizer(2,2,0,0)
        self.freq1 = wx.TextCtrl(self, size=(40, -1))
        self.freq1.SetValue(str(uv.ToneFreq[0]))
        self.Bind(wx.EVT_TEXT,self.updateFreq1,self.freq1)
        self.freq2 = wx.TextCtrl(self, size=(40, -1))
        self.freq2.SetValue(str(uv.ToneFreq[1]))
        self.Bind(wx.EVT_TEXT,self.updateFreq2,self.freq2)
        freqGrid1.AddMany([wx.StaticText(self,-1,"FREQ.1"), self.freq1])
        freqGrid1.AddMany([wx.StaticText(self,-1,"FREQ.2"), self.freq2])
        ss.Add(freqGrid1,row=1, col=3)

        freqGrid2 = wx.GridSizer(2,2,0,0)
        self.freq3 = wx.TextCtrl(self, size=(40, -1))
        self.freq3.SetValue(str(uv.ToneFreq[2]))
        self.Bind(wx.EVT_TEXT,self.updateFreq3,self.freq3,'freq1')
        self.freq4 = wx.TextCtrl(self, size=(40, -1))
        self.freq4.SetValue(str(uv.ToneFreq[3]))
        self.Bind(wx.EVT_TEXT,self.updateFreq4,self.freq4)
        freqGrid2.AddMany([wx.StaticText(self,-1,"FREQ.3"), self.freq3])
        freqGrid2.AddMany([wx.StaticText(self,-1,"FREQ.4"), self.freq4])
        ss.Add(freqGrid2,row=1, col=4)
#raj- changes for freq text control  boxes ends (changes ends)
       # ss.Add(wx.StaticText(self, -1, "Freq1:"),row=1,col=3) #raj
       # self.freq1 = wx.TextCtrl(self, id=299, value=str(uv.ToneFreq[0]), size=(50, -1))
       # ss.Add(self.freq1, row=1, col=4,colspan=2)

        ss.AddSpacer(800, 100, row=1, col=3, colspan=4)
        ss.Add(wx.StaticText(self, -1, "ADD COMPONENTS:"), row=2, col=3) #raj-changed alignment from row-1 to row-2, &ALIGN_CENTER_HORIZONTAL to ALIGN_CENTER
        ss.AddSpacer(800, 10, row=2, col=1, colspan=4)
        ss.AddSpacer(400, 10, row=3, col=1, colspan=4)
        
        ss.Add(wx.StaticText(self, -1, "Intervals"), row=3, col=3)
        ss.Add(wx.StaticText(self, -1, "Actions"), row=3, col=4)
        iset = wx.GridSizer(3,2,0,0)
        aset = wx.GridSizer(3,2,0,0)
        btn_wait = wx.Button(self, id=300, label="Wait")
        btn_tone = wx.Button(self, id=301, label="Tone")
        btn_rint = wx.Button(self, id=302, label="Reward")
        btn_nogo = wx.Button(self, id=306, label="No Go")
        btn_taste = wx.Button(self, id=303, label="Taste")
        btn_jump = wx.Button(self, id=305, label="Jump")
        btn_cid = wx.Button(self, id=307, label="Change \n Interval \n Duration")
    
        btn_del = wx.Button(self, id=39, label="Delete")
        ss.Add(btn_del,row=7, col=2)
        
        iset.AddMany([btn_wait,btn_tone,btn_rint,btn_nogo])
        aset.AddMany([btn_taste,btn_jump,btn_cid])
        ss.Add(iset,row=4,col=3, rowspan=3)
        ss.Add(aset,row=4,col=4,rowspan=3)
        #Bind buttons
        self.Bind(wx.EVT_TEXT, self.updateExpDur, self.input_expDur)
        self.Bind(wx.EVT_BUTTON, self.openIntWaitDialog, btn_wait)
        self.Bind(wx.EVT_BUTTON, self.openIntToneDialog, btn_tone)
        self.Bind(wx.EVT_BUTTON, self.openIntRewardDialog, btn_rint)
        self.Bind(wx.EVT_BUTTON, self.openNogoDialog, btn_nogo)
        self.Bind(wx.EVT_BUTTON,self.openActTasteDialog,btn_taste)
        self.Bind(wx.EVT_BUTTON, self.openActJumpDialog, btn_jump)
        self.Bind(wx.EVT_BUTTON, self.deleteSelected, btn_del)
        self.Bind(wx.EVT_BUTTON, self.openActCid, btn_cid)
        self.Bind(wx.EVT_CHECKBOX, self.updateAutoRinse, self.autoRinseFlag)
        self.Bind(wx.EVT_TEXT, self.updateRinseTime, self.autoRinseTime)
        self.Bind(wx.EVT_TEXT, self.updateRinseWait, self.autoRinseWait)
        self.SetSizer(ss)
#raj- updatefreq function-  changes starts - to update the freq list based on the user inputs
    def updateFreq1(self,evt):
            try:
                d = int(self.freq1.GetValue())  #only numerical freq
                uv.ToneFreq[0]=d
                print 'tone freq1',uv.ToneFreq
                 #print "Please enter a numeric Freq."
                 #pass
            except ValueError:
                print "Please enter a numeric Freq." #prompts to enter a numerical freq
    def updateFreq2(self,evt):
            try:
                d = int(self.freq1.GetValue())
                uv.ToneFreq[0]=d
                print 'tone freq1',uv.ToneFreq
                 #print "Please enter a numeric Freq."
                 #pass
            except ValueError:
                print "Please enter a numeric Freq."
    def updateFreq3(self,evt):
            try:
                d = int(self.freq1.GetValue())
                uv.ToneFreq[0]=d
                print 'tone freq1',uv.ToneFreq
                 #print "Please enter a numeric Freq."
                 #pass
            except ValueError:
                print "Please enter a numeric Freq."
    def updateFreq4(self,evt):
            try:
                d = int(self.freq1.GetValue())
                uv.ToneFreq[0]=d
                print 'tone freq1',uv.ToneFreq
                 #print "Please enter a numeric Freq."
                 #pass
            except ValueError:
                print "Please enter a numeric Freq."

            '''if (self.freq4.GetValue()==''):
                 print "Please enter a numeric Freq."
                 pass
            else:
                d = int(self.freq4.GetValue())
                uv.ToneFreq[3]=d
                print 'tone freq4',uv.ToneFreq'''
#raj- change ends
    def deleteSelected(self,evt):
        """delete selected items"""
        if len(choosenOnes)==0:
            ErrorPopup('Select items to delete')
            return
        for obj in choosenOnes:
            if issubclass(obj.__class__, Intervals.Interval):
                ind = X.intervalList.index(obj)
                #adjust times after
                obj.duration = 0.0
                if ind!=(len(X.intervalList)-1):
                    X.adjustPostIntTimes(ind)
                    E.timeline.adjustPostIntShapes(ind,True)
                
                #delete action-interval links
                for k,v in obj.actions.items():
                    if v!=None:
                        mark = None
                        if k=='Begin':
                            mark = obj.icon.leftMark
                        elif k=='End':
                            mark = obj.icon.rightMark
                        else:
                            mark = obj.icon.centerMark
                        E.timeline.destroyLink(mark, v.icon)
                        obj.actions[k] = None
                #delete link from jump actions
                for act in X.actionList:
                    if isinstance(act,Actions.Jump):
                        jl = len(act.jumper)
                        for ati in range(0,jl):
                            if act.jumper[ati][0]==ind:
                                act.jumper.pop(ati)
                                E.timeline.destroyLink(act.icon, obj.icon)
                    else:
                        continue
                #delete shape
                obj.icon.Delete()
                #delete obj
                X.intervalList.remove(obj)
            elif issubclass(obj.__class__, Actions.Action):
                ind = X.actionList.index(obj)
                
                #delete action-interval links
                for i in X.intervalList:
                    for k,v in i.actions.items():
                        if v==obj:
                            mark = None
                            if k=='Begin':
                                mark = i.icon.leftMark
                            elif k=='End':
                                mark = i.icon.rightMark
                            else:
                                mark = i.icon.centerMark
                            E.timeline.destroyLink(mark, v.icon)
                            i.actions[k] = None
                
                #delete triggers
                ai = 0
                for a in X.actionList:
                    ati = -1
                    if ai>ind:
                        a.icon.index-=1
                        a.icon.ClearText()
                        a.icon.AddText(a.name)
                    ai+=1
                    try:
                        ati = a.triggerFor.index(obj)
                    except ValueError:
                        continue
                    E.timeline.destroyLink(a.icon, obj.icon)
                    a.triggerFor.pop(ati)
                
                #delete triggered by
                for t in obj.triggerFor:
                    E.timeline.destroyLink(obj.icon, t.icon)
                
                if isinstance(obj,Actions.Jump):
                    for i in obj.jumper:
                        if i[0]>=len(X.intervalList):
                            break
                        ival = X.intervalList[i[0]]
                        E.timeline.destroyLink(obj.icon, ival.icon)
                if isinstance(obj,Actions.ChangeIntDur):
                    E.timeline.destroyLink(obj.icon,X.intervalList[obj.interval].icon)
                    
                #delete shape
                E.timeline.diagram.RemoveShape(obj.icon)
                
                #delete obj
                X.actionList.remove(obj)
            else:
                pass
        E.timeline.canvas.Refresh(True)
        del choosenOnes[:]
    
    def adjustTd(self):
        """Adjust trial duration to equal the sum of all max interval duration"""
        self.input_expDur.SetValue(str(X.maxTimeSoFar()))
    
    def updateExpDur(self, evt):
        """Change interval duration when the text field is edited"""
        try:
            expDur = float(evt.GetString())
            X.trialDuration = expDur
            self.timeline.updateExpDur(expDur)
        except ValueError:
            pass
    
    def openIntWaitDialog(self, evt):
        """Open dialog for creating a Wait interval"""
        wv = DialogWait(self, -1)
        wv.ShowModal()
        wv.Destroy()
    
    def openIntToneDialog(self, evt):
        """Open dialog for creating a Tone interval"""
        wv = DialogTone(self, -1)
        wv.ShowModal()
        wv.Destroy()
        
    def openIntRewardDialog(self, evt):
        """Open dialog for creating a Reward interval"""
        wv = DialogRewardInt(self, -1)
        wv.ShowModal()
        wv.Destroy()
    
    def openNogoDialog(self, evt):
        """Open dialog for creating a No Go interval"""
        wv = DialogNogo(self, -1)
        wv.ShowModal()
        wv.Destroy()
    
    def openActTasteDialog(self,event):
        """Open dialog for creating a Taste action"""
        wv = DialogTaste(self,-1)
        wv.ShowModal()
        wv.Destroy()
    
    def openActJumpDialog(self,event):
        """Open dialog for creating a Jump action"""
        wv = DialogJump(self,-1)
        wv.ShowModal()
        wv.Destroy()
    
    def openActCid(self,event):
        """Open dialog for creating a Change Interval Duration action"""
        wv = DialogChangeIntDur(self,-1)
        wv.ShowModal()
        wv.Destroy()
    
    def updateAutoRinse(self,evt):
        """Toggle auto rinse activity"""
        if evt.IsChecked():
            X.autoRinse = True
        else:
            X.autoRinse = False
    
    def updateRinseWait(self, evt):
        """Change wait time before auto rinse"""
        try:
            X.rinseWait = float(evt.GetString())
        except ValueError:
            pass
    
    def updateRinseTime(self,evt):
        """Change auto rinse time"""
        try:
            X.rinseTime = float(evt.GetString())
        except ValueError:
            pass

class FormDialog(wx.Dialog):
    """Abstract FormDialog class"""
    def __init__(self, parent, ID, title, size=wx.DefaultSize, pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        global saveExp
        saveExp = False
        pre = wx.PreDialog()
        pre.Create(parent, ID, title, pos, (400,-1), style)
        self.PostCreate(pre)
        self.tbl = Table.RowColSizer()
        
        self.tbl.AddSpacer(400, 10, row=10, col=1, colspan=2)
            
        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(wx.Button(self, wx.ID_OK))
        btnsizer.AddButton(wx.Button(self, wx.ID_CANCEL))
        btnsizer.Realize()
        
        self.Bind(wx.EVT_BUTTON, self.onSubmit, id=wx.ID_OK)
        
        self.tbl.Add(btnsizer, row=12, col=1, colspan=2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        
        self.SetSizer(self.tbl)
        self.tbl.Fit(self)
        
    def onSubmit(self,event):
        self.Close()
    
    def nonZeroDuration(self):
        ErrorPopup('Please enter a non-zero positive number for duration')

class IntervalForm(FormDialog):
    """Abstract IntervalForm class"""
    def __init__(self, parent, ID, title):
        FormDialog.__init__(self,parent,ID, title)
        # if ID is manually defined, then it is to edit an interval
        self.act = None
        if ID >= 0 and ID < len(X.intervalList):
            self.act = X.intervalList[ID]
        
        self.tbl.Add(wx.StaticText(self, -1, "Name"), row=3, col=1)
        self.nameField = wx.TextCtrl(self)
        self.tbl.Add(self.nameField, row=3, col=2)
        self.tbl.Add(wx.StaticText(self, -1, "Duration (s)"), row=4, col=1)
        self.durField = wx.TextCtrl(self)
        self.tbl.Add(self.durField, row=4, col=2)

        self.varyCheck = wx.CheckBox(self, -1, "Vary by")
        self.varyField = wx.TextCtrl(self,-1, "0.0")
        self.varyField.Enable(False)
        
        self.tbl.Add(self.varyCheck, row=5, col=1)
        self.tbl.Add(self.varyField, row=5, col=2)
        
        self.mdCheck = wx.CheckBox(self,-1,"Set max duration")
        self.mdField = wx.TextCtrl(self,-1,"0.0")
        self.mdField.Enable(False)
        
        self.Bind(wx.EVT_TEXT,self.updateDur,self.durField)
        self.Bind(wx.EVT_CHECKBOX,self.toggleMd,self.mdCheck)
        self.Bind(wx.EVT_CHECKBOX, self.toggleVary, self.varyCheck)
        
        self.tbl.Add(self.mdCheck, row=6, col=1)
        self.tbl.Add(self.mdField, row=6, col=2)
        '''# raj
        self.tbl.Add(wx.StaticText(self, -1, "Duration (s)"), row=8, col=1)
        self.durField = wx.TextCtrl(self)
        self.tbl.Add(self.durField, row=4, col=2) #raj'''
        all = ["None"]
        for a in X.actionList:
            all.append(a.name)
        
        self.aB = wx.Choice(self,-1,choices=all)
        self.aL = wx.Choice(self,-1,choices=all)
        self.aE = wx.Choice(self,-1,choices=all)
        self.aB.Select(0)
        self.aL.Select(0)
        self.aE.Select(0)
        
        if self.act:
            if self.act.actions['Begin']:
                a = X.actionList.index(self.act.actions['Begin'])
                self.aB.Select(1+a)
            if self.act.actions['Lever']:
                a = X.actionList.index(self.act.actions['Lever'])
                self.aL.Select(1+a)
            if self.act.actions['End']:
                a = X.actionList.index(self.act.actions['End'])
                self.aE.Select(1+a)
            self.nameField.SetValue(self.act.name)
            self.durField.SetValue(str(self.act.duration))
            self.mdField.SetValue(str(self.act.maxDuration))
            if self.act.maxDuration!=self.act.duration:
                self.mdCheck.SetValue(True)
                self.mdField.Enable(True)
            if self.act.vary:
                self.varyCheck.SetValue(True)
                self.varyField.Enable(True)
                self.varyField.SetValue(str(self.act.varyBy))
        else:
            self.nameField.SetValue("Interval%d" % len(X.intervalList))
            self.durField.SetValue("0.0")
        
        desc = '''You may attach actions to an interval.'''
        self.tbl.Add(wx.StaticText(self, -1, desc), row=7, col=1, colspan=2)
        grid = wx.GridSizer(3,2,1,1)
        grid.AddMany([wx.StaticText(self,-1,label="At Begin interval: "),self.aB])
        grid.AddMany([wx.StaticText(self,-1,label="At Lever pressed: "),self.aL])
        grid.AddMany([wx.StaticText(self,-1,label="At End interval: "),self.aE])
        self.tbl.Add(grid, row=8, col=1, colspan=2,rowspan=2)
        
        if not(self.act):
            self.tbl.Hide(grid, True)
    
    def updateDur(self,evt):
        if not(self.mdCheck.IsChecked()):
            d = self.durField.GetValue()
            self.mdField.SetValue(d)
    
    def toggleMd(self,evt):
        if evt.IsChecked():
            self.mdField.Enable(True)
        else:
            self.mdField.Enable(False)
    
    def toggleVary(self,evt):
        if evt.IsChecked():
            self.varyField.Enable(True)
        else:
            self.varyField.Enable(False)
       
    def linkacts(self,evt):
        """update linked actions"""
        ab = self.aB.GetSelection()
        al = self.aL.GetSelection()
        ae = self.aE.GetSelection()
        alpha =self.act.icon
        y = alpha.GetY() + alpha.GetHeight()/2
        if ab!=0:
            self.act.actions['Begin'] = X.actionList[ab-1]
            E.timeline.makeLink(alpha,X.actionList[ab-1].icon, 'Begin')
        elif self.act.actions['Begin']!=None:
            E.timeline.destroyLink(alpha.getTick('Begin'),self.act.actions['Begin'].icon)
            self.act.actions['Begin'] = None
        if al!=0:
            self.act.actions['Lever'] = X.actionList[al-1]
            E.timeline.makeLink(alpha,X.actionList[al-1].icon, 'Lever')
        elif self.act.actions['Lever']!=None:
            E.timeline.destroyLink(alpha.getTick('Lever'),self.act.actions['Lever'].icon )
            self.act.actions['Lever'] = None
        if ae!=0:
            self.act.actions['End'] = X.actionList[ae-1]
            E.timeline.makeLink(alpha,X.actionList[ae-1].icon , 'End')
        elif self.act.actions['End']!=None:
            E.timeline.destroyLink(alpha.getTick('End'),self.act.actions['End'].icon )
            self.act.actions['End'] = None

class DialogWait(IntervalForm):
    """ Creator/Editor for Wait interval"""
    def __init__(self, parent, ID):
        IntervalForm.__init__(self,parent,ID,"Wait Interval")
        
        waitdesc = '''A Wait interval is a fixed period of time when nothing happens.
        No tone is played and lever presses during a wait interval will be recorded but not rewarded'''
        self.tbl.Add(wx.StaticText(self, -1, waitdesc), row=1, col=1, colspan=2)        
        
        self.tbl.Fit(self)
    
    def onSubmit(self, evt):
        name = self.nameField.GetValue()
        try:
            dur = float(self.durField.GetValue())
            md = float(self.mdField.GetValue())
            if dur==0.0:
                self.nonZeroDuration()
                return
        except ValueError:
            self.nonZeroDuration()
            return
        if self.act==None:
            ind = X.addInterval(Intervals.WaitInt(dur, name))
            self.Parent.timeline.addInterval(ind)
            self.act = X.intervalList[ind]
        else:
            X.intervalList[self.Id].name = name
            X.intervalList[self.Id].duration = dur
            IntervalForm.linkacts(self, evt)
        self.act.maxDuration = md
        if self.varyCheck.IsChecked():
            self.act.vary = True
            self.act.varyBy = float(self.varyField.GetValue())
        else:
            self.act.vary = False
            self.act.varyBy = 0.0
        E.panel.adjustTd()
        self.Close()        
                        
class DialogTone(IntervalForm):
    """ Creator/Editor for Tone interval"""
    ToneCount = 0
    def __init__(self, parent, ID):
        IntervalForm.__init__(self,parent,ID,"Tone Interval")
            
        tonedesc = '''A Tone interval is a the period of time when a tone is played.
        While tone is playing, lever presses will be recorded but not rewarded'''
        self.tbl.Add(wx.StaticText(self, -1, tonedesc), row=1, col=1, colspan=2)
    
        self.tbl.Add(wx.StaticText(self, -1, "Tone Played"), row=9, col=1)    
        self.toneField = wx.Choice(self, -1, choices=uv.ToneNames)
        self.toneField.Select(0)
        self.tbl.Add(self.toneField, row=9, col=2)
        
        if self.act != None:
            f = self.act.freq
#raj-changes made to handle the cases when we load an old xml and the freq is not matching with the present updated list of Freq.
            try:
                i=uv.ToneFreq.index(f)
            except ValueError,e:
                er  = e
               # print er
               # pass
            else:
                i = uv.ToneFreq.index(f)
                self.toneField.Select(i)

        self.tbl.Fit(self)
#raj-changes ends
    def onSubmit(self, evt):
        name = self.nameField.GetValue()
        try:
            dur = float(self.durField.GetValue())
            md = float(self.mdField.GetValue())
            if dur==0.0:
                self.nonZeroDuration()
                return
        except ValueError:
            self.nonZeroDuration()
            return
        if not(self.act):
            ti = Intervals.ToneInt(dur, name)
            ti.freq = uv.ToneFreq[self.toneField.GetSelection()]
            ind = X.addInterval(ti)
            self.Parent.timeline.addInterval(ind)
            self.act = X.intervalList[ind]
        else:
            self.act.name = name
            self.act.duration = dur
            self.act.freq = uv.ToneFreq[self.toneField.GetSelection()]
            self.act.icon.ClearText()
            self.act.icon.AddText("%d Hz" % uv.ToneFreq[self.toneField.GetSelection()])
            IntervalForm.linkacts(self, evt)
        self.act.maxDuration = md
        if self.varyCheck.IsChecked():
            self.act.vary = True
            self.act.varyBy = float(self.varyField.GetValue())
        else:
            self.act.vary = False
            self.act.varyBy = 0.0
        E.panel.adjustTd()
        self.Close()

class DialogRewardInt(IntervalForm):
    """ Creator/Editor for Reward interval"""
    def __init__(self, parent, ID):
        IntervalForm.__init__(self,parent,ID,"Reward Interval")

        desc = '''A Reward interval is a fixed period of time when any lever press will constitute for an reward to be issued.'''
        self.tbl.Add(wx.StaticText(self, -1, desc), row=1, col=1, colspan=2)
            
        self.tbl.Fit(self)
    
    def onSubmit(self, evt):
        name = self.nameField.GetValue()
        try:
            dur = float(self.durField.GetValue())
            md = float(self.mdField.GetValue())
            if dur==0.0:
                self.nonZeroDuration()
                return
        except ValueError:
            self.nonZeroDuration()
            return
        if not(self.act):
            ind = X.addInterval(Intervals.RewardInt(dur, name))
            rect = E.timeline.addInterval(ind)
            ai = len(X.actionList)
            X.actionList.append(Actions.Taste(name + " action"))
            X.intervalList[ind].actions['Lever'] = X.actionList[ai]
            X.intervalList[ind].actions['Lever'].valves.append(0)
            ces = E.timeline.addAction(ai, False)
            ces.SetY(100)
            ces.SetX(rect.GetX())
            E.timeline.makeLink(rect,ces, 'Lever')
            self.act = X.intervalList[ind]
            E.timeline.canvas.Refresh(True)
        else:
            self.act.name = name
            self.act.duration = dur
            IntervalForm.linkacts(self, evt)
        self.act.maxDuration = md
        if self.varyCheck.IsChecked():
            self.act.vary = True
            self.act.varyBy = float(self.varyField.GetValue())
        else:
            self.act.vary = False
            self.act.varyBy = 0.0
        E.panel.adjustTd()
        self.Close()
        
class DialogNogo(IntervalForm):
    """ Creator/Editor for No Go interval"""
    def __init__(self, parent, ID):
        IntervalForm.__init__(self,parent,ID,"No Go Interval")

        desc = '''A No Go interval is a fixed period of time when 
        reward to be issued at the end if the lever is not pressed'''
        self.tbl.Add(wx.StaticText(self, -1, desc), row=1, col=1, colspan=2)
        
        self.tbl.Fit(self)
    
    def onSubmit(self, evt):
        name = self.nameField.GetValue()
        try:
            dur = float(self.durField.GetValue())
            md = float(self.mdField.GetValue())
            if dur==0.0:
                self.nonZeroDuration()
                return
        except ValueError:
            self.nonZeroDuration()
            return
        if not(self.act):
            ind = X.addInterval(Intervals.NogoInt(dur, name))
            rect = E.timeline.addInterval(ind)
            ai = len(X.actionList)
            X.actionList.append(Actions.Taste(name + " action"))
            X.intervalList[ind].actions['End'] = X.actionList[ai]
            X.intervalList[ind].actions['End'].valves.append(0)
            ces = E.timeline.addAction(ai, False)
            ces.SetY(100)
            ces.SetX(rect.GetX())
            E.timeline.makeLink(rect,ces,'End')
            self.act = X.intervalList[ind]
            E.timeline.canvas.Refresh(True)
        else:
            X.intervalList[self.Id].name = name
            X.intervalList[self.Id].duration = dur
            IntervalForm.linkacts(self, evt)
        self.act.maxDuration = md
        if self.varyCheck.IsChecked():
            self.act.vary = True
            self.act.varyBy = float(self.varyField.GetValue())
        else:
            self.act.vary = False
            self.act.varyBy = 0.0
        E.panel.adjustTd()
        self.Close()
        
class ActionForm(FormDialog):
    """Super class for Action dialog"""
    def __init__(self, parent, ID, title):
        FormDialog.__init__(self,parent,ID, title)
        
        self.act = None
        if ID >= 0 and ID < len(X.actionList):
            self.act = X.actionList[ID]
        
        self.tbl.Add(wx.StaticText(self, -1, "Name"), row=3, col=1)
        self.nameField = wx.TextCtrl(self)
        self.tbl.Add(self.nameField, row=3, col=2)
        
        self.manCheck = wx.CheckBox(self, -1, "Create manual button")
        self.tbl.Add(self.manCheck, row=4, col=1)
        
        self.tcCheck = wx.CheckBox(self, -1, "Time Constraints")
        self.tbl.Add(self.tcCheck, row=4, col=2)
        
        tcSizer = wx.BoxSizer(wx.HORIZONTAL)
        tcSizer.Add(wx.StaticText(self, -1, "Min Time"))
        self.tcMinField = wx.TextCtrl(self)
        tcSizer.Add(self.tcMinField)
        tcSizer.AddSpacer(50, 10)
        tcSizer.Add(wx.StaticText(self, -1, "Max Time"))
        self.tcMaxField = wx.TextCtrl(self)
        tcSizer.Add(self.tcMaxField)
        self.tbl.Add(tcSizer, row=5, col=1, colspan=2)
        self.tbl.Hide(tcSizer, True)
        
        def tcToggle(evt):
            if evt.IsChecked():
                self.tbl.Show(tcSizer, True)
                self.tbl.Fit(self)
            else:
                self.tbl.Hide(tcSizer, True)
                self.tbl.Fit(self)
        self.tcCheck.Bind(wx.EVT_CHECKBOX, tcToggle)
        
        if self.act:
            self.nameField.SetValue(self.act.name)
            if self.act.isManual:
                self.manCheck.SetValue(True)
            if self.act.hasTimeConstraints:
                self.tcCheck.SetValue(True)
                self.tbl.Show(tcSizer, True)
                self.tbl.Fit(self)
                self.tcMaxField.SetValue(str(self.act.maxTime))
                self.tcMinField.SetValue(str(self.act.minTime))
        else:
            self.nameField.SetValue("act %d" % len(X.actionList))
    
    def changeText(self,newname):
        """Update name change into the action shape"""
        self.act.icon.ClearText()
        self.act.icon.AddText(newname)
        

class DialogTaste(ActionForm):
    """ Creator/Editor for Taste action"""
    def __init__(self, parent, ID):
        ActionForm.__init__(self,parent,ID,"Deliver Taste Action")
        
        desc = 'Delivers taste from one of the opened valves'
        self.tbl.Add(wx.StaticText(self, -1, desc), row=1, col=1, colspan=2)
        
        self.tbl.Add(wx.StaticText(self, -1, "Run Time"), row=6, col=1)
        self.rtField = wx.TextCtrl(self,-1,value=str(0.22))  #raj- changed the value to 0.22 as per the requirement
        self.tbl.Add(self.rtField, row=6,col=2)
        
        self.tbl.Add(wx.StaticText(self, -1, "Associated Taste(s)"), row=7, col=1, flag=wx.ALIGN_TOP)
        self.tastesField = wx.CheckListBox(self, -1, size=wx.DefaultSize, choices=uv.TasteNames)
        self.tastesField.SetInitialSize((100,50))
        self.tbl.Add(self.tastesField, row=7, col=2)
        
        if self.act:
            self.rtField.SetValue(str(self.act.runTime))
            self.tastesField.SetChecked(self.act.valves)
           
        self.tbl.Fit(self)
        
    
    def onSubmit(self,evt):
        name = self.nameField.GetValue()
        mb = self.manCheck.IsChecked()
        tc = [self.tcCheck.IsChecked(), 0.0, 0.0]
        rt = 0.0
        if tc[0]:
            try:
                tc[1] = float(self.tcMinField.GetValue())
                tc[2] = float(self.tcMaxField.GetValue())
            except ValueError:
                pass
            
        if self.act:
            if self.act.name!=name:
                self.act.name = name
                self.changeText(name)
            self.act.hasTimeConstraints = tc[0]
        else:    
            ind = len(X.actionList)
            X.actionList.append(Actions.Taste(name))
            self.act = X.actionList[ind]
            E.timeline.addAction(ind, True)
            E.timeline.bindPlaceMouse()
        self.act.isManual = mb
        if tc[0]:
            self.act.setTimeConstraints(tc[1], tc[2])
        try:
            rt = float(self.rtField.GetValue())
        except ValueError:
            pass
        self.act.valves = list(self.tastesField.GetChecked())
        self.act.runTime = rt
        self.Close()

class DialogJump(ActionForm):
    """ Creator/Editor for Jump action"""
    def __init__(self, parent, ID):
        ActionForm.__init__(self,parent,ID,"Jump to Interval Action")
        
        self.ints = []
        it = 0
        for i in X.intervalList:
            self.ints.append("[%d] %s"%(it,i.name))
            it+=1
        self.intRows = 0
        self.jisets = []
        
        desc = 'Pushes clock to the start of another interval'
        self.tbl.Add(wx.StaticText(self, -1, desc), row=1, col=1, colspan=2)
        
        self.isNewTrial = wx.CheckBox(self,-1,"Start new trial")
        self.isNewTrial.SetValue(True)
        self.tbl.Add(self.isNewTrial, row=5, col=1)
        if self.act:
            if self.act.newTrial:
                self.isNewTrial.SetValue(True)
            else:
                self.isNewTrial.SetValue(False)
        
        self.tbl.Add(wx.StaticText(self,-1,"Intervals to Jump to"), row=6, col=1)
        self.newJi_button = wx.Button(self,-1,"+")
        self.tbl.Add(self.newJi_button, row=6, col=2)
        
        self.jilist = wx.GridSizer(-1,3,0,0)
        self.jipanel = scrollp.ScrolledPanel(self)
        self.jipanel.SetMaxSize((-1,100))
        self.jipanel.SetupScrolling()
        self.jilist.AddMany([wx.StaticText(self.jipanel, -1, "Jump to"),
                             wx.StaticText(self.jipanel, -1, "Probability"),
                             wx.StaticText(self.jipanel, -1, "Delete")])
        if self.act:
            self.loadJumps()
        self.jipanel.SetSizerAndFit(self.jilist)
        self.tbl.Add(self.jipanel, row=7, col=1, colspan=2,rowspan=2)        
        
        condy = None
        if self.act:
            condy = self.act.condition
        clist = [Conditions.NullCon(), Conditions.TimeLimit(), 
            Conditions.TrialsLimit(),Conditions.RewardsLimit(), 
            Conditions.ConRwLimit(), Conditions.Noty(), 
            Conditions.Ory(), Conditions.Andy(), Conditions.Xory()]

        self.copanel = pine.createTreePanel(self,clist,condy)
        self.tbl.Add(self.copanel,row=3,col=3,rowspan=4,colspan=1)
        
        self.Bind(wx.EVT_BUTTON, self.onAddJi, self.newJi_button)
           
        self.tbl.Fit(self)
        
    def onAddJi(self,evt):
        """Create new line of components for a interval to joint to"""
        jumpTo = wx.Choice(self.jipanel,self.intRows,choices=self.ints)
        jumpTo.Select(0)
        jumpProb = wx.TextCtrl(self.jipanel,self.intRows,"")
        delButton = wx.Button(self.jipanel,self.intRows,"x")
        if type(evt) is list:
            jumpTo.Select(evt[0])
            jumpProb.SetValue(str(evt[1]))        
        self.jisets.append([jumpTo,jumpProb,delButton])
        self.intRows+=1
        self.Bind(wx.EVT_BUTTON, self.delJump, delButton)
        self.jilist.AddMany([jumpTo, jumpProb, delButton])
        self.jilist.Fit(self.jipanel)
        
    def loadJumps(self):
        """ make line components for intervals in jumper list"""
        if self.act==None:
            return
        for ji in self.act.jumper:
            self.onAddJi(ji)
        
    def delJump(self,evt):
        """ delete interval in jumper"""
        obj = evt.GetEventObject()
        objId = obj.GetId()
        self.jilist.Remove(self.jisets[objId][0])
        self.jilist.Remove(self.jisets[objId][1])
        self.jilist.Remove(self.jisets[objId][2])
        del self.jisets[objId:objId+1]
        self.intRows-=1
        self.jilist.Fit(self.jipanel)
        
    def onSubmit(self,evt):
        name = self.nameField.GetValue()
        mb = self.manCheck.IsChecked()
        tc = [self.tcCheck.IsChecked(), 0.0, 0.0]
        if tc[0]:
            try:
                tc[1] = float(self.tcMinField.GetValue())
                tc[2] = float(self.tcMaxField.GetValue())
            except ValueError:
                pass
        sum = 0.0
        listy = []
        for fs in self.jisets:
            i = fs[0].GetSelection()
            p = float(fs[1].GetValue())
            sum+=p
            listy.append([i,p])
        if sum>1.0:
            ErrorPopup("The probabilities must sum up to 1.0")
            return 
        if self.act:
            if self.act.name!=name:
                self.act.name = name
                self.changeText(name)
            self.act.hasTimeConstraints = tc[0]
            #change links
        else:    
            ind = len(X.actionList)
            X.actionList.append(Actions.Jump(name))
            self.act = X.actionList[ind]
            E.timeline.addAction(ind, True)
            E.timeline.bindPlaceMouse()
        self.act.isManual = mb
        if tc[0]:
            self.act.setTimeConstraints(tc[1], tc[2])
        if self.isNewTrial.IsChecked():
            self.act.newTrial = True
        else:
            self.act.newTrial = False
        del self.act.jumper[:]
        self.act.jumper.extend(listy)
        condy = self.copanel.getMasterCondition()
        if condy==None:
            condy = Conditions.NullCon()
        self.act.condition = condy
        self.Close()


class DialogChangeIntDur(ActionForm):
    """ Creator/Editor for Change Interval Duration action"""
    def __init__(self, parent, ID):
        ActionForm.__init__(self,parent,ID,"Change Interval Duration Action")
        
        desc = 'Extends by adding or multiplying interval duration'
        self.tbl.Add(wx.StaticText(self, -1, desc), row=1, col=1, colspan=2)
                
        self.tbl.Add(wx.StaticText(self,-1,"Select Interval:"), row=7,col=1)
        ints = []
        it = 0
        for i in X.intervalList:
            ints.append("[%d] %s"%(it,i.name))
            it+=1
        
        self.intField = wx.Choice(self,-1,choices=ints)
        self.intField.Select(0)
        self.tbl.Add(self.intField,row=7,col=2)
        
        self.add = wx.RadioButton( self, -1, "Add", style=wx.RB_GROUP )
        mul = wx.RadioButton( self, -1, "Multiply" )
        self.tbl.Add(self.add,row=8,col=1)
        self.tbl.Add(mul,row=8,col=2)
        
        self.tbl.Add(wx.StaticText(self,-1,"Increment"), row=9, col=1)
        self.increField = wx.TextCtrl(self,-1,"0.0")
        self.tbl.Add(self.increField, row=9, col=2)
        
        if self.act:
            self.intField.Select(self.act.interval)
            if self.act.mode==0:
                self.add.SetValue(True)
            else:
                mul.SetValue(True)
            self.increField.SetValue(str(self.act.increment))
           
        self.tbl.Fit(self)
      
    def onSubmit(self, evt):
        name = self.nameField.GetValue()
        mb = self.manCheck.IsChecked()
        tc = [self.tcCheck.IsChecked(), 0.0, 0.0]
        seli = self.intField.GetSelection()
        if tc[0]:
            try:
                tc[1] = float(self.tcMinField.GetValue())
                tc[2] = float(self.tcMaxField.GetValue())
            except ValueError:
                pass
            
        if self.act:
            if self.act.name!=name:
                self.act.name = name
                self.changeText(name)
            self.act.hasTimeConstraints = tc[0]
            if self.act.interval!=seli:
                E.timeline.destroyLink(self.act.icon,X.intervalList[self.act.interval].icon)
        else:    
            ind = len(X.actionList)
            X.actionList.append(Actions.ChangeIntDur(name))
            self.act = X.actionList[ind]
            E.timeline.addAction(ind, True)
            E.timeline.bindPlaceMouse()
        self.act.isManual = mb
        if tc[0]:
            self.act.setTimeConstraints(tc[1], tc[2])
        self.act.interval = seli
        X.intervalList[seli].changable = True
        if self.add.GetValue():
            self.act.mode = 0
        else:
            self.act.mode = 1
        self.act.increment = float(self.increField.GetValue())
        ival = X.intervalList[self.act.interval]
        if ival.duration>=ival.maxDuration:
            ErrorPopup("Remember to set the max duration of the interval we are incrementing")
        self.Close()

class DialogTrigger(FormDialog):
    """ Triggered actions editor """
    def __init__(self, parent, ID):
        FormDialog.__init__(self, parent, ID, "Triggered Actions")
        if len(choosenOnes)<1:
            ErrorPopup('Make sure you select the triggering action first')
            return
        desc = '''Triggered actions are a sequence of actions 
        to performed after an action has completed'''
        self.tbl.Add(wx.StaticText(self, -1, desc), row=1, col=1, colspan=2)
        
        self.alist = []
        self.ion = None
        if issubclass(choosenOnes[0].__class__, Actions.Action):
            self.ion = choosenOnes[0]
            self.tbl.Add(wx.StaticText(self,-1,self.ion.name+" triggers"),row=3,col=1)
        
            for t in self.ion.triggerFor:
                self.alist.append(t.name)
            
            for i in range(1,len(choosenOnes)):
                if issubclass(choosenOnes[i].__class__, Actions.Action):
                    self.alist.append(choosenOnes[i].name) 
                    self.ion.triggerFor.append(choosenOnes[i])
            
            self.ta = wx.ListBox(self,-1,choices=self.alist)
            self.tbl.Add(self.ta,row=4,col=1,rowspan=5)
            
            mvUp = wx.Button(self,-1,label="Move Up")
            mvDn = wx.Button(self,-1,label="Move Down")
            rm = wx.Button(self,-1,label="Remove")
            
            self.tbl.AddMany([ (mvUp,0,0,0, 4, 2), (mvDn,0,0,0,5,2), (rm,0,0,0,6,2)])
            
            self.Bind(wx.EVT_BUTTON,self.onMvUp,mvUp)
            self.Bind(wx.EVT_BUTTON,self.onMvDn,mvDn)
            self.Bind(wx.EVT_BUTTON,self.onRm,rm)
            self.tbl.Fit(self)
            self.ShowModal()
        else:
            ErrorPopup('Make sure you select the triggering action first')
            return
    
    
    def onMvUp(self,event):
        """move action up on triggers list"""
        sel = self.ta.GetSelection()
        if sel==wx.NOT_FOUND:
            return
        if sel==0:
            return
        a = self.alist[sel-1]
        b = self.alist[sel]
        ap = self.ion.triggerFor[sel-1]
        bp = self.ion.triggerFor[sel]
        self.alist[sel-1] = b
        self.alist[sel] = a
        self.ion.triggerFor[sel-1] = bp
        self.ion.triggerFor[sel] = ap
        
        self.ta.SetItems(self.alist)
        self.ta.Select(sel-1)
    
    def onMvDn(self,evt):
        """move action down on triggers list"""
        sel = self.ta.GetSelection()
        if sel==wx.NOT_FOUND:
            return
        if sel==len(self.alist)-1:
            return
        a = self.alist[sel+1]
        b = self.alist[sel]
        ap = self.ion.triggerFor[sel+1]
        bp = self.ion.triggerFor[sel]
        self.alist[sel] = a
        self.alist[sel+1] = b
        self.ion.triggerFor[sel] = bp
        self.ion.triggerFor[sel+1] = ap
        self.ta.SetItems(self.alist)
        self.ta.Select(sel+1)
    
    def onRm(self,evt):
        """ remove selected trigger """
        sel = self.ta.GetSelection()
        if sel==wx.NOT_FOUND:
            return
        self.alist.pop(sel)
        E.timeline.destroyLink(self.ion.icon, self.ion.triggerFor[sel].icon)
        self.ion.triggerFor.pop(sel)
        self.ta.SetItems(self.alist)
    
    def onSubmit(self,event):
        for t in self.ion.triggerFor:
            try:
                L = E.timeline.linesMap[(self.ion.icon,t.icon)]
            except KeyError:
                E.timeline.makeLink(self.ion.icon, t.icon)
        self.Close()
 
class DialogCondition(FormDialog):
    """ Editor for Terminator condition """
    def __init__(self, parent, ID):
        FormDialog.__init__(self,parent,ID,"Terminate Condition")
        desc = 'Define a termination condition for the experiment'
        self.tbl.Add(wx.StaticText(self, -1, desc), row=1, col=1, colspan=2)
        clist = [Conditions.NullCon(), Conditions.TimeLimit(), 
            Conditions.TrialsLimit(),Conditions.RewardsLimit(), 
            Conditions.ConRwLimit(), Conditions.Noty(), 
            Conditions.Ory(), Conditions.Andy(), Conditions.Xory()]
        xterm = None
        if X.terminator:
            xterm = X.terminator
            print xterm.toString()
        self.copanel = pine.createTreePanel(self,clist,xterm)
        self.tbl.Add(self.copanel,row=3,col=1,colspan=2,rowspan=5)
        self.tbl.Fit(self)
        
    def onSubmit(self,evt):
        X.terminator = self.copanel.getMasterCondition()
        self.Close()


class Editor(wx.App):
    """ Main frame of editor"""
    def __init__(self, redirect=False, filename=None):
        wx.App.__init__(self, redirect, filename)
        self.frame = wx.Frame(None, 0, title='Experiment Editor', size=(810, 600))
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        fileMenu.Append(101, "New")
        fileMenu.Append(102, "Open")
        fileMenu.Append(103, "Save")
        fileMenu.Append(104, "Save As")
        fileMenu.AppendSeparator()
        
        fileMenu.Append(107, "Run")
        fileMenu.Append(112, "Termination Condition")
        fileMenu.Append(110, "Print Data")
        fileMenu.AppendSeparator()
        
        #fileMenu.Append(109, "Exit")
        menuBar.Append(fileMenu, "Experiment")
        
        selMenu = wx.Menu()
        selMenu.Append(105,"Deselect All")
        selMenu.Append(111,"Trigger Actions")
        menuBar.Append(selMenu, "Selection")
        
        self.frame.SetMenuBar(menuBar)
        
        self.frame.Bind(wx.EVT_MENU, self.doNewExp, id=101)
        self.frame.Bind(wx.EVT_MENU, self.doOpenExp, id=102)
        self.frame.Bind(wx.EVT_MENU, self.doSaveExp, id=103)
        self.frame.Bind(wx.EVT_MENU, self.doSaveAs, id=104)
        self.frame.Bind(wx.EVT_MENU, self.deselectAll, id=105)
        self.frame.Bind(wx.EVT_MENU,self.doRunExp, id=107)
        #self.frame.Bind(wx.EVT_MENU, self.kamikaze, id=109)
        self.frame.Bind(wx.EVT_MENU, self.printExtData, id=110)
        self.frame.Bind(wx.EVT_MENU,self.openTriggerDialog, id=111)
        self.frame.Bind(wx.EVT_MENU,self.openCondsDialog, id=112)
        
        self.statusBar = wx.StatusBar(self.frame, 2)
        self.frame.SetStatusBar(self.statusBar)
        
        self.timeline = Timeline(self.frame)
        self.panel = CtrlPanel(self.frame, self.timeline)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, flag=wx.EXPAND)
        sizer.Add(self.timeline, flag=wx.EXPAND)
        
        self.frame.SetSizer(sizer)
        self.frame.SetAutoLayout(True)
        
        self.wildcard = "Extended Markup Language (*.xml)|*.xml| All files (*.*)|*.*"
        self.filepath = None
        self.initGlobals()
        #self.autoGenActions()
        
        self.frame.Show()
    
    def kamikaze(self, evt):
        """Quit application"""
        self.Exit()
    
    def doNewExp(self, evt):
        """Set up for a new experiment"""
        global X
        X = Experiment()
        X.trialDuration = 30
        self.timeline.diagram.RemoveAllShapes()
        self.timeline.canvas.Refresh(True)
        self.filepath = None
    
    def doSaveExp(self, evt):
        """ Save experiment"""
        global saveExp
        if X.timeSoFar()>X.trialDuration:
            self.timeline.extendTrialDuration(True)
        saveExp = True
        if self.filepath:
            msg = 'Your experiment file'+self.filepath+' will be overwritten'
            confirm = wx.MessageDialog(E.frame, msg,'Overwrite Warning',wx.YES_NO | wx.ICON_INFORMATION)
            overwrite = confirm.ShowModal()
            if overwrite == wx.ID_YES:
                saveExperiment(self.filepath,X)
            
        else:
            self.doSaveAs(evt)
    
    def doSaveAs(self,evt):
        """ Save experiment as """
        global saveExp
        if X.timeSoFar()>X.trialDuration:
            self.timeline.extendTrialDuration(True)
        saveExp = True
        namer = wx.TextEntryDialog(self.frame, 'Give your experiment a short description here', 'Experiment Description', 'TestExp')
        if namer.ShowModal() == wx.ID_OK:
            X.name = namer.GetValue()
        filename = re.sub('[^A-Za-z0-9]+', '', X.name)
        namer.Destroy()
        filer = wx.FileDialog(self.frame, message="Save file as ...", defaultDir=os.getcwd() + '/saves', defaultFile=filename, wildcard=self.wildcard, style=wx.SAVE)
        if filer.ShowModal() == wx.ID_OK:
            self.filepath = filer.GetPath()
            saveExperiment(self.filepath, X)
        filer.Destroy()
    
    def doOpenExp(self, evt):
        """ Load experiment from XML file"""
        if not(saveExp):
          if(self.filepath!=None): #raj - made 'Do you want to save changes?' dialog to pop only when there is a file already which was loaded in editor
            confirm = wx.MessageDialog(E.frame, 'Do you want to save changes?','Save First?',wx.YES_NO | wx.ICON_INFORMATION)
            saveFirst = confirm.ShowModal()
            if saveFirst ==wx.ID_YES:
                self.doSaveAs(evt)
                return
        self.doNewExp(None)
        opener = wx.FileDialog(self.frame, message="Choose a file", defaultDir=os.getcwd(), defaultFile="", wildcard=self.wildcard, style=wx.OPEN | wx.CHANGE_DIR)
        if opener.ShowModal() == wx.ID_OK:
            self.filepath = opener.GetPath()
            global X 
            X = loadExperiment(self.filepath)
            self.timeline.bracts = 0
            for i in range(0, len(X.intervalList)):
                self.timeline.addInterval(i)
            for j in range(0,len(X.actionList)):
                ac = self.timeline.addAction(j,False)
                ac.SetY(200)
                ac.SetX(50+50 * self.timeline.bracts)
                self.timeline.bracts+=1;
            for itt in X.intervalList:
                for t,ia in itt.actions.items():
                    if ia!=None:
                        ia.icon.SetY(150)
                        E.timeline.makeLink(itt.icon,ia.icon,t)
            self.panel.input_expDur.SetValue(str(X.trialDuration))
            self.panel.autoRinseFlag.SetValue(X.autoRinse)
            self.panel.autoRinseTime.SetValue(str(X.rinseTime))
            for act in X.actionList:
                if act.isATrigger():
                    for ion in act.triggerFor:
                        E.timeline.makeLink(act.icon,ion.icon)
                E.timeline.drawActionLinks(act)
        opener.Destroy()
        os.chdir(rootDir)
    
    def doRunExp(self, evt):
        """ Express load this experiment into PyView"""
        if self.filepath==None:
            ErrorPopup('Please save experiment to file first')
        else:
            pathy = self.filepath.replace('\\','/')
            currdir = rootDir
            currdir = currdir.replace('\\','/')
            exefile=currdir+"/PyView.py"
            subprocess.Popen('python "'+exefile+'" "'+pathy+'"')
    
    def initGlobals(self):
        """ initalize brusehs"""
        global choosenOnes, palette
        palette['stroke'] = wx.Pen("#ff0000")
        palette['stroke'] .SetWidth(3)
        
        for k,v in uv.aColors.items():
            palette[k+'_pen'] = wx.Pen(v)
            palette[k+'_brush'] = wx.Brush(v)
        
        for k,v in uv.iColors.items():
            palette[k+'_pen'] = wx.Pen(v)
            palette[k+'_brush'] = wx.Brush(v)     
    
    def autoGenActions(self):
        """make preloaded actions"""
        rinse = Actions.Taste("Rinse")
        rinse.setManual()
        rinse.valve = 0
        mt = Actions.Taste("Manual Taste")
        mt.setManual()
        X.actionList.extend([rinse, mt])
        for ai in range(0,len(X.actionList)):
            sh = self.timeline.addAction(ai, False)
            sh.SetY(200)
            sh.SetX(self.timeline.w - 50 - 50 * self.timeline.bracts)
            self.timeline.bracts += 1
        
    def deselectAll(self,event):
        """ clear all selection"""
        for e in choosenOnes:
            e.icon.selected = False
            if issubclass(e.__class__, Intervals.Interval):
                e.icon.rect.SetPen(palette[e.type+'_pen'])
            else:
                e.icon.SetPen(palette[e.type+'_pen'])
        E.timeline.canvas.Refresh(True)
        del choosenOnes[:]
    
    def openTriggerDialog(self,event):
        """ Open trigger dialog"""
        wv = DialogTrigger(self.frame,-1)
        wv.Destroy()
        E.deselectAll(None)
    
    def openCondsDialog(self,evt):
        """ Open terminator dialog"""
        wv = DialogCondition(self.frame,-1)
        wv.ShowModal()
        wv.Destroy()

    def printExtData(self, evt):
        """Print Experiment information"""
        X.printExpData()
               

def ErrorPopup(msg):
    """Make popup
    Args:
        msg (str): message in popup dialog
    """
    dlg = wx.MessageDialog(E.frame, msg,'Error',wx.OK | wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()        

E = Editor()
E.MainLoop()
