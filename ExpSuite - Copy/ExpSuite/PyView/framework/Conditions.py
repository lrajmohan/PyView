from xml.etree import ElementTree as elle
import random

"""
Conditions module
    
    Imports:
        ElementTree
"""

class Condition(object):
    """
    General class for a Condition
    """
    def __init__(self):
        self.flag = False
        """ Evaluated truth value of condition"""
        self.type=''
        """ type of condition """
        self.parent = None
        """the node linked to this node directly"""
        self.leaf = False
        """ True if as no children, False otherwise """
        self.place = 0
        """ index of which child link to change in its parent"""

    def test(self,p):
        """
        Return if its true or false
        
        Arguments:
            p contains experiment time, number of rewards, number of trials, 
                number of consecutively correct trials
        """
        return False
    
    def toString(self):
        """
        general function, to be redefined later by subclasses
        """
        return ""
    
    def toXml(self):
        """
        general function, to be redefined later by subclasses
        """
        return ""
    
    def morph(self,state):
        """
        make this node's parent's child flag link to this object
        """
        state.parent = self.parent
        state.place = self.place
        if self.place==1:
            self.parent.c1 = state
        elif self.place==2:
            self.parent.c2 = state
        else:
            pass

class Ender(Condition):
    """
    Superclass for End conditions
    """
    def __init__(self):
        Condition.__init__(self)
        self.leaf = True

class Floater(Ender):
    """A Floater node where the limit is a float"""
    
    def __init__(self,limit=0.0):
        Ender.__init__(self)
        self.limit = limit


class Inter(Ender):
    """
    An Inter node where the limit is an int
    """
    def __init__(self,limit=0):
        Ender.__init__(self)
        self.limit = limit

class Klaus(Condition):
    """
    Superclass for Not, And, Or, Xor type condition connectors
    """
    def __init__(self):
        Condition.__init__(self)
        self.leaf = False
   
class Unik(Klaus):
    """
    Takes one condition properly (has one child)
    """
    def __init__(self,c1):
        Klaus.__init__(self)
        self.c1 = c1
    
    def setNull(self):
        """
        Set child to be NullCon
        """
        if self.c1==None:
            self.c1 = NullCon()
        self.c1.place = 1
        self.c1.parent = self

class Bik(Klaus):
    """
    Takes two condition properties (has two children)
    """
    def __init__(self,c1,c2):
        Klaus.__init__(self)
        self.c1 = c1
        self.c2 = c2
    
    def setNull(self):
        """
        set children to be NullCon
        """
        if self.c1==None:
            self.c1 = NullCon()
        if self.c2==None:
            self.c2 = NullCon()
        self.c2.place = 2
        self.c2.parent = self
        self.c1.place = 1
        self.c1.parent = self

class NullCon(Ender):
    """ Null Condition is a place holder condition.
    It always return True upon calling its test method
    """
    def __init__(self):
        Ender.__init__(self)
        self.type="Null"
        
    def test(self,p):
        """ Returns True"""
        return True
    
    def toString(self):
        return 'Null'
    
    def toXml(self):
        """ Returns <null> """
        return elle.Element('null')

class TimeLimit(Floater):
    """
    stop if experiment time exceeds limit
    """
    def __init__(self,limit=0.0):
        Floater.__init__(self,limit)
        self.type='Time Limit'
    
    def test(self,p):
        """ Returns True if experiment time exceeds limit """
        if(p['time']>self.limit):
            self.flag = True
            return True
        else:
            return False
    
    def toString(self):
        return "TimeLimit=%f"%(self.limit)
    
    def toXml(self):
        """ Returns <time limit='(float)'> """
        lim = elle.Element('time')
        lim.set('limit',str(self.limit))
        return lim
   
class TrialsLimit(Inter):
    """
    stops after performing a certain number of trials  
    """
    def __init__(self,limit=0):
        Inter.__init__(self,limit)
        self.type='Max Trials'
    
    def test(self,p):
        """ Returns True if we exceeds trials limit """
        if(p['trials']>self.limit):
            self.flag = True
            return True
        else:
            return False
    
    def toString(self):
        return "MaxTrials=%d"%(self.limit)
    
    def toXml(self):
        """ Returns <trials limit='(int)'> """
        lim = elle.Element('trials')
        lim.set('limit',str(self.limit))
        return lim

class RewardsLimit(Inter):
    """stops after the number of rewards given exeeds the limit"""
    def __init__(self,limit=0):
        Inter.__init__(self,limit)
        self.type='Max Rewards'
    
    def test(self,p):
        """ Returns True if number of rewards given reaches or exceeds limit"""
        if(p['rewards']>=self.limit):
            self.flag = True
            return True
        else:
            return False
    
    def toString(self):
        return "MaxRewards=%d"%(self.limit)
    
    def toXml(self):
        """ Returns <rewards limit='(int)'> """
        lim = elle.Element('rewards')
        lim.set('limit',str(self.limit))
        return lim


class ConRwLimit(Inter):
    """
    stops after the number of consecutively correct trials is performed
    """
    def __init__(self,limit=0):
        Inter.__init__(self,limit)
        self.type='Max Consecutive Rewards'
    
    def test(self,p):
        """ Returns True if number of consecutive rewards exceeds or reaches limit"""
        if(p['cc']>=self.limit):
            self.flag == True
            return True
        else:
            return False
        
    def toString(self):
        return "ConsecRewards=%d"%(self.limit)

    def toXml(self):
        """ Returns <cc limit='(int)'> """
        lim = elle.Element('cc')
        lim.set('limit',str(self.limit))
        return lim


class BiasRandom(Floater):
    """
    Decided on whether or not we return true
    by some random biased. if limit=0.5 then fair toss
    """
    def __init__(self,limit=0.5):
        Floater.__init__(self,limit)
        self.type='Random Switch'
        
    def test(self,p):
        """ Returns True if random number is less than limit,
        otherwise returns False
        """
        r = random.random()
        if r<self.limit:
            self.flag = True
        else:
            self.flag = False
        return self.flag

    def toString(self):
        return "BiasRandom=%f"%(self.limit)
    
    def toXml(self):
        """ Returns <random limit='(float)'>
        """
        ran = elle.Element('random')
        ran.set('limit',str(self.limit))
        return ran

class Noty(Unik):
    """ Not condition reverse the results of the test on child condition
    """
    def __init__(self,c1=None):
        Unik.__init__(self,c1)
        self.type="Not"
        self.c1 = c1
    
    def test(self,p):
        """ Return false if evaluative c1 is true, and vice versa
        """
        if self.c1:
            self.flag = not(self.c1.test(p))
        return self.flag
    
    def toString(self):
        return "NOT( %s )"%(self.c1.toString())
    
    def toXml(self):
        """ Returns <not> and runs toXml() on c1 """
        noty = elle.Element('not')
        noty.append(self.c1.toXml())
        return
  
class Ory(Bik):
    """ Is True if either one of its children returns True"""
    def __init__(self,c1=None,c2=None):
        Bik.__init__(self,c1,c2)
        self.type="Or"

    def test(self,p):
        """ Return true if c1 or c2 is true, False if they are both false
        """
        if self.c1 or self.c2:
            self.flag = (self.c1.test(p) or self.c2.test(p))
        return self.flag

    def toString(self):
        return "( %s OR %s )"%(self.c1.toString(),self.c2.toString())

    def toXml(self):
        """ Returns <or> and runs toXml() on its children """
        dou = elle.Element('or')
        dou.extend([self.c1.toXml(),self.c2.toXml()])
        return dou

class Andy(Bik):
    """ Is True only if both of its children evaluate as true """
    def __init__(self,c1=None,c2=None):
        Bik.__init__(self,c1,c2)
        self.type="And"
    
    def test(self,p):
        """ Return true only if both c1 and c2 are true, false otherwise
        """
        if self.c1 and self.c2:
            self.flag = (self.c1.test(p) and self.c2.test(p))
        return self.flag

    def toString(self):
        return "( %s AND %s )"%(self.c1.toString(),self.c2.toString())

    def toXml(self):
        """ Returns <and> and runs toXml() on its children """
        dou = elle.Element('and')
        dou.extend([self.c1.toXml(),self.c2.toXml()])
        return dou

class Xory(Bik):
    """ Is True if only one of its children is True"""
    def __init__(self,c1=None,c2=None):
        Bik.__init__(self,c1,c2)
        self.type="Xor"
    
    def test(self,p):
        """ Return true if either c1 is true and c2 is false, or c1 is false and c2 is true
        """
        if self.c1 and self.c2:
            self.flag = (self.c1.test(p) != self.c2.test(p))
        return self.flag

    def toString(self):
        return "( %s XOR %s )"%(self.c1.toString(),self.c2.toString())

    def toXml(self):
        " Returns <xor> and runs toXml() on its children """
        dou = elle.Element('xor')
        dou.extend([self.c1.toXml(),self.c2.toXml()])
        return dou

def parseXml(node):
    """Builds Conditional tree from XML tree
    """
    nodeName = node.tag
    obj = None
    if nodeName=='null':
        obj = NullCon()
    elif nodeName=='time':
        lim = float(node.get('limit'))
        obj = TimeLimit(lim)
    elif nodeName=='trials':
        lim = int(node.get('limit'))
        obj = TrialsLimit(lim)
    elif nodeName=='rewards':
        lim = int(node.get('limit'))
        obj = RewardsLimit(lim)
    elif nodeName=='cc':
        lim = int(node.get('limit'))
        obj = ConRwLimit(lim)
    elif nodeName=='random':
        ran = float(node.get('limit'))
        obj = BiasRandom(ran)
    elif nodeName=='not':
        c1txt = list(node)[0]
        c1 = parseXml(c1txt)
        obj = Noty(c1)
    elif nodeName in ['or','and','xor']:
        clist = list(node)
        c1 = parseXml(clist[0])
        c2 = parseXml(clist[1])
        if nodeName=='or':
            obj = Ory(c1,c2)
        elif nodeName=='and':
            obj = Andy(c1,c2)
        else:
            obj = Xory(c1,c2)
        obj.setNull()
    else:
        obj = NullCon()
    return obj