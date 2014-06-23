from libnidaqmx import DigitalOutputTask
import time
import framework
from Tkinter import *

taskO = DigitalOutputTask()
taskO.create_channel('Dev1/Port11/Line0:7')
fx = 1

def play():
    taskO.start()
    a = framework.int2bi8(fx)
    if len(a)==0:
        return
    else:
        taskO.write(a,layout='group_by_channel')

def stop():
    taskO.write([0,0,0,0,0,0,0,0],layout='group_by_channel')
    taskO.stop()

class App:
    def __init__(self,master):
        frame = Frame(master)
        frame.grid(padx=5, pady=2)

        play_btn = Button(frame, text="play", bg="green", command=play)
        stop_btn = Button(frame, text="stop", bg="red", command=stop)
        freq_txt = Label(frame, text="Frequency (Hz)")
        self.freq_val = Spinbox(frame, from_=1000, to=11160, increment=40,
                                command=self.updateVal, width=10)

        play_btn.grid(row=0, column=0)
        stop_btn.grid(row=0, column=1)
        freq_txt.grid(row=1, column=0)
        self.freq_val.grid(row=1, column=1)


    def updateVal(self):
        global fx
        sv = self.freq_val.get()
        try:
            iv = int(sv)
            if iv>999 and iv<11161:
                fx = framework.freq2int(iv)
        except ValueError:
            pass

root = Tk()
app = App(root)
root.mainloop()
