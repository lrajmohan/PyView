from threading import Thread

def two():
    for i in range(0,100):
        if i%2==0:
            print i

class MainThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.start()
    
    def run(self):
        two()
        for i in range(0,100):
            if i%2==1:
                print i

MainThread()