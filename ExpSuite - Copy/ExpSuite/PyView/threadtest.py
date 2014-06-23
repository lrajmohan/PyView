import threading
from threading import Thread

class MainProc(Thread):
    
    def __init__(self):
        Thread.__init__(self)
        self.start()
    
    def run(self):
        i = 0
        while (i<100):
            print "MAIN %d"%i
            if i%10==0:
                SubProc(i)
            i+=1

class SubProc(Thread):
    
    def __init__(self,j):
        Thread.__init__(self)
        self.j = j
        self.start()
    
    def run(self):
        while(self.j>0):
            print "SUB %d"%self.j
            self.j-=2

MainProc()