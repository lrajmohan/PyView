
from pulsar import *
'''
g = loadDuoSequence('saves/duo1.xml')
g.printDuoSeq()

class A(object):
    def __init__(self,n=0):
        self.name = 'A'
        self.n = n

mapy = {'newA':A}
'''
namesMap = [Conditions.NullCon, Conditions.TimeLimit, Conditions.TrialsLimit,Conditions.RewardsLimit,
             Conditions.ConRwLimit, Conditions.BiasRandom, Conditions.Noty, Conditions.Ory,
              Conditions.Andy, Conditions.Xory]

for v in namesMap:
    a = v()
    print "'%s':Conditions.%s, "%(a.type,a.__class__.__name__)