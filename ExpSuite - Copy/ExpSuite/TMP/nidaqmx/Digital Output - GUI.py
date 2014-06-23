from libnidaqmx import System
from libnidaqmx import Device
from libnidaqmx import DigitalOutputTask

import wx
import numpy as np
import time
import string

system = System()
dev1 = system.devices[0]

time.clock(); # to call this function for the fist time

#print 'libnidaqmx version:', system.version
#print 'NI-DAQ devices:', system.devices
#print 'Product Type:', dev1.get_product_type()
#print 'Product Number:',dev1.get_product_number()
#print 'Product Serial:', dev1.get_serial_number()
#print 'Bus Type:', dev1.get_bus()

frameName = "NI-DAQ " + dev1.get_product_type();


class ExamplePanel(wx.Panel):
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.quote = wx.StaticText(self, label=frameName, pos=(20, 30))

        # A multiline TextCtrl - This is here to show how the events work in this program, don't pay too much attention to it
        self.logger = wx.TextCtrl(self, pos=(300,20), size=(200,300), style=wx.TE_MULTILINE | wx.TE_READONLY)

        # A button
        self.button =wx.Button(self, label="Deliver", pos=(100, 200))
        self.Bind(wx.EVT_BUTTON, self.OnClick,self.button)

        self.lblname0 = wx.StaticText(self, label=" Number of Pulses ", pos=(20,60))
        self.editname0 = wx.TextCtrl(self, value="5", pos=(160, 60), size=(50,-1))
        self.Bind(wx.EVT_TEXT, self.EvtText0, self.editname0)
        self.Bind(wx.EVT_CHAR, self.EvtChar0, self.editname0)
        self.numberPulses = "5"

        self.lblname1 = wx.StaticText(self, label="Pulse Interval (in sec): ", pos=(20,100))
        self.editname1 = wx.TextCtrl(self, value="1", pos=(160, 100), size=(50,-1))
        self.Bind(wx.EVT_TEXT, self.EvtText1, self.editname1)
        self.pulseInterval = "1"
        
        self.lblname2 = wx.StaticText(self, label="Pulse Duration (in m sec): ",pos=(20,140))
        self.editname2 = wx.TextCtrl(self, value="100", pos=(160, 140), size=(50,-1))
        self.Bind(wx.EVT_TEXT, self.EvtText2, self.editname2)
        self.pulseDuration = "100"
        
     
   
    def OnClick(self,event):
        #self.logger.AppendText(" Click on object with Id %d\n" %event.GetId())
        task = DigitalOutputTask()
        true = [1];
        false = [0];
        task.create_channel('Dev1/Port2/Line7');
        task.start();
                
        for i in range(string.atoi(self.numberPulses)):
            T1 = time.clock();
            T2 = time.clock();
            pI = string.atoi(self.pulseInterval);
            while (T2 - T1) < pI: 
                # waiting to deliver the pulse
                T2 = time.clock();
            task.write(true); # pulse delivered
        
            T1 = time.clock();
            T2 = time.clock();
            pD = string.atoi(self.pulseDuration) / 1000.0;
            while (T2 - T1) < pD :
                # keep delivering pulse
                T2 = time.clock();
            task.write(false); # pulse delivery stopped

        task.stop();
        task.clear();
        
    def EvtText0(self, event):
        self.logger.AppendText('No. of Pulses: %s\n' % event.GetString())
        self.numberPulses = event.GetString();

    def EvtText1(self, event):
        self.logger.AppendText('Pulse Interval: %s\n' % event.GetString())
        self.pulseInterval = event.GetString();

    def EvtText2(self, event):
        self.logger.AppendText('Pulse Duration: %s\n' % event.GetString())
        self.pulseDuration = event.GetString();
        
    def EvtChar0(self, event):
        self.logger.AppendText('EvtChar: %d\n' % event.GetKeyCode())
        event.Skip()
    



app = wx.App(False)  # Create a new app, don't redirect stdout/stderr to a window.
frame = wx.Frame(None,title = frameName, size=(400,400))
panel = ExamplePanel(frame)
frame.Show()


#ddata = np.zeros(nsamples, dtype=np.uint8)
#ddata[0:nsamples:5]=1



# have to connect channel port2/line7 P2.7



   


app.MainLoop()

#task.configure_timing_sample_clock(rate = 1, active_edge='rising', sample_mode = 'continuous', samples_per_channel = 100)

#task.configure_timing_sample_clock(source=r'ao/SampleClock',rate=1000,sample_mode='finite',samples_per_channel=1000)
#task.write(ddata, auto_start=False)
#task.start()

#task.stop()


