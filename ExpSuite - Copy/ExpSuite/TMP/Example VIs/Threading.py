import time

import wx
from threading import Thread
from wx.lib.pubsub import Publisher

class WorkerThread(Thread):
    def __init__(self):
        Thread.__init__(self)

        #A flag that can be set 
        #to tell the thread to end
        self.stop_flag = False

        #This calls the run() to start the new thread
        self.start()


    def run(self):
        """ Over-rides the super-classes run()"""
        #Put everything in here that 
        #you want to run in your new thread

        #e.g...
        for x in range(20):
            if self.stop_flag:
                break
            time.sleep(1)
            #Broadcast a message to who ever's listening
            Publisher.sendMessage("your_topic_name", x)
        Publisher.sendMessage("your_topic_name", "finished")


    def stop(self):
        """
        Call this method to tell the thread to stop
        """
        self.stop_flag = True




class GUI(wx.Frame):
    def __init__(self, parent, id=-1,title=""):
        wx.Frame.__init__(self, parent, id, title, size=(140,180))
        self.SetMinSize((140,180)) 
        panel = wx.Panel(id=wx.ID_ANY, name=u'mainPanel', parent=self)

        #Subscribe to messages from the workerThread
        Publisher().subscribe(self.your_message_handler, "your_topic_name")

        #A button to start the workerThread
        self.startButton = wx.Button(panel, wx.ID_ANY, 'Start thread')
        self.Bind(wx.EVT_BUTTON,  self.onStart, self.startButton)

        #A button to stop the workerThread
        self.stopButton = wx.Button(panel, wx.ID_ANY, 'Stop thread')
        self.Bind(wx.EVT_BUTTON,  self.onStop, self.stopButton)

        #A text control to display messages from the worker thread
        self.threadMessage = wx.TextCtrl(panel, wx.ID_ANY, '', size=(75, 20))

        #Do the layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.startButton, 0, wx.ALL, 10)
        sizer.Add(self.stopButton, 0, wx.ALL, 10)
        sizer.Add(self.threadMessage, 0, wx.ALL, 10)
        panel.SetSizerAndFit(sizer)


    def onStart(self, event):
        #Start the worker thread
        self.worker = WorkerThread()

        #Disable any widgets which could affect your thread
        self.startButton.Disable()

    def onStop(self, message):
        self.worker.stop()

    def your_message_handler(self, message):
        message_data = message.data
        if message_data == 'finished':
            self.startButton.Enable()
            self.threadMessage.SetLabel(str(message_data))
        else:
            self.threadMessage.SetLabel(str(message_data))

if __name__ == "__main__":

    app = wx.PySimpleApp()
    frame = GUI(None, wx.ID_ANY, 'Threading Example')
    frame.Show()
    app.MainLoop()