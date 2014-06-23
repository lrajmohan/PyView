"""
Intervals module

"""
import random
class Interval(object):
    """Super class for interval objects
    
    Interval objects are WaitInt, ToneInt, RewardInt, and NogoInt
    """
    
    def __init__(self,duration=0,name=""):
        """ Creates an Interval Action
        
        Kwargs:
            duration (float): duration of interval. 0 by DEFAULT
            nane (str): nickname of interval. "" by DEFAULT
        """
        self.duration = duration 
        """how long this interval last"""
        self.maxDuration = duration 
        """if this interval is to be extended, how long can it possibility be"""
        self.oriDur = duration
        """original duration before its changed by random vary or ChangeIntDur"""
        self.name = name
        """nickname for this interval object"""
        self.actions = {'Lever':None,'Begin':None,'End':None}
        """Links to actions to be triggered upon these 3 modes. Begin, Lever, and End"""
        self.startTime = 0 
        """time interval is suppose to start at within trial time"""
        self.completed = False
        """if the clock has passed through this interval yet during PyView runtime"""
        self.vary = False 
        """if we can allow this interval to vary by some value at random"""
        self.varyBy = 0.0
        """if vary is True, how much will be vary by. 
        Vary duration D, st. D' = D + varyBy * (2*r-1); st. r : (0,1)
        """
        self.changable = False
        """if this interval is changable by a ChangeIntDur action"""
        self.type="superclass"
        """type of action"""

    def toString(self):
        """
        Generalized print for Intervals
        """
        ln1 = "%s Interval: %s \n" % (self.type,self.name)
        ln2 = "Start Time = %f \nDuration = %f \n" %(self.startTime,self.duration)
        if self.vary:
            ln3 = "Vary by %f \n"%(self.varyBy)
        else:
            ln3 = ""
        ln4 = "Associated Actions \n"
        for k,v in self.actions.items():
            if v!=None:
                v = v.name
            ln4+="\t %s : %s"%(k,v)
        return ln1+ln2+ln3+ln4
    
    def varyDuration(self):
        r = random.random()
        self.duration = self.oriDur+self.varyBy*(2.0*r-1.0)
        self.maxDuration = self.duration

# Just a block of time, nothing happens    
class WaitInt(Interval):
    """ Wait Interval is when nothing happens by default. It is just an allocated block of time within an experiment trial.
    """
    def __init__(self,duration,name):
        """ Creates Wait Interval by using constructor from superclass, Interval
        """
        Interval.__init__(self,duration,name)
        self.type="Wait"
        
# Duration in which tone is played
class ToneInt(Interval):
    """ Tone Intervals will play a tone for its duration
        
    """
    def __init__(self,duration,name):
        """ 
        Creates Tone Interval by using constructor from superclass, Interval
        """
        Interval.__init__(self,duration,name)
        self.type="Tone"
        self.freq = 0
        """ Tone frequency in Hz. 
        Based on the current setup and scaling. Frequency range = [1000,11160] Hz"""
    
    def toString(self):
        """ extends toString() function for ToneInterval
        """
        ln0 = Interval.toString(self)
        ln1 = "Tone Frequency = %d Hz \n"%self.freq
        return ln0+ln1

class RewardInt(Interval):
    """ If lever pressed during this interval we deliver taste 
    """
    def __init__(self,duration,name):
        Interval.__init__(self,duration,name)
        self.type="Reward"

class NogoInt(Interval):
    """ If lever pressed during this interval no reward is delievered at the end
    
    """
    
    def __init__(self,duration,name):
        Interval.__init__(self,duration,name)
        self.type="Nogo"
        self.ready = True
        """Is set false, if lever is pressed"""
