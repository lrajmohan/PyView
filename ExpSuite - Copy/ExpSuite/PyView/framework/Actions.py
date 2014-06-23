import time
import random
class Action(object):
    """
    Super class for Actions: Taste, PlayTone, Jump, ChangeIntDur
    """
    def __init__(self,name=""):
        self.performed = False
        """if action is performed"""
        self.hasTimeConstraints = False
        """if time constraints defined, then Action is not performed if we are not within"""
        self.isManual = False
        """if this action can be manually triggered"""
        self.ready = False
        """sometimes this flag is used to figure out if we should perform this action"""
        self.triggerFor = []
        """ Actions we preform immediately after this action is performed"""
        self.name=name
        """name of action"""
        self.type="superclass"
        """ type of action"""

    def act(self):
        """ empty function, later binded by Experiment execution module
        """
        pass

    def bindAction(self,actmeth):
        """ bind the function passed by 'actmeth' to the act() function
        """
        self.__dict__['act'] = actmeth
    
    def setManual(self):
        """ set this action to be manually stimulated
        """
        self.isManual = True
    
    def setTimeConstraints(self,minTime,maxTime):
        """ set time constraints
        """
        self.minTime = minTime
        self.maxTime = maxTime
        self.hasTimeConstraints = True
    
    def checkTimeConst(self,t):
        """ are we within time constraint
        """
        if self.hasTimeConstraints:
            if t>=self.minTime and t<=self.maxTime:
                return True
            else:
                return False
        else:
            return True
    
    def perform(self,t):
        """Perform action by:
            checking time constraint
            running act() function
            run perform() on all triggerFor actions
        """
        if not(self.checkTimeConst(t)):
            return False
        else:
            self.act()
        self.performed = True
        print "%s performed at %f"%(self.name,t)
        if self.isATrigger():
            self.triggerActions(t)
            
      
    def addTriggeredEffect(self,anotherAction):
        """ Add 'anotherAction' to triggerFor list  
        """
        self.triggerFor.append(anotherAction)
    
    def isATrigger(self):
        """ test if this action is a trigger for any other actions
        """
        return len(self.triggerFor)>0
    
    def triggerActions(self,t):
        """ run perform() on all triggerFor actions
        """
        for a in self.triggerFor:
            a.perform(t)
    
    def toString(self):
        """ print Action information
        """
        ln1 = "%s Action: %s\n" % (self.type,self.name)
        ln2 = "Manual=%s \n"%(self.isManual)
        if self.hasTimeConstraints:
            ln3 = "Time Constraint [%f,%f] secs \n"%(self.minTime,self.maxTime)
            ln2+=ln3
        if self.isATrigger():
            ln4 = "Trigger for: \n"
            for t in self.triggerFor:
                ln4+=(t.name+", ")
            ln2+=ln4+"\n"
        return ln1+ln2
        

class Taste(Action):
    """
    Deliver taste from valve action
    """    
    def __init__(self,name):
        Action.__init__(self,name)
        self.type="Taste"
        self.runTime = 0.043
        """lag time to deliver water from valve"""
        self.valves = []
        """ Available valves to deliver water from. If more than one is select,
        then we randomly choose one"""
     
    def chooseATaste(self):
        """ Returns the valve number to open"""
        l = len(self.valves)
        if l==0:
            return -1
        elif l==1:
            return self.valves[0]
        else:
            return random.choice(self.valves)
       
    def toString(self):
        """
        Extends to toString() function as defined in Action 
        """
        ln0 = Action.toString(self)
        ln1="Delivery Time=%f s\n"%(self.runTime)
        ln1 += "Default valves: ["
        for v in self.valves:
            ln1+=str(v)+", "
        ln1+="]\n"
        return ln0+ln1

class PlayTone(Action):
    """ s not an active action in the experiment paradigm. 
    It is used during our particular PyView implementation 
    to attach to the begin action of any Tone intervals.
    """
    def __init__(self,name):
        Action.__init__(self,name)
        self.name = name
        self.type="PlayTone"
        self.freq=1000
        """ frequency: 1000 Hz - 11,160 Hz (default=1000) """
    
    def toString(self):
        """ Extends to toString() function as defined in Action """
        return Action.toString(self)

  
class Jump(Action):
    """ Jumps to the start of another interval """
    def __init__(self,name):
        Action.__init__(self, name)
        self.type="Jump"
        self.jumper = []
        """ 2d array of interval(s) to jump to [Interval Index, Jump Probability]"""
        self.condition = None 
        """ when condition==None or NullCon it is considered as true, and will jump by default """
        self.newTrial = True
        """ if this jump stimulates a new trial event"""
    
    def test(self,p):
        """ Test if we should jump or nop"""
        if self.condition==None:
            return True
        else:
            return self.condition.test(p)
        
    def selectIval(self, r):
        """ Returns the index of the interval to jump to
        
        Arguments:
            r : (float) random number [0,1)
        """
        minLim = 0.0
        si = 0
        for j in range(0,len(self.jumper)):
            if r>minLim and r<=(minLim+self.jumper[j][1]):
                si = self.jumper[j][0]
                break
            minLim+=self.jumper[j][1]
        return si
           
    def toString(self):
        """
        Extends to toString() function as defined in Action    
        """
        ln0 = Action.toString(self)
        ln1 ="Jump to: ["
        leny = len(self.jumper)
        for i in range(0,leny):
            ln1+=" (%d,%f),"%(self.jumper[i][0], self.jumper[i][1])
        ln1+="]\n"
        return ln0+ln1
    
    def makeRestarter(self):
        """ Make this jump simulate a restart action"""
        del self.jumper[:]
        self.jumper.append([0,1.0])
        self.newTrial = True
        self.condition = None
    
class ChangeIntDur(Action):
    """ Cause an interval duration to change
    """
    def __init__(self,name):
        Action.__init__(self, name)
        self.type="ChangeIntDur"
        self.interval = 0
        """index of interval to influence""" 
        self.increment = 0
        """ how much to increment by """
        self.mode = 0 
        """ additive or multiplicative increment [0: add, 1: multi]"""
           
    def toString(self):
        """ Extends to toString() function as defined in Action"""
        ln0 = Action.toString(self)
        ln1 = "Change duration of interval %d \n"%(self.interval)
        if self.mode==0:
            m="+"
        else:
            m="*"
        ln2=m+str(self.increment)+"\n"
        return ln0+ln1+ln2
