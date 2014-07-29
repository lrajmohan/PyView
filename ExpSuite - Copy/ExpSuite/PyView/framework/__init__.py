#import modules for this package
import Intervals
import Actions
import Conditions

#import python built-in modules
from xml.etree import ElementTree as elle
from datetime import datetime

class Experiment(object):
    """
    The Experiment class contains all information
    of an experiment paradigm. It consist of a sequence of intervals
    """    
    def __init__(self):
        self.trialDuration = 30.0
        """how long all the sequences last in seconds"""
        self.intervalList = []
        """list of intervals"""
        self.actionList = []
        """list of all actions in experiment"""
        self.name = '' 
        """nickname for experiment"""
        self.datestamp = '' 
        """date time experiment paradigm created"""

        self.terminator = None 
        """terminator will be a Condition,  
        if terminator is None then the experiment goes on 
        forever or until user manually stops it
        """
        
        self.autoRinse = False
        """ Automatically deliver water after a taste is delivered"""
        self.rinseTime = 0.025 #raj- changed the value to 0.025
        """ How long to deliver rinse for, in seconds"""
        self.rinseWait = 0.5
        """ intermission between reward delivery and rinse"""
        Actions.Taste.runTime = self.rinseTime #raj- changed to match with the rinse time

        self.loadedfilename = '' #raj- stores the name of the file loaded
        """stores the name of the file loaded"""
    def addInterval(self,ival):
        """
        Appends an Interval object to intervals list
        """
        ll=len(self.intervalList)
        print 'intervalListin add interval',self.intervalList
        print "ival::",str(ival)
        if ll>0:
            prev = self.intervalList[ll-1]
            ival.startTime = prev.startTime+prev.duration
            print "ival::",str(ival)
        self.intervalList.append(ival)
        return ll
    
    def printAllIntervals(self):
        """
        Prints intervals list
        """
        txt = ""
        for i in self.intervalList:
            txt+=i.fr()
        print txt
    
    def printAllActions(self):
        """
        prints list of actions
        """
        txt = ""
        for a in self.actionList:
            txt+=a.toString()
        print txt
          
    def adjustPostIntTimes(self,i):
        """
        When we change the interval duration, 
        we would need to recalculate the startTimes of the intervals after it
        
        Args:
            i (int): interval adjusted
        """
        if i==(len(self.intervalList)-1):
            return
        for j in range(i,len(self.intervalList)-1):
            self.intervalList[j+1].startTime = self.intervalList[j].startTime + self.intervalList[j].duration
    
    
    def timeSoFar(self):
        """
        Sums up the duration of all the intervals
        """
        ct = 0.0
        for i in self.intervalList:
            ct += i.duration
        return ct
    
    def maxTimeSoFar(self):
        """
        Sum up the max durations of all the intervals
        """
        ct = 0.0
        for i in self.intervalList:
            ct += i.maxDuration
        return ct
    
    def printExpData(self):
        """
        Prints experiment data (meta properties, all intervals, and actions)
        """
        print "\n Experiment %s"%self.name
        print "\t Trial Duration= %f s, Current Time = %f s"%(self.trialDuration,self.timeSoFar())
        termstr = "None"
        if self.terminator!=None:
            termstr = self.terminator.toString()
        print "\t Termination Condition: "+termstr
        self.printAllIntervals()
        self.printAllActions()
        
def loadExperiment(filename):
    """
    Reads XML file and returns an Experiment object create an Experiment, 
    which will be returned at the end
    """
    E = Experiment() #: 
    pe = "Error: Unable to parse "
    tree = elle.parse(filename)
        # root : <Experiment>
    root = tree.getroot()
        # info : <info>
    info = root.find('info')
    if info!=None:
        E.loadedfilename = filename #raj- to store the file which is loaded
        E.name = info.find('name').text
        E.datestamp = info.find('date').text
    else:
        print pe+"Cannot find meta information for this experiment"
    try:    
        E.trialDuration = float(tree.find('trialDuration').text)
    except ValueError:
        print pe+"Unable to parse trialDuration as float"
    
    # check if we have termination condition(s)
    term = tree.find('terminator')
    if len(list(term))>0:
        termroot = list(term)[0]
        E.terminator = Conditions.parseXml(termroot)
        #E.terminator.toString()
    
    #     check if an automatic rinse should be
    # administered after taste delievered
    # do : True/False
    # for : duration of rinse
    ar = tree.find('autoRinse')
    try:
        E.autoRinse = eval(ar.get('do'))
    except (ValueError,NameError,SyntaxError):
        print pe+"autoRinse.do as boolean"
    try:
        E.rinseTime = float(ar.get('for'))
    except ValueError:
        print pe+"autoRinise.for as float"
    try:
        E.rinseWait = float(ar.get('wait'))
    except ValueError:
        print pe+"waitRinse.for as float"
    
    # make list of intervals
    intervals = tree.find('intervals')
    ilist = []
    if intervals!=None:
        ilist = intervals.findall('Interval')

    # make Interval items
    for e in ilist:
        itype = e.get('type')
        iname = e.get('name')
        dure = e.find('duration')

        try:
            idur = float(dure.text)
        except ValueError:
            print pe+"duration as float"
        inter = None
        if itype=="Wait":
            inter = Intervals.WaitInt(idur,iname)

        elif itype=="Tone":
            inter = Intervals.ToneInt(idur,iname)
            act = Actions.PlayTone(iname) #raj
            opts = e.find('opt')
            try:
                inter.freq = int(opts.get('freq'))
                inter.freqType = str(opts.get('freqType')) #raj
                #print "inter::",inter.toString()

                #raj
                '''act.freq = int(opts.get('freq'))
                act.freqType = str(opts.get('freqType')) #raj
                #Actions.PlayTone(opts.get('freq')).freqType = str(opts.get('freqType')) #raj '''
                #raj

            except ValueError:
                print pe+"freq as integer"
        elif itype=="Reward":
            inter = Intervals.RewardInt(idur,iname)
        elif itype=="Nogo":
            inter = Intervals.NogoInt(idur,iname)


        else:
            continue
        md = dure.get('max')
        if md!=None:
            try:
                md = float(md)
                inter.maxDuration = md
            except ValueError:
                print pe+"maxDuration as float"
        try:
            inter.vary = eval(dure.get('vary'))
        except (ValueError,NameError,SyntaxError):
            print pe+"duration.vary as boolean"
        try:
            inter.changable = eval(dure.get('changable'))
        except (ValueError,NameError,SyntaxError):
            print pe+"duration.changable as boolean"
        try:
            inter.varyBy = float(dure.get('varyBy'))
        except ValueError:
            print pe+"duration.varyBy as float"
        inter.type = itype
        try:
            inter.startTime = float(e.find('startTime').text)
        except ValueError:
            print pe+"startTime as float"
        
        aa = e.find('action')
        try:
            aL = int(aa.find('Lever').get('id'))
            aB = int(aa.find('Begin').get('id'))
            aE = int(aa.find('End').get('id'))
        except ValueError:
            print pe+"one of the actions id as integer"
        if aL!=-1:
            inter.actions['Lever'] = aL
        if aB!=-1:
            inter.actions['Begin'] = aB
        if aE!=-1:
            inter.actions['End'] = aE
        try:    
            idx = int(e.get('id'))
        except ValueError:
            print pe+"Interval.id as integer"
        E.intervalList.insert(idx,inter)
    # make Action lists
    actions = tree.find('actions')
    alist = []
    if actions!=None:
        alist = actions.findall('Action')
    # make Action items
    aTrigList = []
    for e in alist:
        atype = e.get('type')
        aname = e.get('name')
        try:
            aman = eval(e.find('manual').text)
        except (ValueError,NameError,SyntaxError):
            print pe+"Action.manual as boolean"
        idx = int(e.get('id'))
        act = None
        if atype=="Taste":
            act = Actions.Taste(aname)
            opts = e.find('opt')
            rt = opts.get('runTime')
            try:
                act.runTime = float(rt)
            except ValueError:
                print pe+"runTime as float"
            ta = e.find('valves')
            for t in list(ta):
                act.valves.append(int(t.text))

        elif atype=="Jump":
            act = Actions.Jump(aname)
            opts = e.find('opt')
            try:
                act.newTrial = eval(opts.get('newTrial'))
            except (ValueError,NameError,SyntaxError):
                print pe+"newTrial as boolean"
            condy = e.find('condition')
            cl = list(condy)
            if len(cl)>0:
                act.condition = Conditions.parseXml(cl[0])
            jumper = e.find('jumper')
            jlist = jumper.findall('jump')
            for ji in jlist:
                try:
                    to = int(ji.get('to'))
                    pr = float(ji.get('prob'))
                except ValueError:
                    print pe+"jumper to as int or prob as float"
                act.jumper.append([to,pr])
        elif atype=="ChangeIntDur":
            act = Actions.ChangeIntDur(aname)
            ch = e.find('opt')
            try:
                act.interval = int(ch.get('int'))
                act.mode = int(ch.get('mode'))
                act.increment = float(ch.get('incre'))
            except ValueError:
                print pe+"ChangeIntDur opt as integers and floats"
        else:
            continue
        act.type = atype
        if aman:
            act.setManual()
        atc = e.find('timeConstraints')
        try:
            amin = float(atc.get('minTime'))
            amax = float(atc.get('maxTime'))
        except ValueError:
            print pe+"timeConstraints minTime or maxTime as floats"
        if amin!=amax:
            act.setTimeConstraints(amin, amax)
        trigs = e.find('triggers')
        tlist = list(trigs)
        aTrigList.insert(idx,[])
        if len(tlist)>0:
            for t in tlist:
                aTrigList[idx].append(int(t.text))
        E.actionList.insert(idx, act)
    
    # link up triggers
    for i in range(0,len(E.actionList)):
        if len(aTrigList[i])>0:
            for j in aTrigList[i]:
                E.actionList[i].triggerFor.append(E.actionList[j])
    
    # link up interval actions
    for i in E.intervalList:
        for k,v in i.actions.items():
            if v==None:
                continue
            i.actions[k] = E.actionList[v]
    
    return E

# Save experiment 'exp' as 'filename'
def saveExperiment(filename,exp):
    """ Save experiment
    
    Arguments:
        exp (Experiment): save experiment properties to filename
        filename (str): file to save to
     """
    root = elle.Element('Experiment')
    info = elle.Element('info')
    info_name = elle.Element('name')
    info_name.text = exp.name
    info_date = elle.Element('date')
    info_date.text = datetime.now().strftime("%Y.%B.%d %H.%M.%S")
    info.extend([info_date,info_name])
    root.append(info)

    time = elle.Element('trialDuration')
    time.text = str(exp.trialDuration)
    root.append(time)
    
    ar = elle.Element('autoRinse')
    ar.set('do',str(exp.autoRinse))
    ar.set('for',str(exp.rinseTime))
    ar.set('wait',str(exp.rinseWait))
    root.append(ar)
    
    term = elle.Element('terminator')
    if exp.terminator!=None:
        term.append(exp.terminator.toXml())
    root.append(term)

    # make XML list of intervals
    intervals = elle.Element('intervals')
    root.append(intervals)
    idx = 0
    for i in exp.intervalList:
        node = elle.Element('Interval')
        node.set('type',i.type)
        node.set('id',str(idx))
        node.set('name',i.name)
        startAt = elle.Element('startTime')
        startAt.text = str(i.startTime)
        duration = elle.Element('duration')
        duration.set('vary',str(i.vary))
        duration.set('varyBy',str(i.varyBy))
        duration.set('changable',str(i.changable))
        if i.duration!=i.maxDuration:
            duration.set('max',str(i.maxDuration))
        duration.text = str(i.duration)
        node.extend([startAt,duration])
        if i.type=="Tone":
            opt = elle.Element('opt')
            opt.set('freq',str(i.freq))
            opt.set('freqType',str(i.freqType)) #raj - to determine the frequency type while saving
            node.append(opt)
        action = elle.Element('action')
        for k,v in i.actions.items():
            act = elle.Element(k)
            if v==None:
                act.set('id',str(-1))
            elif isinstance(v, Actions.PlayTone):
                act.set('id',str(-1))
            else:
                act.set('id', str(exp.actionList.index(v)) )
            action.append(act)
        node.append(action)
        intervals.append(node)
        idx+=1
    
    # make XML list from Actions
    actions = elle.Element('actions')
    root.append(actions)
    idx = 0
    for i in exp.actionList:
        node = elle.Element('Action')
        node.set('type',i.type)
        node.set('id',str(idx))
        node.set('name',i.name)
        manual = elle.Element('manual')
        manual.text = str(i.isManual)
        timec = elle.Element('timeConstraints')
        mint = 0.0
        maxt = 0.0
        if i.hasTimeConstraints:
            mint = i.minTime
            maxt = i.maxTime
        timec.set('minTime',str(mint))
        timec.set('maxTime',str(maxt))
        triggers = elle.Element('triggers')
        if i.isATrigger():
            for j in i.triggerFor:
                jd = exp.actionList.index(j)
                ai = elle.Element('Act')
                ai.text = str(jd)
                triggers.append(ai)
        node.extend([manual,timec,triggers])
        if i.type=="Taste":
            opt = elle.Element('opt')
            opt.set('runTime',str(i.runTime))
            node.append(opt)
            tastes = elle.Element('valves')
            for t in i.valves:
                v = elle.Element('v')
                v.text = str(t)
                tastes.append(v)
            node.append(tastes)
        elif i.type=="Jump":
            jl = elle.Element('jumper')
            for j in i.jumper:
                ji = elle.Element('jump')
                ji.set('to',str(j[0]))
                ji.set('prob',str(j[1]))
                jl.append(ji)
            node.append(jl)
            opt = elle.Element('opt')
            opt.set('newTrial',str(i.newTrial))
            node.append(opt)
            condy = elle.Element('condition')
            if i.condition!=None:
                condy.append(i.condition.toXml())
            node.append(condy)
        elif i.type=="ChangeIntDur":
            ch = elle.Element("opt")
            ch.set('int',str(i.interval))
            ch.set('mode',str(i.mode))
            ch.set('incre',str(i.increment))
            node.append(ch)
        actions.append(node)
        idx+=1
    
    tree = elle.ElementTree(root)
    tree.write(filename)
    
def freq2int(f):
    """ converts frequency to a integer between 1-255"""
    return int((f-960)/40)

def int2freq(i):
    """ converts a integer (between 1-255) to a frequency between 1 KHz to 11.6 KHz"""
    return (i*40)+960

def int2bi8(num):
    """ converts an integer (between 1-255) to a bindary array"""
    if num>255:
        return []
    s = bin(num)
    s = s[2:]
    s = s.zfill(8)
    a = list(s)
    a.reverse()
    return a
