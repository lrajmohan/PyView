from pulsar import *
'''
X = Experiment()
X.trialDuration = 10.0
w1 = Intervals.WaitInt(2.0,"Wait 1")
t1 = Intervals.ToneInt(1.0,"Tone 1")
t1.freq = 2000
t1.tastes.append(0)
u1 = Intervals.RewardInt(3.0,"Reward Time")
w2 = Intervals.WaitInt(2.0,"Wait 2")
t2 = Intervals.ToneInt(1.0, "Tone 2")
t2.freq = 5000
t2.tastes.append(1)
u2 = Intervals.NogoInt(3.0,"No Go Time")

X.addInterval(w1)
X.addInterval(t1)
X.addInterval(u1)
X.addInterval(w2)
X.addInterval(t2)
X.addInterval(u2)

rs = Actions.Jump("Restart")

j1 = Actions.Jump("Jumper")
del j1.jumper[:]
j1.jumper.extend([(3,1.0)])

v1 = Actions.Taste("Taste 1")
v2 = Actions.Taste("Taste 2")

X.actionList.append(rs)
X.actionList.append(j1)
X.actionList.append(v1)
X.actionList.append(v2)

u1.actions['Lever'] = v1
u2.actions['Lever'] = j1
u2.actions['End'] = v2
v1.triggerFor.append(j1)
v2.triggerFor.append(rs) 

saveExperiment('test.xml',X)
'''

X = loadExperiment('test.xml')

X.printExpData()
